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
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped

from flask_muck import FlaskMuckCallback, FlaskMuck
from flask_muck.views import FlaskMuckApiView

login_manager = LoginManager()


# Init Flask-SQLAlchemy and set database to a local sqlite file.
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


# Create SQLAlchemy database models.
class UserModel(db.Model, UserMixin):
    """Flask-Login User model to use for authentication."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


class FamilyModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    surname = db.Column(db.String, nullable=False)


class GuardianModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=True)
    family_id = db.Column(db.Integer, db.ForeignKey(FamilyModel.id))
    family = db.relationship(FamilyModel)
    children: Mapped[list["ChildModel"]] = db.relationship()


class ChildModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    family_id = db.Column(db.Integer, db.ForeignKey(FamilyModel.id))
    guardian_id = db.Column(db.Integer, db.ForeignKey(GuardianModel.id))
    guardian = db.relationship(GuardianModel, back_populates="children")
    toy: Mapped["ToyModel"] = db.relationship(uselist=False)


class ToyModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey(FamilyModel.id))
    child_id = db.Column(db.Integer, db.ForeignKey(ChildModel.id))
    child = db.relationship(ChildModel, back_populates="toy")


class GuardianSchema(BaseModel):
    name: str


class ChildSchema(ma.Schema):
    name = mf.String(required=True)
    guardian_id = mf.Integer(required=True, load_only=True)


class GuardianDetailSchema(ma.Schema):
    name = mf.String(required=True)
    children = mf.Nested(ChildSchema, many=True)


class ToySchema(ma.Schema):
    name = mf.String(required=True)
    child_id = mf.Integer(required=True, load_only=True)


api_blueprint = Blueprint("api", __name__, url_prefix="/")


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
class PreCallback(FlaskMuckCallback):
    def execute(self) -> None:
        return


class PostCallback(FlaskMuckCallback):
    def execute(self) -> None:
        return


class BaseApiView(FlaskMuckApiView):
    """Base view to inherit from. Helpful for setting class variables shared with all API views such as "sqlalchemy_db"
    and "decorators".
    """

    session = db.session
    decorators = [login_required]
    pre_create_callbacks = [PreCallback]
    pre_update_callbacks = [PreCallback]
    pre_patch_callbacks = [PreCallback]
    pre_delete_callbacks = [PreCallback]
    post_create_callbacks = [PostCallback]
    post_update_callbacks = [PostCallback]
    post_patch_callbacks = [PostCallback]
    post_delete_callbacks = [PostCallback]


class GuardianApiView(BaseApiView):
    api_name = "guardians"
    Model = GuardianModel
    ResponseSchema = GuardianSchema
    CreateSchema = GuardianSchema
    PatchSchema = GuardianSchema
    UpdateSchema = GuardianSchema
    DetailSchema = GuardianDetailSchema
    searchable_columns = [GuardianModel.name, GuardianModel.age]


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
    api_name = "toy"
    Model = ToyModel
    ResponseSchema = ToySchema
    CreateSchema = ToySchema
    PatchSchema = ToySchema
    UpdateSchema = ToySchema
    parent = ChildApiView
    one_to_one_api = True


def create_app(use_extension: bool = True) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo_example.db"
    app.config["TESTING"] = True
    app.config["DEBUG"] = True
    app.test_client_class = FlaskLoginClient
    login_manager.init_app(app)
    db.init_app(app)
    if use_extension:
        muck = FlaskMuck(app)
        with app.app_context():
            muck.register_muck_views([GuardianApiView, ChildApiView, ToyApiView])
    else:
        GuardianApiView.add_rules_to_blueprint(api_blueprint)
        ChildApiView.add_rules_to_blueprint(api_blueprint)
        ToyApiView.add_rules_to_blueprint(api_blueprint)
        app.register_blueprint(api_blueprint)
    return app
