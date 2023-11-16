import pytest
from sqlalchemy.orm import DeclarativeBase

from tests.app import create_app, UserModel, GuardianModel, ChildModel, ToyModel
from tests.app import db as _db


class Base(DeclarativeBase):
    pass


def make_request(client, method, url, expected_status_code, **kwargs):
    response = getattr(client, method)(url, **kwargs)
    if response.status_code != expected_status_code:
        raise AssertionError(
            f"Expected status code {expected_status_code}, got {response.status_code}"
        )
    return response.json


@pytest.fixture
def get(client):
    def _get(url, expected_status_code=200, **kwargs):
        return make_request(client, "get", url, expected_status_code, **kwargs)

    return _get


@pytest.fixture
def post(client):
    def _post(url, expected_status_code=201, **kwargs):
        return make_request(client, "post", url, expected_status_code, **kwargs)

    return _post


@pytest.fixture
def put(client):
    def _put(url, expected_status_code=200, **kwargs):
        return make_request(client, "put", url, expected_status_code, **kwargs)

    return _put


@pytest.fixture
def patch(client):
    def _patch(url, expected_status_code=200, **kwargs):
        return make_request(client, "patch", url, expected_status_code, **kwargs)

    return _patch


@pytest.fixture
def delete(client):
    def _delete(url, expected_status_code=204, **kwargs):
        return make_request(client, "delete", url, expected_status_code, **kwargs)

    return _delete


@pytest.fixture
def db(app):
    _db.create_all()
    yield _db
    _db.session.close()
    _db.drop_all()


@pytest.fixture(scope="session")
def app():
    app = create_app()
    with app.app_context():
        yield app


@pytest.fixture
def client(app, user):
    return app.test_client(user=user)


@pytest.fixture
def user(db):
    user = UserModel()
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def guardian(db):
    parent = GuardianModel(name="Samantha")
    db.session.add(parent)
    db.session.flush()
    return parent


@pytest.fixture
def simpson_family(db):
    marge = GuardianModel(name="Marge", age=34)
    db.session.add(marge)
    db.session.flush()
    bart = ChildModel(name="Bart", age=10, guardian_id=marge.id)
    maggie = ChildModel(name="Maggie", age=1, guardian_id=marge.id)
    lisa = ChildModel(name="Lisa", age=8, guardian_id=marge.id)
    db.session.add_all([bart, maggie, lisa])
    db.session.flush()
    skateboard = ToyModel(name="Skateboard", child_id=bart.id)
    saxophone = ToyModel(name="Saxophone", child_id=lisa.id)
    pacifier = ToyModel(name="Pacifier", child_id=maggie.id)
    db.session.add_all([skateboard, saxophone, pacifier])
    db.session.flush()
    return marge, bart, maggie, lisa, skateboard, saxophone, pacifier


@pytest.fixture
def belcher_family(db):
    bob = GuardianModel(name="Bob", age=46)
    db.session.add(bob)
    db.session.flush()
    tina = ChildModel(name="Tina", age=12, guardian_id=bob.id)
    louise = ChildModel(name="Louise", age=9, guardian_id=bob.id)
    gene = ChildModel(name="Gene", age=11, guardian_id=bob.id)
    db.session.add_all([tina, louise, gene])
    db.session.flush()
    pony = ToyModel(name="Pony", child_id=tina.id)
    hat = ToyModel(name="Hat", child_id=louise.id)
    keyboard = ToyModel(name="Keyboard", child_id=gene.id)
    db.session.add_all([pony, hat, keyboard])
    db.session.flush()
    return bob, tina, louise, gene, pony, hat, keyboard
