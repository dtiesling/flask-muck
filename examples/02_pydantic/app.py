from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from pydantic import BaseModel
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


class TodoResponseSchema(BaseModel):
    id: int
    text: str


class TodoPayloadSchema(BaseModel):
    text: str


api_blueprint = Blueprint("v1_api", __name__, url_prefix="/api/v1/")


class TodoApiView(FlaskMuckApiView):
    session = db.session
    api_name = "todos"
    Model = TodoModel
    ResponseSchema = TodoResponseSchema
    CreateSchema = TodoPayloadSchema
    PatchSchema = TodoPayloadSchema
    UpdateSchema = TodoPayloadSchema
    searchable_columns = [TodoModel.text]


TodoApiView.add_rules_to_blueprint(api_blueprint)
app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
