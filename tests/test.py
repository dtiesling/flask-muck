import json

import pytest

from flask_muck.utils import (
    get_url_rule,
    get_fk_column,
    get_query_filters_from_request_path,
    get_join_models_from_parent_views,
)
from tests.app import (
    GuardianModel,
    ToyApiView,
    ChildModel,
    ToyModel,
    BaseApiView,
)


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


class TestAllowedMethods:
    def test_get_only(self, client, monkeypatch):
        monkeypatch.setattr(BaseApiView, "allowed_methods", {"GET"})
        assert client.get("/api/v1/guardians/").status_code == 200
        assert client.post("/api/v1/guardians/").status_code == 405
        assert client.put("/api/v1/guardians/").status_code == 405
        assert client.patch("/api/v1/guardians/").status_code == 405
        assert client.delete("/api/v1/guardians/").status_code == 405

    def test_no_methods(self, client, monkeypatch):
        monkeypatch.setattr(BaseApiView, "allowed_methods", {})
        assert client.get("/api/v1/guardians/").status_code == 405
        assert client.post("/api/v1/guardians/").status_code == 405
        assert client.put("/api/v1/guardians/").status_code == 405
        assert client.patch("/api/v1/guardians/").status_code == 405
        assert client.delete("/api/v1/guardians/").status_code == 405


@pytest.mark.usefixtures("simpson_family", "belcher_family")
class TestFiltering:
    @pytest.fixture
    def filter_guardians(self, get):
        def _filter_guardians(filters: dict, expected_status_code: int = 200):
            return get(
                f"/api/v1/guardians/",
                query_string={"filters": json.dumps(filters)},
                expected_status_code=expected_status_code,
            )

        return _filter_guardians

    def test_equal(self, filter_guardians):
        assert filter_guardians({"name": "Marge"}) == [{"name": "Marge"}]
        assert filter_guardians({"name": "Bob"}) == [{"name": "Bob"}]
        assert filter_guardians({"name": "Marge", "age": 34}) == [{"name": "Marge"}]
        assert filter_guardians({"name": "Marge", "age": 45}) == []

    def test_gt(self, filter_guardians):
        assert filter_guardians({"age__gt": 18}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]
        assert filter_guardians({"age__gt": 34}) == [{"name": "Bob"}]
        assert filter_guardians({"age__gt": 46}) == []

    def test_gte(self, filter_guardians):
        assert filter_guardians({"age__gte": 18}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]
        assert filter_guardians({"age__gte": 34}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]
        assert filter_guardians({"age__gte": 46}) == [{"name": "Bob"}]
        assert filter_guardians({"age__gte": 47}) == []

    def test_lt(self, filter_guardians):
        assert filter_guardians({"age__lt": 18}) == []
        assert filter_guardians({"age__lt": 34}) == []
        assert filter_guardians({"age__lt": 46}) == [{"name": "Marge"}]
        assert filter_guardians({"age__lt": 47}) == [{"name": "Marge"}, {"name": "Bob"}]

    def test_lte(self, filter_guardians):
        assert filter_guardians({"age__lte": 18}) == []
        assert filter_guardians({"age__lte": 34}) == [{"name": "Marge"}]
        assert filter_guardians({"age__lte": 46}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]
        assert filter_guardians({"age__lte": 47}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]

    def test_in(self, filter_guardians):
        assert filter_guardians({"name__in": ["Marge", "Bob"]}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]
        assert filter_guardians({"name__in": ["Marge"]}) == [{"name": "Marge"}]
        assert filter_guardians({"name__in": ["Bob"]}) == [{"name": "Bob"}]
        assert filter_guardians({"name__in": ["Billy"]}) == []

    def test_not_in(self, filter_guardians):
        assert filter_guardians({"name__not_in": ["Marge", "Bob"]}) == []
        assert filter_guardians({"name__not_in": ["Marge"]}) == [{"name": "Bob"}]
        assert filter_guardians({"name__not_in": ["Bob"]}) == [{"name": "Marge"}]
        assert filter_guardians({"name__not_in": ["Billy"]}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]

    def test_ne(self, filter_guardians):
        assert filter_guardians({"name__ne": "Marge"}) == [{"name": "Bob"}]
        assert filter_guardians({"name__ne": "Bob"}) == [{"name": "Marge"}]
        assert filter_guardians({"name__ne": "Billy"}) == [
            {"name": "Marge"},
            {"name": "Bob"},
        ]

    def test_change_operator_separator(self, filter_guardians, monkeypatch):
        monkeypatch.setattr(BaseApiView, "operator_separator", "|")
        assert filter_guardians({"name|ne": "Marge"}) == [{"name": "Bob"}]
        assert filter_guardians({"name|in": ["Marge"]}) == [{"name": "Marge"}]

    def test_nested_filter(self, filter_guardians, client):
        assert filter_guardians({"children.name": "Bart"}) == [{"name": "Marge"}]
        assert filter_guardians({"children.name": "Gene"}) == [{"name": "Bob"}]
        filter_guardians({"children.nope": "fail"}, expected_status_code=400)


class TestSort:
    def test_sort(self, get, simpson_family, belcher_family):
        marge, bart, maggie, lisa, skateboard, saxophone, pacifier = simpson_family
        assert get(
            f"/api/v1/guardians/{marge.id}/children/", query_string={"sort": "name"}
        ) == [{"name": bart.name}, {"name": lisa.name}, {"name": maggie.name}]
        assert get(
            f"/api/v1/guardians/{marge.id}/children/", query_string={"sort": "age"}
        ) == [{"name": maggie.name}, {"name": lisa.name}, {"name": bart.name}]

    def test_sort_asc(self, get, simpson_family, belcher_family):
        marge, bart, maggie, lisa, skateboard, saxophone, pacifier = simpson_family
        assert get(
            f"/api/v1/guardians/{marge.id}/children/", query_string={"sort": "age__asc"}
        ) == [{"name": maggie.name}, {"name": lisa.name}, {"name": bart.name}]
        assert get(
            f"/api/v1/guardians/{marge.id}/children/",
            query_string={"sort": "name__asc"},
        ) == [{"name": bart.name}, {"name": lisa.name}, {"name": maggie.name}]

    def test_sort_desc(self, get, simpson_family, belcher_family):
        marge, bart, maggie, lisa, skateboard, saxophone, pacifier = simpson_family
        assert get(
            f"/api/v1/guardians/{marge.id}/children/",
            query_string={"sort": "age__desc"},
        ) == [{"name": bart.name}, {"name": lisa.name}, {"name": maggie.name}]
        assert get(
            f"/api/v1/guardians/{marge.id}/children/",
            query_string={"sort": "name__desc"},
        ) == [{"name": maggie.name}, {"name": lisa.name}, {"name": bart.name}]

    def test_change_operator_separator(
        self, get, simpson_family, belcher_family, monkeypatch
    ):
        monkeypatch.setattr(BaseApiView, "operator_separator", "|")
        marge, bart, maggie, lisa, skateboard, saxophone, pacifier = simpson_family
        assert get(
            f"/api/v1/guardians/{marge.id}/children/",
            query_string={"sort": "age|desc"},
        ) == [{"name": bart.name}, {"name": lisa.name}, {"name": maggie.name}]
        assert get(
            f"/api/v1/guardians/{marge.id}/children/",
            query_string={"sort": "name|desc"},
        ) == [{"name": maggie.name}, {"name": lisa.name}, {"name": bart.name}]


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
