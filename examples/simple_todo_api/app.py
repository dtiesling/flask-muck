import marshmallow as ma
from flask import Flask, Blueprint
from flask_login import (
    LoginManager,
    login_required,
    UserMixin,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields as mf
from sqlalchemy.orm import DeclarativeBase

from flask_muck.views import MuckApiView

# Create a Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret"


# Init Flask-SQLAlchemy and set database to a local sqlite file.
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo_example.db"
db.init_app(app)


# Create SQLAlchemy database models.
class UserModel(db.Model, UserMixin):
    """Flask-Login User model to use for authentication."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


class TodoModel(db.Model):
    """Simple model to track ToDo items."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String, nullable=False)


# Create Marshmallow schemas for serialization.
class TodoSchema(ma.Schema):
    """ToDo model schema that can be used for CRUD operations."""

    id = mf.Integer(required=True, dump_only=True)
    text = mf.String(required=True)


# Add a Flask blueprint for the base of the REST API and register it with the app.
api_blueprint = Blueprint("v1_api", __name__, url_prefix="/api/v1/")


# Init Flask-Login for user authentication and add login/logout endpoints.
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return UserModel.query.get(user_id)


@api_blueprint.route("login", methods=["POST"])
def login_view():
    """Dummy login view that creates a User and authenticates them."""
    user = UserModel()
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return {}, 200


@api_blueprint.route("logout", methods=["POST"])
def logout_view():
    logout_user()
    return {}, 200


# Add Muck views to generate CRUD REST API.
class BaseApiView(MuckApiView):
    """Base view to inherit from. Helpful for setting class variables shared with all API views such as "sqlalchemy_db"
    and "decorators".
    """

    session = db.session
    decorators = [login_required]


class TodoApiView(BaseApiView):
    """ToDo API view that provides all RESTful CRUD operations."""

    Model = TodoModel
    ResponseSchema = TodoSchema
    CreateSchema = TodoSchema
    PatchSchema = TodoSchema
    UpdateSchema = TodoSchema
    searchable_columns = [TodoModel.text]


# Add all url rules to the blueprint.
TodoApiView.add_crud_to_blueprint(api_blueprint, url_prefix="todos")

# Register api blueprint with the app.
app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
