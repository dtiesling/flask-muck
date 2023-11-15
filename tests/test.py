import json

import pytest

from flask_muck.utils import (
    get_url_rule,
    get_fk_column,
    get_query_filters_from_request_path,
    get_join_models_from_parent_views,
)
from tests.app import GuardianModel, ToyApiView, ChildModel, ToyModel


class TestBasicCrud:
    def test_create(self, post, user):
        response = post("/api/v1/guardians/", json={"name": "Jill"})
        parent = GuardianModel.query.one()
        assert response == {"name": parent.name}

    def test_read(self, get, user, guardian):
        assert get(f"/api/v1/guardians/{guardian.id}") == {"name": guardian.name}
        assert get(f"/api/v1/guardians/") == [{"name": guardian.name}]

    def test_update(self, put, patch, guardian):
        assert put(f"/api/v1/guardians/{guardian.id}", json={"name": "updated"}) == {
            "name": "updated"
        }
        assert patch(f"/api/v1/guardians/{guardian.id}", json={"name": "patched"}) == {
            "name": "patched"
        }

    def test_delete(self, client, guardian):
        client.delete(f"/api/v1/guardians/{guardian.id}")
        assert GuardianModel.query.count() == 0


@pytest.mark.usefixtures("simpson_family", "belcher_family")
class TestFiltering:
    @pytest.fixture
    def filter_guardians(self, get):
        def _filter_guardians(filters: dict):
            return get(
                f"/api/v1/guardians/", query_string={"filters": json.dumps(filters)}
            )

        return _filter_guardians

    def test_equal(self, filter_guardians):
        assert filter_guardians({"name": "Marge"}) == [{"name": "Marge"}]


class TestNestedApis:
    def test_get(self, get, simpson_family, belcher_family, db):
        marge, bart, maggie, lisa, skateboard, saxophone, pacifier = simpson_family
        bob, tina, louise, gene, pony, hat, keyboard = belcher_family
        children = (bart, maggie, lisa)
        assert get(f"/api/v1/guardians/") == [{"name": marge.name}, {"name": bob.name}]
        assert get(f"/api/v1/guardians/{marge.id}/children/") == [
            {"name": child.name} for child in children
        ]
        assert get(f"/api/v1/guardians/{marge.id}/children/{bart.id}/toys/") == [
            {"name": skateboard.name}
        ]


class TestBlueprintRegistering:
    def test_str_pk_patch_creation(self):
        return

    def test_int_pk_patch_update(self):
        return


class TestUtils:
    def test_get_url_rule(self):
        assert (
            get_url_rule(ToyApiView, None)
            == "guardians/<int:guardians_id>/children/<int:children_id>/toys/"
        )

    def test_get_fk_column(self):
        assert (
            get_fk_column(parent_model=GuardianModel, child_model=ChildModel)
            == ChildModel.guardian_id
        )
        assert (
            get_fk_column(parent_model=ChildModel, child_model=ToyModel)
            == ToyModel.child_id
        )
        assert get_fk_column(parent_model=GuardianModel, child_model=ToyModel) is None

    def test_get_query_filters_from_request_path(self, app):
        with app.test_request_context("/api/v1/guardians/65/children/22/toys/"):
            assert [
                str(i) for i in get_query_filters_from_request_path(ToyApiView, [])
            ] == [
                str(ToyModel.child_id == 22),
                str(ChildModel.guardian_id == 65),
            ]

    def test_get_join_models_from_parent_views(self):
        assert get_join_models_from_parent_views(ToyApiView, []) == [
            GuardianModel,
            ChildModel,
        ]
