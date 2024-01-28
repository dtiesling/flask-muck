import marshmallow as ma
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields as mf
from sqlalchemy.orm import DeclarativeBase

from flask_muck import FlaskMuck
from flask_muck import FlaskMuckApiView

# Create a Flask app
app = Flask(__name__)
muck = FlaskMuck()
muck.init_app(app)


# Init Flask-SQLAlchemy and set database to a local sqlite file.
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo_example.db"
db.init_app(app)


# Create SQLAlchemy database models.
class TodoModel(db.Model):
    """Simple model to track ToDo items."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String, nullable=False)


# Create Marshmallow schemas for serialization.
class TodoSchema(ma.Schema):
    """ToDo model schema that can be used for CRUD operations."""

    id = mf.Integer(required=True, dump_only=True)
    text = mf.String(required=True)


# Add Muck views to generate CRUD REST API.
class BaseApiView(FlaskMuckApiView):
    """Base view to inherit from. Helpful for setting class variables shared with all API views such as "session"
    and "decorators".
    """

    session = db.session


class TodoApiView(BaseApiView):
    """ToDo API view that provides all RESTful CRUD operations."""

    api_name = "todos"
    Model = TodoModel
    ResponseSchema = TodoSchema
    CreateSchema = TodoSchema
    PatchSchema = TodoSchema
    UpdateSchema = TodoSchema
    searchable_columns = [TodoModel.text]


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        muck.register_muck_views([TodoApiView])
    app.run(debug=True)
