from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Union, Literal

from flask import request
from marshmallow import Schema
from pydantic import BaseModel, create_model
from sqlalchemy import Column, inspect

from flask_muck.exceptions import MuckImplementationError
from flask_muck.types import SqlaModelType, SqlaModel, JsonDict, SerializerType

if TYPE_CHECKING:
    from flask_muck.views import FlaskMuckApiView


def get_url_rule(muck_view: type[FlaskMuckApiView], append_rule: Optional[str]) -> str:
    """Recursively build the url rule for a MuckApiView by looking at its parent if it exists."""
    rule = muck_view.api_name
    if append_rule:
        rule = f"{rule}/{append_rule}"
    if muck_view.parent:
        rule = f"<{get_pk_type(muck_view.parent.Model)}:{muck_view.parent.api_name}_id>/{rule}"
        return get_url_rule(muck_view.parent, rule)
    if not rule.endswith("/"):
        rule = rule + "/"
    return rule


def get_fk_column(
    parent_model: SqlaModelType, child_model: SqlaModelType
) -> Optional[Column]:
    """Get the foreign key column for a child model."""
    for column in inspect(child_model).columns:
        if column.foreign_keys:
            for fk in column.foreign_keys:
                if fk.column.table == parent_model.__table__:
                    return column
    raise MuckImplementationError(
        f"The {child_model.__name__} model does not have a foreign key to the {parent_model.__name__} model. "
        f"Your MuckApiView parents are not configured correctly."
    )


def get_pk_column(model: SqlaModelType) -> Column:
    """Returns the Primary Key column for a model."""
    return model.__table__.primary_key.columns.values()[0]


def get_pk_type(model: SqlaModelType) -> Literal["str", "int"]:
    """Returns either "int" or "str" to describe the Primary Key type for a model. Used for building URL rules."""
    pk_column = get_pk_column(model)
    if issubclass(pk_column.type.python_type, (int, float)):
        return "int"
    else:
        return "str"


def get_query_filters_from_request_path(
    view: Union[type[FlaskMuckApiView], FlaskMuckApiView], query_filters: list
) -> list:
    """Recursively builds query kwargs from the request path based on nested MuckApiViews. If the view has no parent
    then nothing is done and original query_kwargs are returned.
    """
    if view.parent:
        child_model = view.Model
        parent_model = view.parent.Model
        fk_column = get_fk_column(parent_model, child_model)
        query_filters.append(
            fk_column == request.view_args[f"{view.parent.api_name}_id"]
        )
        return get_query_filters_from_request_path(view.parent, query_filters)
    return query_filters


def get_join_models_from_parent_views(
    view: Union[type[FlaskMuckApiView], FlaskMuckApiView],
    join_models: list[SqlaModelType],
) -> list[SqlaModelType]:
    """Recursively builds a list of models that need to be joined in queries based on the view's parents.."""
    if view.parent:
        join_models.append(view.parent.Model)
        return get_join_models_from_parent_views(view.parent, join_models)
    join_models.reverse()
    return join_models


def serialize_model_instance(
    instance: SqlaModel, serializer: SerializerType
) -> JsonDict:
    """Serializes a SQLAlchemy model instance using a Marshmallow schema or Pydantic model."""
    if issubclass(serializer, Schema):
        return serializer().dump(instance)
    elif issubclass(serializer, BaseModel):
        return serializer.model_validate(instance, from_attributes=True).model_dump()
    else:
        raise TypeError(
            f"Schemas must be Marshmallow Schemas or Pydantic BaseModels. {serializer} is a {type(serializer)}"
        )


def pydantic_model_to_optional(model: type[BaseModel]) -> type[BaseModel]:
    """Returns a new model where all fields are Optional. Used for PATCH JSON payload validation."""
    return create_model(  # type: ignore
        model.__class__.__name__,
        **{
            name: (Optional[type_], None)
            for name, type_ in model.__annotations__.items()
        },
    )


def validate_payload(
    payload: JsonDict, serializer: SerializerType, partial: bool = False
) -> JsonDict:
    """Validates JSON payload data and returns it if valid."""
    if issubclass(serializer, Schema):
        return serializer(partial=partial).load(payload)
    elif issubclass(serializer, BaseModel):
        if partial:
            serializer = pydantic_model_to_optional(serializer)
        serializer.model_config["from_attributes"] = True
        return serializer.model_validate(payload).model_dump()
    else:
        raise TypeError(
            f"Schemas must be Marshmallow Schemas or Pydantic BaseModels. {serializer} is a {type(serializer)}"
        )
