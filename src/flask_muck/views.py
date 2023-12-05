from __future__ import annotations

import json
from json import JSONDecodeError
from logging import getLogger
from typing import Optional, Union, Any

from flask import request, Blueprint
from flask.typing import ResponseReturnValue
from flask.views import MethodView
from marshmallow import Schema
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import (
    BinaryExpression,
    UnaryExpression,
    BooleanClauseList,
    or_,
)
from webargs import fields
from webargs.flaskparser import parser
from werkzeug.exceptions import MethodNotAllowed, BadRequest, Conflict

from flask_muck.callback import CallbackType
from flask_muck.callback import FlaskMuckCallback
from flask_muck.types import SqlaModelType, JsonDict, ResourceId, SqlaModel
from flask_muck.utils import (
    get_url_rule,
    get_query_filters_from_request_path,
    get_pk_column,
    get_pk_type,
)

logger = getLogger(__name__)

METHOD_OPERATION_MAP = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "patch",
    "DELETE": "delete",
}


class FlaskMuckApiView(MethodView):
    session: scoped_session
    api_name: str
    Model: SqlaModelType
    parent: Optional[type[FlaskMuckApiView]] = None

    ResponseSchema: type[Schema]
    CreateSchema: Optional[type[Schema]] = None
    UpdateSchema: Optional[type[Schema]] = None
    PatchSchema: Optional[type[Schema]] = None
    DeleteSchema: Optional[type[Schema]] = None
    DetailSchema: Optional[type[Schema]] = None

    pre_create_callbacks: list[type[FlaskMuckCallback]] = []
    pre_update_callbacks: list[type[FlaskMuckCallback]] = []
    pre_patch_callbacks: list[type[FlaskMuckCallback]] = []
    pre_delete_callbacks: list[type[FlaskMuckCallback]] = []

    post_create_callbacks: list[type[FlaskMuckCallback]] = []
    post_update_callbacks: list[type[FlaskMuckCallback]] = []
    post_patch_callbacks: list[type[FlaskMuckCallback]] = []
    post_delete_callbacks: list[type[FlaskMuckCallback]] = []

    searchable_columns: list[InstrumentedAttribute] = []
    default_pagination_limit: int = 20
    one_to_one_api: bool = False
    allowed_methods: set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    operator_separator: str = "__"

    @property
    def query(self) -> Query:
        return self.session.query(self.Model)

    def dispatch_request(self, **kwargs: Any) -> ResponseReturnValue:
        if request.method.lower() not in [m.lower() for m in self.allowed_methods]:
            raise MethodNotAllowed
        return super().dispatch_request(**kwargs)

    def _execute_callbacks(
        self,
        resource: SqlaModel,
        kwargs: JsonDict,
        callback_type: CallbackType,
    ) -> None:
        attr = f"{callback_type.value}_{METHOD_OPERATION_MAP[request.method]}_callbacks"
        for callback in getattr(self, attr):
            callback(resource, kwargs).execute()

    def get_base_query_kwargs(self) -> JsonDict:
        """Returns a set of base query args. This can be overridden to add additional kwargs to the base query.
        Useful for multi-tenant apps that need to logically separate resources by client.
        """
        return {}

    def _get_base_query(self) -> Query:
        base_query: Query = self.query
        base_query = base_query.filter(*get_query_filters_from_request_path(self, []))
        if query_kwargs := self.get_base_query_kwargs():
            base_query = base_query.filter_by(**query_kwargs)
        return base_query

    def _get_resource(cls, resource_id: Optional[ResourceId]) -> SqlaModel:
        query = cls._get_base_query()
        if cls.one_to_one_api:
            return query.one()
        return query.filter(get_pk_column(cls.Model) == resource_id).one()

    def _get_clean_filter_data(self, filters: str) -> JsonDict:
        try:
            return json.loads(filters)
        except JSONDecodeError:
            raise BadRequest(f"Filters [{filters}] is not valid json.")

    def _get_kwargs_from_request_payload(self) -> JsonDict:
        """Creates the correct schema based on request method and returns a sanitized dictionary of kwargs from the
        request json.
        """
        if self.PatchSchema:
            patch_schema = self.PatchSchema(partial=True)
        elif self.UpdateSchema:
            patch_schema = self.UpdateSchema(partial=True)
        else:
            None
        schema_method_map = {
            "POST": self.CreateSchema() if self.CreateSchema else None,
            "PUT": self.UpdateSchema() if self.UpdateSchema else None,
            "PATCH": patch_schema,
            "DELETE": self.DeleteSchema() if self.DeleteSchema else None,
        }
        schema = schema_method_map[request.method]
        if not schema:
            raise NotImplementedError
        kwargs = schema.load(request.json or {})
        kwargs.update(self.get_base_query_kwargs())
        return kwargs

    @parser.use_kwargs(
        {
            "limit": fields.Integer(missing=None),
            "offset": fields.Integer(missing=None),
            "filters": fields.String(required=False, missing=None),
            "sort": fields.String(required=False, missing=None),
            "search": fields.String(required=False, missing=None),
        },
        location="querystring",
    )
    def get(
        self,
        resource_id: Optional[ResourceId],
        limit: Optional[int],
        offset: Optional[int],
        filters: Optional[str],
        sort: Optional[str],
        search: Optional[str],
        **kwargs: Any,
    ) -> tuple[Union[JsonDict, list[JsonDict]], int]:
        if resource_id or self.one_to_one_api:
            resource = self._get_resource(resource_id)
            if hasattr(self, "DetailSchema") and self.DetailSchema:
                return self.DetailSchema().dump(resource)
            else:
                return self.ResponseSchema().dump(resource)
        else:
            query = self._get_base_query()
            query_filters: list = []
            join_models: set[SqlaModelType] = set()
            if filters:
                _filters = self._get_clean_filter_data(filters)
                query_filters, _join_models = self._get_query_filters(_filters)
                join_models.update(_join_models)

            # Get order by from request
            order_by = None
            if sort:
                order_by, _join_models = self._get_query_order_by(sort)
                join_models.update(_join_models)

            if search:
                search_filter, _join_models = self._get_query_search_filter(search)
                join_models.update(_join_models)
                if search_filter is not None:
                    query_filters.append(search_filter)

            # Apply joins, filters and order by to the query.
            for model in join_models:
                if model != self.Model:
                    query = query.outerjoin(model)
            if query_filters:
                query = query.filter(*query_filters)
            if order_by is not None:
                query = query.order_by(order_by)
            query = query.distinct()

            # If offset or limit were included in the query params return paginated response object else return a flat
            # list of all items.
            if offset or limit:
                query_limit = limit or self.default_pagination_limit
                query_offset = offset or 0
                resources = query.limit(query_limit).offset(query_offset).all()
                response_data = {
                    "limit": query_limit,
                    "offset": query_offset,
                    "total": query.count(),
                    "items": self.ResponseSchema(many=True).dump(resources),
                }
            else:
                resources = query.all()
                response_data = self.ResponseSchema(many=True).dump(resources)
            return response_data, 200

    def _create_resource(self, kwargs: JsonDict) -> SqlaModel:
        resource = self.Model(**kwargs)
        self.session.add(resource)
        self.session.flush()
        return resource

    def _update_resource(self, resource: SqlaModel, kwargs: JsonDict) -> SqlaModel:
        for attr, value in kwargs.items():
            setattr(resource, attr, value)
        return resource

    def post(self) -> tuple[JsonDict, int]:
        if not self.CreateSchema:
            raise NotImplementedError()
        kwargs = self.get_base_query_kwargs()
        data = self._get_kwargs_from_request_payload()
        kwargs.update(data)
        try:
            resource = self._create_resource(kwargs)
        except IntegrityError as e:
            self.session.rollback()
            raise Conflict(str(e))
        self._execute_callbacks(resource, kwargs, CallbackType.pre)
        self.session.commit()
        self._execute_callbacks(resource, kwargs, CallbackType.post)
        return self.ResponseSchema().dump(resource), 201

    def put(self, resource_id: ResourceId, **kwargs: Any) -> tuple[JsonDict, int]:
        if not self.UpdateSchema:
            raise NotImplementedError()
        resource = self._get_resource(resource_id)
        kwargs = self._get_kwargs_from_request_payload()
        resource = self._update_resource(resource, kwargs)
        self._execute_callbacks(resource, kwargs, CallbackType.pre)
        self.session.commit()
        self._execute_callbacks(resource, kwargs, CallbackType.post)
        return self.ResponseSchema().dump(resource), 200

    def patch(self, resource_id: ResourceId, **kwargs: Any) -> tuple[JsonDict, int]:
        if not self.PatchSchema:
            raise NotImplementedError()
        resource = self._get_resource(resource_id)
        kwargs = self._get_kwargs_from_request_payload()
        resource = self._update_resource(resource, kwargs)
        self._execute_callbacks(resource, kwargs, CallbackType.pre)
        self.session.commit()
        self._execute_callbacks(resource, kwargs, CallbackType.post)
        return self.ResponseSchema().dump(resource), 200

    def delete(self, resource_id: ResourceId, **kwargs: Any) -> tuple[str, int]:
        resource = self._get_resource(resource_id)
        kwargs = {}
        if self.DeleteSchema:
            kwargs = self._get_kwargs_from_request_payload()
        self.session.delete(resource)
        self._execute_callbacks(resource, kwargs, CallbackType.pre)
        self.session.commit()
        self._execute_callbacks(resource, kwargs, CallbackType.post)
        return "", 204

    def _get_query_filters(
        self, filters: JsonDict
    ) -> tuple[list[BinaryExpression], set[SqlaModelType]]:
        """Translates a dictionary of column names and values into a list of SQLA query filters.
        Also returns a list of models that should be joined to the base query.
        """
        query_filters: list[BinaryExpression] = []
        join_models: set[SqlaModelType] = set()
        for column_name, value in filters.items():
            # Get operator.
            operator = None
            if self.operator_separator in column_name:
                column_name, operator = column_name.split(self.operator_separator)

            # Handle nested filters.
            if "." in column_name:
                relationship_name, column_name = column_name.split(".")
                field = getattr(self.Model, relationship_name, None)
                if not field:
                    raise BadRequest(
                        f"{column_name} is not a valid filter field. The relationship does not exist."
                    )
                _Model = field.property.mapper.class_
                join_models.add(_Model)
            else:
                _Model = self.Model

            if not (column := getattr(_Model, column_name, None)):
                raise BadRequest(f"{column_name} is not a valid filter field.")

            if operator == "gt":
                _filter = column > value
            elif operator == "gte":
                _filter = column >= value
            elif operator == "lt":
                _filter = column < value
            elif operator == "lte":
                _filter = column <= value
            elif operator == "ne":
                _filter = column != value
            elif operator == "in":
                _filter = column.in_(value)
            elif operator == "not_in":
                _filter = column.not_in(value)
            else:
                _filter = column == value
            query_filters.append(_filter)
        return query_filters, join_models

    def _get_query_order_by(
        self, sort: str
    ) -> tuple[Optional[UnaryExpression], set[SqlaModelType]]:
        if self.operator_separator in sort:
            column_name, direction = sort.split(self.operator_separator)
        else:
            column_name, direction = sort, "asc"

        # Handle nested fields.
        join_models = set()
        if "." in column_name:
            relationship_name, column_name = column_name.split(".")
            field = getattr(self.Model, relationship_name, None)
            if not field:
                raise BadRequest(f"{column_name} is not a valid sort field.")
            _Model = field.property.mapper.class_
            join_models.add(_Model)
        else:
            _Model = self.Model

        if hasattr(_Model, column_name):
            column = getattr(_Model, column_name)
            if direction == "asc":
                order_by = column.asc()
            elif direction == "desc":
                order_by = column.desc()
            else:
                raise BadRequest(
                    f"Invalid sort direction: {direction}. Must asc or desc"
                )
        else:
            raise BadRequest(f"{column_name} is not a valid sort field.")
        return order_by, join_models

    def _get_query_search_filter(
        self, search_string: str
    ) -> tuple[Optional[BooleanClauseList], set[SqlaModelType]]:
        """Returns SQLA full text search filters for the search_term provided."""
        if not self.searchable_columns:
            raise BadRequest("Search is not supported on this endpoint.")
        searches = []
        join_models = set()
        for column in self.searchable_columns:
            join_models.add(column.parent.class_)
            searches.append(column.ilike(f"%{search_string}%"))
        if len(searches) == 1:
            return searches[0], join_models
        else:
            return or_(*searches), join_models

    @classmethod
    def add_rules_to_blueprint(cls, blueprint: Blueprint) -> None:
        """Adds CRUD endpoints to a blueprint."""
        url_rule = get_url_rule(cls, None)
        api_view = cls.as_view(f"{cls.api_name}_api")

        # In the special case that this API represents a ONE-TO-ONE relationship, use / for all methods.
        if cls.one_to_one_api:
            blueprint.add_url_rule(
                url_rule,
                defaults={"resource_id": None},
                view_func=api_view,
                methods={"GET", "PUT", "PATCH", "DELETE"},
            )

        else:
            # Create endpoint - POST on /
            blueprint.add_url_rule(url_rule, view_func=api_view, methods=["POST"])

            # List endpoint - GET on /
            blueprint.add_url_rule(
                url_rule,
                defaults={"resource_id": None},
                view_func=api_view,
                methods=["GET"],
            )

            # Detail, Update, Patch, Delete endpoints - GET, PUT, PATCH, DELETE on /<resource_id>
            blueprint.add_url_rule(
                f"{url_rule}/<{get_pk_type(cls.Model)}:resource_id>/",
                view_func=api_view,
                methods={"GET", "PUT", "PATCH", "DELETE"},
            )
