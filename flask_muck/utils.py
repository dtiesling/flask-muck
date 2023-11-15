from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Union

from flask import request
from sqlalchemy import Column, inspect

from flask_muck.exceptions import MuckImplementationError
from flask_muck.types import SqlaModelType

if TYPE_CHECKING:
    from flask_muck.views import MuckApiView


def get_url_rule(muck_view: type[MuckApiView], append_rule: Optional[str]):
    """Recursively build the url rule for a MuckApiView by looking at its parent if it exists."""
    rule = muck_view.api_name
    if append_rule:
        rule = f"{rule}/{append_rule}"
    if muck_view.parent:
        rule = f"<{muck_view.parent.primary_key_type.__name__}:{muck_view.parent.api_name}_id>/{rule}"
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
    return None


def get_query_filters_from_request_path(
    view: Union[type[MuckApiView], MuckApiView], query_filters: list
) -> list:
    """Recursively builds query kwargs from the request path based on nested MuckApiViews. If the view has no parent
    then nothing is done and original query_kwargs are returned.
    """
    if view.parent:
        child_model = view.Model
        parent_model = view.parent.Model
        fk_column = get_fk_column(parent_model, child_model)
        if fk_column is None:
            raise MuckImplementationError(
                f"The model associated with {view} does not have a foreign key to its parent model."
            )
        query_filters.append(
            fk_column == request.view_args[f"{view.parent.api_name}_id"]
        )
        return get_query_filters_from_request_path(view.parent, query_filters)
    return query_filters


def get_join_models_from_parent_views(
    view: Union[type[MuckApiView], MuckApiView], join_models: list[SqlaModelType]
) -> list[SqlaModelType]:
    """Recursively builds a list of models that need to be joined in queries based on the view's parents.."""
    if view.parent:
        join_models.append(view.parent.Model)
        return get_join_models_from_parent_views(view.parent, join_models)
    join_models.reverse()
    return join_models
