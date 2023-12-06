# Escape Hatches

Flask-Muck is designed to handle standard CRUD endpoints efficiently, but it's not intended to cover 100% of your API needs. Inevitably, you'll require more specific or targeted endpoints. Flask-Muck is flexible, allowing integration with other Flask method-based or class-based views.

This chapter covers various "escape hatches" that enable you to step outside Flask-Muck's logic, adding custom endpoints to your API or altering Flask-Muck's internal operations.

## Using `allowed_methods` Settings to Omit Endpoint(s)

The `allowed_methods` class variable lets you omit certain endpoints from being added by Flask-Muck. This is useful if you wish to implement a custom endpoint for a specific HTTP method. A common scenario is an API with a complex creation operation, while the rest of the CRUD operations are straightforward.

```python
blueprint = Blueprint("api", __name__, url_prefix="/api/")

class MyModelApiView(FlaskMuckApiView):
    api_name = "my-model"
    session = db.session
    Model = MyModel
    ResponseSchema = MyModelSchema
    CreateSchema = MyModelSchema
    PatchSchema = MyModelSchema
    UpdateSchema = MyModelSchema
    searchable_columns = [MyModel.name]
    allowed_methods = {"GET", "PATCH", "PUT", "DELETE"}#(1)!

MyModelApiView.add_rules_to_blueprint(blueprint)

@blueprint.route("/api/v1/my-model", methods=["POST"])
def create_my_model():
    ...#(2)!
```

1. The "POST" method is omitted from the `allowed_methods` set, preventing Flask-Muck from adding a create endpoint.
2. Implement your custom create logic here.

The `allowed_methods` setting can also be used to create read-only APIs (e.g., `allowed_methods = {"GET"}`).

## Overriding Create and Update Logic

FlaskMuckApiView has two simple methods for creating (POST) and updating (PUT/PATCH) resources:

```python
    def _create_resource(self, kwargs: JsonDict) -> SqlaModel:
        resource = self.Model(**kwargs)
        self.session.add(resource)
        self.session.flush()
        return resource

    def _update_resource(self, resource: SqlaModel, kwargs: JsonDict) -> SqlaModel:
        for attr, value in kwargs.items():
            setattr(resource, attr, value)
        return resource
```

These methods are designed as override points, allowing customization of resource creation and updating. For instance, if all your models have a `create` class method for resource creation, you could override `_create_resource` to use this method instead of the default constructor:

```python
    def _create_resource(self, kwargs: JsonDict) -> SqlaModel:
        resource = self.Model.create(**kwargs)
        return resource
```

## Customizing Keyword Arguments Passed to All Operations

You might want to customize the keyword arguments passed to all operations. FlaskMuckApiView's `get_base_query_kwargs` method can be overridden for this purpose:

```python
    def get_base_query_kwargs(self) -> JsonDict:
        return {}
```

For example, if you have a `deleted` column for soft-deleting resources, you could override `get_base_query_kwargs` to filter out deleted resources and ensure new or updated resources aren't marked as deleted:

```python
    def get_base_query_kwargs(self) -> JsonDict:
        return {"deleted": False}
```

A more detailed example using this method can be found in the [Supporting Logical Data Separation (Multi-tenancy)](logical_separation.md) chapter.