from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from apispec import APISpec
from marshmallow import Schema
from marshmallow_jsonschema import JSONSchema  # type: ignore

from flask_muck.types import JsonDict
from flask_muck.utils import get_url_rule, get_pk_type, get_url_path_variable

if TYPE_CHECKING:
    from flask_muck import FlaskMuckApiView
    from sqlalchemy.orm import DeclarativeBase  # type: ignore


def _get_openapi_pk_type(model: type[DeclarativeBase]) -> str:
    """Returns the type to use for the primary key of the model in an OpenAPI specification."""
    type_map = {"int": "integer", "str": "string"}
    return type_map[get_pk_type(model)]


def _get_path_parameters(
    muck_view: type[FlaskMuckApiView], parameters: Optional[list] = None
) -> list[JsonDict]:
    """Returns a list of OpenAPI path parameters a FlaskMuckApiView will use at the instance level. Parameters are in
    order that they appear in the url path.
    """
    parameters = parameters or []
    resource_name = muck_view.Model.__name__
    id_string = get_url_path_variable(muck_view)
    parameter = {
        "name": id_string,
        "in": "path",
        "required": True,
        "description": f"ID of the {resource_name} resource",
        "schema": {"type": _get_openapi_pk_type(muck_view.Model)},
    }
    parameters.insert(0, parameter)
    if muck_view.parent:
        return _get_path_parameters(muck_view.parent, parameters)
    return parameters


def _convert_flask_path_to_openapi_path(url_path: str) -> str:
    """String manipulation to convert flask url path style to OpenAPI style."""
    return (
        url_path.replace("<", "{")
        .replace(">", "}")
        .replace("int:", "")
        .replace("str:", "")
    )


def update_spec_from_muck_view(
    api_spec: Optional[APISpec], url_prefix: str, muck_view: type[FlaskMuckApiView]
) -> None:
    """Updates the given APISpect with endpoints and components based on a FlaskMuckApiView."""
    if not api_spec:
        return None
    tag_name = muck_view.api_name
    api_spec.tag({"name": tag_name})

    resource_name = muck_view.Model.__name__

    if issubclass(muck_view.ResponseSchema, Schema):
        json_schema = JSONSchema().dump(muck_view.ResponseSchema())
        # There will only be a single entry in the json schema. Extract the resource name and component schema from it.
        resource_name, component_schema = list(json_schema["definitions"].items())[0]
    else:
        component_schema = muck_view.ResponseSchema.model_json_schema()
    api_spec.components.schema(resource_name, component_schema, lazy=False)

    path = get_url_rule(muck_view, None, url_prefix=url_prefix)
    path = _convert_flask_path_to_openapi_path(path)

    success_description = "Successful operation"
    instance_operations = {}
    if "POST" in muck_view.allowed_methods:
        instance_operations["post"] = {
            "tags": [tag_name],
            "summary": f"Create {resource_name} resource",
            "responses": {
                "201": {
                    "content": {"application/json": {"schema": resource_name}},
                    "description": success_description,
                }
            },
        }
    if "GET" in muck_view.allowed_methods:
        instance_operations["get"] = {
            "tags": [tag_name],
            "summary": f"Fetch {resource_name} resource",
            "responses": {
                "200": {
                    "content": {"application/json": {"schema": resource_name}},
                    "description": success_description,
                }
            },
        }
    if "PUT" in muck_view.allowed_methods:
        instance_operations["put"] = {
            "tags": [tag_name],
            "summary": f"Update {resource_name} resource",
            "responses": {
                "200": {
                    "content": {"application/json": {"schema": resource_name}},
                    "description": success_description,
                }
            },
        }
    if "PATCH" in muck_view.allowed_methods:
        instance_operations["patch"] = {
            "tags": [tag_name],
            "summary": f"Patch {resource_name} resource",
            "responses": {
                "200": {
                    "content": {"application/json": {"schema": resource_name}},
                    "description": success_description,
                }
            },
        }
    if "DELETE" in muck_view.allowed_methods:
        instance_operations["delete"] = {
            "tags": [tag_name],
            "summary": f"Delete {resource_name} resource",
            "responses": {"204": {"description": "Deleted successfully"}},
        }

    path_parameters = _get_path_parameters(muck_view)
    if muck_view.one_to_one_api:
        api_spec.path(
            path=path,
            parameters=path_parameters[:-1],
            summary=f"CRUD operations for a {resource_name} resource",
            description=f"CRUD operations for a {resource_name} resource",
            operations=instance_operations,
        )
    else:
        api_spec.path(
            path=f"{path}{{{get_url_path_variable(muck_view)}}}/",
            summary=f"CRUD operations for a {resource_name} resource",
            parameters=path_parameters,
            operations=instance_operations,
        )
        api_spec.path(
            path=path,
            parameters=path_parameters[:-1],
            operations={
                "get": {
                    "summary": f"List {resource_name} resources",
                    "description": f"Fetches {resource_name} resources with support for searching, filtering, "
                    f"sorting and pagination.",
                    "tags": [tag_name],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Number of resources to return. Using this parameter will return a paginated response.",
                            "required": False,
                            "schema": {"type": "integer"},
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "description": "Number of resources to skip. Using this parameter will return a paginated response.",
                            "required": False,
                            "schema": {"type": "integer"},
                        },
                        {
                            "name": "search",
                            "in": "query",
                            "description": "Search term to match resources against.",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "filter",
                            "in": "query",
                            "description": f"""
JSON-encoded object used to filter the resources. Filtering can be done 
against any field on the resource and supports filtering against relationships 
using dot notation. Operators are supported using the syntax:  `<column>{muck_view.operator_separator}<operator>` 
for more complex filtering. Available operators are below:.

| Operator | Description              |
|----------|--------------------------|
| None     | Equals                   |
| `ne`     | Not Equals               |
| `lt`     | Less Than                |
| `lte`    | Less Than or Equal To    |
| `gt`     | Greater Than             |
| `gte`    | Greater Than or Equal To |
| `in`     | In                       |
| `not_in` | Not In                   |
""",
                            "required": False,
                            "schema": {
                                "type": "string",
                            },
                        },
                        {
                            "name": "sort",
                            "in": "query",
                            "description": "Sorts resources by the provided field. Use dot notation to sort by a "
                            "related field and the `asc` or `desc` suffix to specify the sort order.",
                            "example": f"id{muck_view.operator_separator}asc",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": success_description,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "oneOf": [
                                            {
                                                "type": "array",
                                                "items": {
                                                    "$ref": f"#/components/schemas/{resource_name}",
                                                },
                                            },
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "total": {"type": "integer"},
                                                    "limit": {"type": "integer"},
                                                    "offset": {"type": "integer"},
                                                    "items": {
                                                        "type": "array",
                                                        "items": {
                                                            "$ref": f"#/components/schemas/{resource_name}",
                                                        },
                                                    },
                                                },
                                            },
                                        ]
                                    }
                                }
                            },
                        }
                    },
                }
            },
        )
