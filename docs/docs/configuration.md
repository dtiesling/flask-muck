# Configuration

Configuration in Flask-Muck is handled at the app-level and class-level.

## App-Level Configuration

When using the `FlaskMuck` extension the following settings can be configured using the standard Flask config API.

| Key                      | Default    | Description                                                                                      |
|--------------------------|------------|--------------------------------------------------------------------------------------------------| 
| MUCK_API_URL_PREFIX      | "/"        | URL prefix the CRUD views will be registered under.                                              |
| MUCK_APIDOCS_ENABLED     | True       | If True, Swagger UI browser API docs will be available.                                          |
| MUCK_APIDOCS_URL_PATH    | "/apidocs/ | URL path to register the browsable API docs.                                                     |
| MUCK_API_VERSION         | 1.0.0      | API version. Used in OpenAPI spec definition and Swagger UI.                                     |
| MUCK_API_TITLE           | "REST API" | Title of the API. Used in OpenAPI spec definition and Swagger UI.                                |
| MUCK_APIDOCS_INTERACTIVE | False      | If True, Swagger UI wil have interactive mode enable allowing users to make requests to the API. |

## FlaskMuckApiView Class Variables

Much of the configuration occurs through setting class variables on `FlaskMuckApiView` classes. As noted in
the [quickstart](quickstart.md), you will
likely have some class variable settings that are shared by most or all of your view classes. It's advisable to set up
base classes to handle sharing configuration between views.

| Class Variable                                        | Description                                                                                                                                                                                                                                                           |          Required          |
|:------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------:|
| session `scoped_session`                              | SqlAlchemy database session used to query and modify the resource.                                                                                                                                                                                                    | :octicons-check-circle-16: |
| api_name `str`                                        | Name of the API. Used as the url path appended to your Flask Blueprint.                                                                                                                                                                                               | :octicons-check-circle-16: |
| Model `SqlaModelType`                                 | SqlAlchemy Model used to make queries.                                                                                                                                                                                                                                | :octicons-check-circle-16: |
| ResponseSchema `SerializerType`                       | Marshmallow schema or Pydantic model used to serialize the resource returned by any of the views.                                                                                                                                                                     | :octicons-check-circle-16: |
| decorators `list[Callable]`                           | List of decorators to apply to all views in the API. This is inherited functionality built into Flask's [class-based views](https://flask.palletsprojects.com/en/2.3.x/views/#view-decorators).                                                                       |                            |
| parent `Optional[type[FlaskMuckApiView]]`             | If set, this API becomes a nested resource API. For more information on nested APIs see the [documentation](nesting_apis.md).                                                                                                                                         |                            |
| CreateSchema `Optional[SerializerType]]`              | Marshmallow schema or Pydantic model used to validate the POST request JSON payload sent to create a resource.                                                                                                                                                        |                            |
| UpdateSchema `Optional[SerializerType]]`              | Marshmallow schema or Pydantic model used to validate the PUT request JSON payload sent to update a resource.                                                                                                                                                         |                            |
| PatchSchema `Optional[SerializerType]]`               | Marshmallow schema or Pydantic model used to validate the PATCH request JSON payload sent to patch a resource.                                                                                                                                                        |                            |
| DeleteSchema `Optional[SerializerType]]`              | Marshmallow schema or Pydantic model used to validate the DELETE request JSON payload sent to create a resource. Optional.                                                                                                                                            |                            |
| DetailSchema `Optional[SerializerType]]`              | Optional Marshmallow schema or Pydantic model used to serialize the resource returned by the GET /<api_name\>/<ID\>/ endpoint. If this schema is not set the ResponseSchema is used.                                                                                  |                            |
| pre_create_callbacks `list[type[FlaskMuckCallback]]`  | List of callback classes to be called before a resource is created. Ideal for validation.                                                                                                                                                                             |                            |
| pre_update_callbacks `list[type[FlaskMuckCallback]]`  | List of callback classes to be called before a resource is updated. Ideal for validation.                                                                                                                                                                             |                            |
| pre_patch_callbacks `list[type[FlaskMuckCallback]]`   | List of callback classes to be called before a resource is patched. Ideal for validation.                                                                                                                                                                             |                            |
| pre_delete_callbacks `list[type[FlaskMuckCallback]]`  | List of callback classes to be called before a resource is deleted. Ideal for validation.                                                                                                                                                                             |                            |
| post_create_callbacks `list[type[FlaskMuckCallback]]` | List of callback classes to be called after a resource is created. Useful for activities such as notifications. Called post commit.                                                                                                                                   |                            |
| post_update_callbacks `list[type[FlaskMuckCallback]]` | List of callback classes to be called after a resource is updated. Useful for activities such as notifications. Called post commit.                                                                                                                                   |                            |
| post_patch_callbacks `list[type[FlaskMuckCallback]]`  | List of callback classes to be called after a resource is patched. Useful for activities such as notifications. Called post commit.                                                                                                                                   |                            |
| post_delete_callbacks `list[type[FlaskMuckCallback]]` | List of callback classes to be called after a resource is deleted. Useful for activities such as notifications. Called post commit.                                                                                                                                   |                            |
| searchable_columns `list[InstrumentedAttribute]`      | List of Model columns that will be queried using an "ILIKE" statement when the `search=` query param is used on the GET /resource/ endpoint.                                                                                                                          |                            |
| default_pagination_limit `int`                        | Default pagination limit when retrieving paginated results on the GET /<api_name\>/ endpoint. Default is 20.                                                                                                                                                          |                            |
| one_to_one_api `bool`                                 | If True, this API is treated as a one-to-one relationship and the GET /<api_name\>/ endpoint will return a single resource. Generally used in combination with the `parent` setting.                                                                                  |                            |
| allowed_methods `set[str]`                            | Set of allowed HTTP methods for this API. Default is `{"GET", "POST", "PUT", "PATCH", "DELETE"}`. This setting is used to control which actions are available for this resource. Not including a method affects which routes will be registered to a Flask Blueprint. |                            |
| operator_separator `str`                              | Separator used when assigning operators to search or filter query parameters in the GET /<api_name\>/ endpoint. Default is `"__"`.                                                                                                                                    |                            |

### Base Class Example

Suppose you have an API with the following requirements for all views:

- Authentication decorator.
- Permission checking decorator.
- No allowance for patches.
- Uses "|" as the operator separator for filters.
- Uses the standard database session.

The best way to handle this is to create a base API view that all other API views inherit from.

```python title="Base Class"
class BaseApiView(FlaskMuckApiView):
    session = db.session
    decorators = [login_required, permission_required]
    allowed_methods = {"GET", "POST", "PUT", "DELETE"}
    operator_separator = "|"
```

```python title="Concrete Class"
class TurtleApiView(BaseApiView):  # (1)!
    api_name = 'turtles'
    Model = Turtle
    ...  # (2)!
```

1. The concrete view inherits from BaseApiView and all of its configurations.
2. The remainder of the class variables are configured as normal.
