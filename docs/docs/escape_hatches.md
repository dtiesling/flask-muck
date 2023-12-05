# Escape Hatches

Flask-Muck is not intended to handle 100% of your API endpoints. It does one job and does it well, creating standard CRUD 
endpoints. Inevitably you will need to step out of Flask-Muck's logic for more specific or targeted endpoints. Flask-Muck
is designed to be mixed and matched with any other Flask method-based or class-based views.

This chapter covers the various "escape hatches" that allow you to step outside Flask-Muck's logic and add your own custom
endpoints to the API or change the internals of how Flask-Muck handles operations.

## Using `allowed_methods` settings to omit endpoint(s).

The `allowed_methods` class variable allows you to omit endpoints from being added to your API by Flask-Muck. This is useful
if you want to add your own custom endpoint for a specific HTTP method. A common example is an API whose create operation
 is very complex but the rest of the CRUD operations are simple. 

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

1. Notice the "POST" method is omitted from the `allowed_methods` set. This will prevent Flask-Muck from adding a create endpoint.
2. Do your one-off create logic here.

Additionally the `allowed_methods` setting can be used to create read-only APIs - `allowed_methods = {"GET"}`.

## Overriding create and update logic.
There are two simple FlaskMuckApiView methods that handle creating (POST) and updating (PUT/PATCH) resources.

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

These methods are designed to be override seams that allow you to customize how resources are created and updated. For example,
let's say all of your models have a `create` classmethod that should be used to create new resources. You could override
the `_create_resource` method to use the `create` classmethod instead of the default constructor.

```python
    def _create_resource(self, kwargs: JsonDict) -> SqlaModel:
        resource = self.Model.create(**kwargs)
        return resource
```

## Customizing keyword arguments passed to all operations.

In many cases you will want to customize the keyword arguments passed to all operations. FlaskMuckApiView provides a 
`get_base_query_kwargs` method that can be overridden to customize the keyword arguments passed to all operations.

```python
    def get_base_query_kwargs(self) -> JsonDict:
        return {}
```

Let's say you have a `deleted` column that is used to soft-delete resources. You could override `get_base_query_kwargs` to
always filter out deleted resources and make sure that any new or updated resources are not marked as deleted.

```python
    def get_base_query_kwargs(self) -> JsonDict:
        return {"deleted": False}
```

You can find a deeper example using this method in the [Supporting Logical Data Separation (Multi-tenancy)](logical_separation.md) chapter.