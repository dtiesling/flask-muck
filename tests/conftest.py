from typing import Callable, Literal

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner
from flask_sqlalchemy import SQLAlchemy
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

from flask_muck.types import JsonDict
from tests.app import (
    create_app,
    UserModel,
    GuardianModel,
    ChildModel,
    ToyModel,
    FamilyModel,
)
from tests.app import db as _db


def make_request(
    client: FlaskClient,
    method: Literal["get", "put", "patch", "post", "delete"],
    url: str,
    expected_status_code: int,
    **kwargs,
) -> JsonDict:
    response = getattr(client, method)(url, **kwargs)
    if response.status_code != expected_status_code:
        raise AssertionError(
            f"Expected status code {expected_status_code}, got {response.status_code}"
        )
    return response.json


@pytest.fixture
def create_model(db) -> Callable:
    def _create_model(model_instance: DeclarativeBase) -> DeclarativeBase:
        db.session.add(model_instance)
        db.session.flush()
        return model_instance

    return _create_model


@pytest.fixture
def get(client) -> Callable:
    def _get(url, expected_status_code=200, **kwargs):
        return make_request(client, "get", url, expected_status_code, **kwargs)

    return _get


@pytest.fixture
def post(client) -> Callable:
    def _post(url, expected_status_code=201, **kwargs):
        return make_request(client, "post", url, expected_status_code, **kwargs)

    return _post


@pytest.fixture
def put(client) -> Callable:
    def _put(url, expected_status_code=200, **kwargs):
        return make_request(client, "put", url, expected_status_code, **kwargs)

    return _put


@pytest.fixture
def patch(client) -> Callable:
    def _patch(url, expected_status_code=200, **kwargs):
        return make_request(client, "patch", url, expected_status_code, **kwargs)

    return _patch


@pytest.fixture
def delete(client) -> Callable:
    def _delete(url, expected_status_code=204, **kwargs):
        return make_request(client, "delete", url, expected_status_code, **kwargs)

    return _delete


@pytest.fixture
def db(app) -> SQLAlchemy:
    _db.create_all()
    yield _db
    _db.session.close()
    _db.drop_all()


@pytest.fixture(scope="session", params=[True, False])
def app(request) -> Flask:
    app = create_app(use_extension=request.param)
    with app.app_context():
        yield app


@pytest.fixture
def client(app, user) -> FlaskClient:
    return app.test_client(user=user)


@pytest.fixture
def cli_runner(app) -> FlaskCliRunner:
    return app.test_cli_runner()


@pytest.fixture
def user(create_model) -> UserModel:
    return create_model(UserModel())


@pytest.fixture
def family(create_model) -> FamilyModel:
    return create_model(FamilyModel(surname="Brown"))


@pytest.fixture
def guardian(family, create_model) -> GuardianModel:
    return create_model(GuardianModel(name="Samantha", family_id=family.id))


@pytest.fixture
def child(family, guardian, create_model) -> ChildModel:
    return create_model(
        ChildModel(name="Tamara", family_id=family.id, guardian_id=guardian.id)
    )


@pytest.fixture
def simpson_family(create_model) -> FamilyModel:
    return create_model(FamilyModel(surname="Simpsons"))


@pytest.fixture
def marge(simpson_family, create_model) -> GuardianModel:
    return create_model(
        GuardianModel(name="Marge", age=34, family_id=simpson_family.id)
    )


@pytest.fixture
def bart(simpson_family, marge, create_model) -> ChildModel:
    return create_model(
        ChildModel(
            name="Bart", age=10, guardian_id=marge.id, family_id=simpson_family.id
        )
    )


@pytest.fixture
def maggie(simpson_family, marge, create_model) -> ChildModel:
    return create_model(
        ChildModel(
            name="Maggie", age=1, guardian_id=marge.id, family_id=simpson_family.id
        )
    )


@pytest.fixture
def lisa(simpson_family, marge, create_model) -> ChildModel:
    return create_model(
        ChildModel(
            name="Lisa", age=8, guardian_id=marge.id, family_id=simpson_family.id
        )
    )


@pytest.fixture
def skateboard(simpson_family, bart, create_model) -> ToyModel:
    return create_model(
        ToyModel(name="Skateboard", child_id=bart.id, family_id=simpson_family.id)
    )


@pytest.fixture
def saxophone(simpson_family, lisa, create_model) -> ToyModel:
    return create_model(
        ToyModel(name="Saxophone", child_id=lisa.id, family_id=simpson_family.id)
    )


@pytest.fixture
def pacifier(simpson_family, maggie, create_model) -> ToyModel:
    return create_model(
        ToyModel(name="Pacifier", child_id=maggie.id, family_id=simpson_family.id)
    )


@pytest.fixture
def simpsons(marge, bart, maggie, lisa, skateboard, saxophone, pacifier) -> None:
    pass


@pytest.fixture
def belcher_family(create_model) -> FamilyModel:
    return create_model(FamilyModel(surname="Belcher"))


@pytest.fixture
def bob(belcher_family, create_model) -> GuardianModel:
    return create_model(GuardianModel(name="Bob", age=46, family_id=belcher_family.id))


@pytest.fixture
def tina(belcher_family, bob, create_model) -> ChildModel:
    return create_model(
        ChildModel(name="Tina", age=12, guardian_id=bob.id, family_id=belcher_family.id)
    )


@pytest.fixture
def louise(belcher_family, bob, create_model) -> ChildModel:
    return create_model(
        ChildModel(
            name="Louise", age=9, guardian_id=bob.id, family_id=belcher_family.id
        )
    )


@pytest.fixture
def gene(belcher_family, bob, create_model) -> ChildModel:
    return create_model(
        ChildModel(name="Gene", age=11, guardian_id=bob.id, family_id=belcher_family.id)
    )


@pytest.fixture
def pony(tina, belcher_family, create_model):
    return create_model(
        ToyModel(name="Pony", child_id=tina.id, family_id=belcher_family.id)
    )


@pytest.fixture
def hat(louise, belcher_family, create_model):
    return create_model(
        ToyModel(name="Hat", child_id=louise.id, family_id=belcher_family.id)
    )


@pytest.fixture
def keyboard(gene, belcher_family, create_model):
    return create_model(
        ToyModel(name="Keyboard", child_id=gene.id, family_id=belcher_family.id)
    )


@pytest.fixture
def belchers(bob, tina, louise, gene, pony, hat, keyboard) -> None:
    return


@pytest.fixture
def pydantic_swap(monkeypatch):
    from tests.app import GuardianApiView

    class GuardianPydanticModel(BaseModel):
        name: str

    monkeypatch.setattr(GuardianApiView, "ResponseSchema", GuardianPydanticModel)
    monkeypatch.setattr(GuardianApiView, "CreateSchema", GuardianPydanticModel)
    monkeypatch.setattr(GuardianApiView, "UpdateSchema", GuardianPydanticModel)
    monkeypatch.setattr(GuardianApiView, "PatchSchema", GuardianPydanticModel)
