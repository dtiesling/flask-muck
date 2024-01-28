# Quick Start

Flask-Muck provides standard REST APIs for resources in your Flask/SqlAlchemy application. This 
is accomplishing by creating subclasses of the FlaskMuckApiView and configuring them by setting a series of class
variables.

The quick start guide will walk you through creating your first basic API. The subsequent chapters cover using the APIs and configuring advanced features.


## Define a base view
Flask-Muck works by subclassing the FlaskMuckApiView and setting class variables on the concrete view classes. In almost 
all projects there will be a basic set of class variables shared by all FlaskMuckApiView subclasses. The two most common 
settings to be shared across all views is the database session used for committing changes and a set of 
decorators that should be applied to all views.

In this example a base class is defined with the app's database session and authentication decorator set.

Application using [SqlAlchemy in Flask](https://flask.palletsprojects.com/en/3.0.x/patterns/sqlalchemy/) session setup:
```python
from flask_muck import FlaskMuckApiView
from myapp.database import db_session 
from myapp.auth.decorators import login_required


class BaseApiView(FlaskMuckApiView):
    session = db_session
    decorators = [login_required]

```

Application using [Flask-SqlAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/#quick-start) extension:
```python
from flask_muck import FlaskMuckApiView
from myapp import db
from myapp.auth.decorators import login_required


class BaseApiView(FlaskMuckApiView):
    session = db.session
    decorators = [login_required]
```

!!! note
    For the remainder of this guide we'll assume usage of the [Flask-SqlAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/#quick-start) extension.

## Create SQLAlchemy Model
Flask-Muck requires the use of SQLAlchemy's [declarative system](https://docs.sqlalchemy.org/en/20/orm/quickstart.html). If you are not using the declarative system, you will need to review those [docs](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) and re-evaluate whether Flask-Muck is the right choice for your project. Explaining the full process of creating and registering a SQLAlchemy model in your Flask app is outside the scope of this guide. The example code below shows the model class we will be creating an API for in the rest of the guide.

```python
from myapp import db

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    years_teaching = db.Column(db.Integer)
```

## Create Request and Response Schemas
Flask-Muck requires configuring Marshmallow and/or Pydantic classes that will be used to validate the payload data for 
the Create, Update, Patch, and (optionally) Delete endpoints. Additionally, a schema must be supplied that will 
serialize the endpoint's resource in responses. In this example, a simple schema is defined that can be re-used for 
all validation and serialization. In this example you'll be defining [Marshmallow](https://marshmallow.readthedocs.io/en/stable/)
schemas. 

!!! tip
    In v0.2.0 and higher, Pydantic models can also be used as schemas. You can see an example app using Pydantic models
    [here](https://github.com/dtiesling/flask-muck/tree/main/examples/02_pydantic)

```python
from marshmallow import Schema, fields as mf

class TeacherSchema(Schema):
    id = mf.Integer(dump_only=True)
    name = mf.String(required=True)
    years_teaching = mf.Integer()
```

## Create Concrete FlaskMuckApiView
Inherit from the project's base API view class and define the required class variables.

```python
class TeacherApiView(BaseApiView):
    api_name = "teachers" #(1)!
    Model = Teacher #(2)!
    ResponseSchema = TeacherSchema #(3)!
    CreateSchema = TeacherSchema #(4)!
    PatchSchema = TeacherSchema #(5)!
    UpdateSchema = TeacherSchema #(6)!
    searchable_columns = [Teacher.name] #(7)!
```

1. Name used as the URL endpoint in the REST API.
2. Model class that will be queried and updated by this API.
3. Marshmallow schema used to serialize Teachers returned by the API.
4. Marshmallow schema used to validate payload data sent to the Create endpoint.
5. Marshmallow schema used to validate payload data sent to the Patch endpoint.
6. Marshmallow schema used to validate payload data sent to the Update endpoint.
7. List of model columns that can be searched when listing Teachers using the API.

## Register the FlaskMuckApiViews
There are two options for registering the CRUD views. FlaskMuck can be initialized as a Flask extension or each 
FlaskMuckApiView can be added to an existing Flask Blueprint. 

### Initialize FlaskMuck extension.
The FlaskMuck extension is the "batteries included" approach and handles registering all of your views to a single 
API url root. Optionally the extension generates an OpenAPI spec definition and host a Swagger UI page.

```python
from myapp import app

from flask_muck import FlaskMuck

app.config['MUCK_API_URL_PREFIX'] = "/api/"
app.config['MUCK_APIDOCS_ENABLED'] = True
app.config['MUCK_API_TITLE'] = "School App API"
muck = FlaskMuck(app)
muck.register_muck_views([TeacherApiView])
```

### OR

### Manually register FlaskMuckApiViews
Manually registering each FlaskMuckApiView is an escape hatch to allow greater flexibility to work with existing 
views in an app and other frameworks and extensions.

A class method is included that handles adding all necessary rules to the given Blueprint.

```python
from flask import Blueprint

from myapp import app

blueprint = Blueprint("api", __name__, url_prefix="/api/")
TeacherApiView.add_rules_to_blueprint(blueprint)
app.register_blueprint(blueprint)
```

## Success!

The following views are generated for a standard REST API:

| URL Path                    | Method | Description                                                                                                |
|-----------------------------|--------|------------------------------------------------------------------------------------------------------------|
| /api/teachers/              | GET    | List all teachers - querystring options available for sorting, filtering, searching, and pagination        |
| /api/teachers/              | POST   | Create a teacher                                                                                           |
| /api/teachers/<TEACHER_ID\> | GET    | Fetch a single teacher                                                                                     |
| /api/teachers/<TEACHER_ID\> | PUT    | Update a single teacher                                                                                    |
| /api/teachers/<TEACHER_ID\> | PATCH  | Patch a single teacher                                                                                     |
| /api/teachers/<TEACHER_ID\> | DELETE | Delete a single teacher                                                                                    |
| /apidocs/                   | GET    | Swagger UI browsable API documentation page (Only available if FlaskMuck extension used to register views) |


