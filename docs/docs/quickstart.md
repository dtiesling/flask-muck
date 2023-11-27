# Quick Start

Flask-Muck provides standard REST APIs for resources in your Flask/SqlAlchemy application. This 
is accomplishing by creating subclasses of the FlaskMuckApiView and configuring them by setting a series of class
variables.

The quick start guide will walk you through creating your first basic API. The subsequent chapters covering using the 
APIs and configuring advanced features.


## Define a base view
Flask-Muck works by subsclassing the FlaskMuckApiView and setting class variables on the concrete view classes. In almost 
all projects there will be a basic set of class variables shared by all FlaskMuckApiView subclasses. The two most common 
settings to be shared across all views is the database session used for committing changes and a set of 
decorators that should be applied to all views.

In this example a base class is defined with with the app's database session and authentication decorator set.

Application using [SqlAlchemy in Flask](https://flask.palletsprojects.com/en/3.0.x/patterns/sqlalchemy/) session setup:
```python
from flask_muck import FlaskMuckApiView
from myapp.database import db_session 
from myapp.auth.decorators import login_required


class BaseApiView(FlaskMuckApiView):
    session = db_session
    decorators = [login_required]

```

Application using [Flask-SqlAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/#quick-start) exension:
```python
from flask_muck import FlaskMuckApiView
from myapp import db
from myapp.auth.decorators import login_required


class BaseApiView(FlaskMuckApiView):
    session = db.session
    decorators = [login_required]
```

NOTE: For the remainder of this guide we'll assume the usage of the [Flask-SqlAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/#quick-start) extension.

## Create SqlAlchemy Model
Flask-Muck requires the use of SqlAlchemy's [declarative system](). If you are not using the declarative system you will
need to review those [docs]() and re-evaluate whether Flask-Muck is the right choice. Explaining the full process of 
creating and registering a SqlAlchemy model in your Flask app is outside the scope of this guide. The example code below
shows the model class we will be creating an API for in the rest of the guide.

```python
from myapp import db

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    years_teaching = db.Column(db.Integer)
```

## Create input and response Marshmallow schemas
Flask-Muck requires configuring [Marshmallow](https://marshmallow.readthedocs.io/en/stable/) schemas that will be used 
to validate the payload data for the Create, Update, Patch and (optionally) Delete endpoints. Additionally a schema must 
be supplied that will serialize the endpoint's resource in responses. In this example simple schema is defined that 
can be re-used for all validation and serialization.

```python
from marshmallow import Schema
from marshmallow import fields as mf


class TeacherSchema(Schema):
    id = mf.Integer(dump_only=True)
    name = mf.String(required=True)
    years_teaching = mf.Integer()
```

## Create concrete FlaskMuckApiView
Inherit from the project's base api view class and define the required class variables.

```python
class TeacherApiView(BaseApiView):
    api_name = "teachers"  # Name used as the url endpoint in the REST API.
    Model = Teacher  # Model class that will be queried and updated by this API.
    ResponseSchema = TeacherSchema  # Marshmallow schema used to serialize and Teachers returned by the API.
    CreateSchema = TeacherSchema  # Marshmallow schema used to validate payload data sent to the Create endpoint.
    PatchSchema = TeacherSchema  # Marshmallow schema used to validate payload data sent to the Patch endpoint.
    UpdateSchema = TeacherSchema  # Marshmallow schema used to validate payload data sent to the Update endpoint.
    searchable_columns = [Teacher.name]  # List of model columns that can be searched when listing Teachers using the API.
```

## Add URL rules to a Flask Blueprint.
The final step is to add the correct URL rules to an existing [Flask Blueprint](https://flask.palletsprojects.com/en/3.0.x/blueprints/) 
object. A classmethod is included that handles adding all necessary rules to the given Blueprint.

```python
from flask import Blueprint

blueprint = Blueprint("api", __name__, url_prefix="/api/")
TeacherApiView.add_rules_to_blueprint(blueprint)
```

This produces the following views, a standard REST API!

| URL Path             | Method | Description                                                                                        |
|----------------------|--------|----------------------------------------------------------------------------------------------------|
| /api/teachers/       | GET    | List all teachers - querystring options available for sorting, filtering, searching and pagination |
| /api/teachers/       | POST   | Create a teacher                                                                                   |
| /api/teachers/\<ID>/ | GET    | Fetch a single teacher                                                                             |
| /api/teachers/\<ID>/ | PUT    | Update a single teacher                                                                            |
| /api/teachers/\<ID>/ | PATCH  | Patch a single teacher                                                                             |
| /api/teachers/\<ID>/ | DELETE | Delete a single teacher                                                                            |



