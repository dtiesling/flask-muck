# Pre/Post Callbacks

As most projects evolve, simple CRUD actions often become insufficient. APIs may need to perform complex validations, possibly requiring checks against external services, or execute additional actions after CRUD operations like sending emails, starting asynchronous tasks, or adding audit information.

Flask-Muck provides an easy-to-use callback system that allows you to define functions and execute them before or after any CRUD operation.

These functions are defined by creating `FlaskMuckCallback` subclasses. A `FlaskMuckCallback` has a single method, `execute`, that must be overridden. This method takes no arguments and returns `None`. Override this function with any logic that needs to occur before or after a CRUD operation.

The `execute` method has access to two attributes: `self.resource` and `self.kwargs`.

| Attribute | Description                                                                                                                                                                                                                                                                                                      | 
|:----------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| resource  | The SqlAlchemy model instance affected by the operation.                                                                                                                                                                                                                                                        |
| kwargs    | A dictionary of keyword arguments used to execute the CRUD operation. This is a union of kwargs sent in the JSON payload and any returned by the `get_base_query_kwargs` method. You can read more about `get_base_query_kwargs` in the [Supporting Logical Data Separation (Multi-tenancy)](logical_separation.md) section. |

The `FlaskMuckCallback` class is then added to pre or post callback lists on a `FlaskMuckApiView`. There is a class variable for the pre and post callback list for each CRUD operation. The names of these class variables follow this naming convention: `<pre_or_post>_<operation>_callbacks`.

```python
import logging
from flask import request
from flask_muck import FlaskMuckCallback, FlaskMuckApiView

class LogCallback(FlaskMuckCallback):
    def execute(self) -> None:
        logging.info(f"{request.method=} {self.resource=} {self.kwargs=}")

class MyApiView(FlaskMuckApiView):
    ...
    post_create_callbacks = [LogCallback]
    post_patch_callbacks = [LogCallback]
    post_update_callbacks = [LogCallback]
    post_delete_callbacks = [LogCallback]
```

!!! tip
    You can add any number of callbacks to a callback list. The callbacks are executed serially and in order. Keep this in mind if the effects of some callbacks may influence others.
    

## Example Usage

!!! note
    This example expands on the one in the [quickstart](quickstart.md). If you haven't read through the [quickstart](quickstart.md), it will make more sense if you do.

This scenario represents an app that tracks teachers and students. The requirements for the app are:

- Teachers' credentials must be verified against an external service before they can be added.
- All modification actions need to be added to the audit log for compliance.
- When a student or teacher is added, they will be sent a welcome email.

```python title="myapp/models.py"
from myapp import db

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    years_teaching = db.Column(db.Integer)
    
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    parent_id = db.Column(db.ForeignKey(Teacher.id))
    parent = db.relationship(Teacher)
```

```python title="myapp/callbacks.py"
from flask import request
from flask_login import current_user
from flask_muck import FlaskMuckCallback

from myapp.utils import add_audit_log#(1)!
from myapp.utils import verify_teacher#(2)!
from myapp.utils import send_welcome_email#(3)!

class VerifyTeacherCredentialsCallback(FlaskMuckCallback):
    """Check external service to verify a teacher has the correct teaching credentials."""
    def execute(self) -> None:
        verify_teacher(self.resource.name)

class AuditLogCallback(FlaskMuckCallback):
    """Adds a record to the audit log for SOC2 compliance."""
    def execute(self) -> None:
        add_audit_log(
            user=current_user,
            operation=request.method,
            resource_type=type(self.resource),
            resource_id=self.resource.id,
            kwargs=self.kwargs,
        )

class SendWelcomeEmailCallback(FlaskMuckCallback):
    """Sends a welcome email to newly created students or teachers."""
    def execute(self) -> None:
        send_welcome_email(name=self.resource.name, email=self.resource.email)
```

1. `add_audit_log` is a function that adds a record to an audit log used for compliance purposes.
2. `verify_teacher` is a function that makes a request to an external service to verify a teacher's credentials. If the proper credentials are not present, an exception is raised.
3. `send_welcome_email` is a function that sends a welcome email to a student or teacher when they are added to the application.

```python title="myapp/schemas.py"
from marshmallow import Schema
from marshmallow import fields as mf

class TeacherSchema(Schema):
    id = mf.Integer(dump_only=True)
    name = mf.String(required=True)
    email = mf.String(required=True)
    years_teaching = mf.Integer()

class StudentSchema(Schema):
    id = mf.Integer(dump_only=True)
    email = mf.String(required=True)
    name = mf.String(required=True)
```

```python title="myapp/views.py"
from flask_muck import FlaskMuckApiView
from myapp import db
from myapp.auth.decorators import login_required
from myapp.models import Teacher, Student
from myapp.schemas import TeacherSchema, StudentSchema
from myapp.callbacks import VerifyTeacherCredentialsCallback, AuditLogCallback, SendWelcomeEmailCallback

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
    
    pre_create_callbacks = [VerifyTeacherCredentialsCallback]#(1)!
    post_create_callbacks = [AuditLogCallback, SendWelcomeEmailCallback]#(2)!
    post_patch_callbacks = [AuditLogCallback]
    post_update_callbacks = [AuditLogCallback]
    post_delete_callbacks = [AuditLogCallback]

class StudentApiView(BaseApiView):
    api_name = "students" 
    Model = Student 
    parent = TeacherApiView
    ResponseSchema = StudentSchema 
    CreateSchema = StudentSchema 
    PatchSchema = StudentSchema 
    UpdateSchema = StudentSchema

    post_create_callbacks = [AuditLogCallback, SendWelcomeEmailCallback]
    post_patch_callbacks = [AuditLogCallback]
    post_update_callbacks = [AuditLogCallback]
    post_delete_callbacks = [AuditLogCallback]
```

1. The `pre_create_callbacks` are used to validate the teacher before they are added.
2. Note that you can add as many callbacks as you like. They will be executed serially and in order