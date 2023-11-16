import marshmallow as ma
from flask import Flask, Blueprint
from flask_login import (
    LoginManager,
    login_required,
    UserMixin,
    login_user,
    logout_user,
    FlaskLoginClient,
)
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields as mf
from sqlalchemy.orm import DeclarativeBase, Mapped

from flask_muck.views import MuckApiView


login_manager = LoginManager()


# Init Flask-SQLAlchemy and set database to a local sqlite file.
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


# Create SQLAlchemy database models.
class UserModel(db.Model, UserMixin):
    """Flask-Login User model to use for authentication."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


class GuardianModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    children: Mapped[list["ChildModel"]] = db.relationship()


class ChildModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey(GuardianModel.id))
    guardian = db.relationship(GuardianModel, back_populates="children")
    toys: Mapped[list["ToyModel"]] = db.relationship()


class ToyModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey(ChildModel.id))
    child = db.relationship(ChildModel, back_populates="toys")


class GuardianSchema(ma.Schema):
    name = mf.String(required=True)


class ChildSchema(ma.Schema):
    name = mf.String(required=True)
    guardian_id = mf.Integer(required=True, load_only=True)


class ToySchema(ma.Schema):
    name = mf.String(required=True)
    child_id = mf.Integer(required=True, load_only=True)


api_blueprint = Blueprint("v1_api", __name__, url_prefix="/api/v1/")


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


class GuardianApiView(BaseApiView):
    api_name = "guardians"
    Model = GuardianModel
    ResponseSchema = GuardianSchema
    CreateSchema = GuardianSchema
    PatchSchema = GuardianSchema
    UpdateSchema = GuardianSchema
    searchable_columns = [GuardianModel.name]


class ChildApiView(BaseApiView):
    api_name = "children"
    Model = ChildModel
    ResponseSchema = ChildSchema
    CreateSchema = ChildSchema
    PatchSchema = ChildSchema
    UpdateSchema = ChildSchema
    parent = GuardianApiView
    searchable_columns = [ChildModel.name]


class ToyApiView(BaseApiView):
    api_name = "toys"
    Model = ToyModel
    ResponseSchema = ToySchema
    CreateSchema = ToySchema
    PatchSchema = ToySchema
    UpdateSchema = ToySchema
    parent = ChildApiView
    searchable_columns = [ToyModel.name]


# Add all url rules to the blueprint.
GuardianApiView.add_crud_to_blueprint(api_blueprint)
ChildApiView.add_crud_to_blueprint(api_blueprint)
ToyApiView.add_crud_to_blueprint(api_blueprint)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo_example.db"
    app.config["TESTING"] = True
    app.config["DEBUG"] = True
    app.test_client_class = FlaskLoginClient
    login_manager.init_app(app)
    db.init_app(app)
    app.register_blueprint(api_blueprint)
    return app
