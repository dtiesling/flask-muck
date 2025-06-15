import marshmallow as ma
from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields as mf
from sqlalchemy.orm import DeclarativeBase

from flask_muck import FlaskMuckApiView

app = Flask(__name__)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo_example.db"
db.init_app(app)


class TodoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String, nullable=False)


class TodoSchema(ma.Schema):
    """ToDo model schema that can be used for CRUD operations."""

    id = mf.Integer(required=True, dump_only=True)
    text = mf.String(required=True)


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


# This is the existing api blueprint where all other routes are registered.
api_blueprint = Blueprint("v1_api", __name__, url_prefix="/")

# Use add_rules_to_blueprint classmethod on the FlaskMuckApiView to add all the CRUD route rules to the existing blueprint.
TodoApiView.add_rules_to_blueprint(api_blueprint)

app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)
