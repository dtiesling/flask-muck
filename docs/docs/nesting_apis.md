# Nesting Resource APIs

Nesting hierarchical resources in a REST API is a common practice. Flask-Muck provides support for generating nested APIs if the SqlAlchemy models are related by a basic foreign key relationship. Nested APIs automatically handle filtering child resources and supplying the parent ID as input during the Create operation.

Creating a nested relationship is as simple as setting the `parent` class variable of a `FlaskMuckApiView` to another `FlaskMuckApiView` whose `Model` has a valid foreign key relationship.

```python
from flask import Blueprint
from flask_muck import FlaskMuckApiView
from myapp import db
from myapp.models import Parent, Child
from myapp.schemas import ParentSchema, ChildSchema

class ParentApiView(FlaskMuckApiView):
    api_name = "parents"
    session = db.session
    Model = Parent
    ResponseSchema = ParentSchema
    CreateSchema = ParentSchema
    PatchSchema = ParentSchema
    UpdateSchema = ParentSchema
    
class ChildApiView(FlaskMuckApiView):
    api_name = "children"
    session = db.session
    parent = ParentApiView#(1)!
    Model = Child#(2)!
    ResponseSchema = ChildSchema
    CreateSchema = ChildSchema
    PatchSchema = ChildSchema
    UpdateSchema = ChildSchema

blueprint = Blueprint("api", __name__, url_prefix="/api/")
ParentApiView.add_rules_to_blueprint(blueprint)
ChildApiView.add_rules_to_blueprint(blueprint)
```

1. Setting the `parent` class variable to another `FlaskMuckApiView` is all that is needed to set up nesting.
2. The `Child` model must have a foreign key column that references the `Parent` model.

This setup produces the following nested API resources:

| URL Path                           | Method | Description                               |
|------------------------------------|--------|-------------------------------------------|
| /api/parents/                      | GET    | List all parents                          |
| /api/parents/                      | POST   | Create a parent                           |
| /api/parents/<ID\>/                | GET    | Fetch a parent                            |
| /api/parents/<ID\>/                | PUT    | Update a parent                           |
| /api/parents/<ID\>/                | PATCH  | Patch a parent                            |
| /api/parents/<ID\>/                | DELETE | Delete a parent                           |
| /api/parents/<ID\>/children/       | GET    | List all children of a parent             |
| /api/parents/<ID\>/children/       | POST   | Create a child foreign keyed to a parent. |
| /api/parents/<ID\>/children/<ID\>/ | GET    | Fetch a child                             |
| /api/parents/<ID\>/children/<ID\>/ | PUT    | Update a child                            |
| /api/parents/<ID\>/children/<ID\>/ | PATCH  | Patch a child                             |
| /api/parents/<ID\>/children/<ID\>/ | DELETE | Delete a child                            |

!!! Tip
    Nesting APIs works recursively, allowing for multiple levels of nesting.

!!! Warning
    Nested APIs may not function correctly if your models do not use standard integer or UUID primary keys.

## Usage Example

!!! note
    This example builds upon the [quickstart](quickstart.md) example. It will be more comprehensible if you have read through the [quickstart](quickstart.md).

Suppose you want to add a nested endpoint to the teacher detail endpoint from the quickstart, allowing you to manage all of a teacher's students.

Below are the necessary models, schemas, and views:

```python title="myapp/models.py"
from myapp import db

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    years_teaching = db.Column(db.Integer)
    
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    parent_id = db.Column(db.ForeignKey(Teacher.id))
    parent = db.relationship(Teacher)
```

```python title="myapp/schemas.py"
from marshmallow import Schema
from marshmallow import fields as mf


class TeacherSchema(Schema):
    id = mf.Integer(dump_only=True)
    name = mf.String(required=True)
    years_teaching = mf.Integer()

class StudentSchema(Schema):
    id = mf.Integer(dump_only=True)
    name = mf.String(required=True)
```

```python title="myapp/views.py"
from flask_muck import FlaskMuckApiView
from myapp import db
from myapp.auth.decorators import login_required
from myapp.models import Teacher, Student
from myapp.schemas import TeacherSchema, StudentSchema


class BaseApiView(FlaskMuckApiView):
    session = db.session
    decorators = [login_required]
    
    
class TeacherApiView(BaseApiView):
    api_name = "teachers" 
    Model = Teacher 
    ResponseSchema = TeacherSchema 
    CreateSchema = TeacherSchema 
    PatchSchema = TeacherSchema 
    UpdateSchema = TeacherSchema 
    searchable_columns = [Teacher.name] 

    
class StudentApiView(BaseApiView):
    api_name = "students" 
    Model = Student 
    parent = TeacherApiView
    ResponseSchema = StudentSchema 
    CreateSchema = StudentSchema 
    PatchSchema = StudentSchema 
    UpdateSchema = StudentSchema 
    searchable_columns = [Student.name]
```