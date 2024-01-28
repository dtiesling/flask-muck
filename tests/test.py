import json
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from flask_muck.exceptions import MuckImplementationError
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
    PreCallback,
    PostCallback,
    GuardianApiView,
)


class TestBasicCrud:
    def test_create(self, post, user):
        response = post("/guardians/", json={"name": "Jill"})
        parent = GuardianModel.query.one()
        assert response == {"name": parent.name}

        # Verify integrity errors are handled.
        post("/guardians/", json={"name": "Jill"}, expected_status_code=409)

    def test_read(self, get, user, guardian, child):
        assert get(f"/guardians/") == [{"name": guardian.name}]
        assert get(f"/guardians/{guardian.id}/") == {
            "name": "Samantha",
            "children": [{"name": "Tamara"}],
        }

    def test_update(self, put, patch, guardian):
        assert put(f"/guardians/{guardian.id}/", json={"name": "updated"}) == {
            "name": "updated"
        }
        assert patch(f"/guardians/{guardian.id}/", json={"name": "patched"}) == {
            "name": "patched"
        }

    def test_delete(self, client, guardian):
        client.delete(f"/guardians/{guardian.id}/")
        assert GuardianModel.query.count() == 0


class TestAllowedMethods:
    def test_get_only(self, client, monkeypatch):
        monkeypatch.setattr(BaseApiView, "allowed_methods", {"GET"})
        assert client.get("/guardians/").status_code == 200
        assert client.post("/guardians/").status_code == 405
        assert client.put("/guardians/").status_code == 405
        assert client.patch("/guardians/").status_code == 405
        assert client.delete("/guardians/").status_code == 405

    def test_no_methods(self, client, monkeypatch):
        monkeypatch.setattr(BaseApiView, "allowed_methods", {})
        assert client.get("/guardians/").status_code == 405
        assert client.post("/guardians/").status_code == 405
        assert client.put("/guardians/").status_code == 405
        assert client.patch("/guardians/").status_code == 405
        assert client.delete("/guardians/").status_code == 405


@pytest.mark.usefixtures("simpsons", "belchers")
class TestPagination:
    def test_offset(self, get):
        assert get("/guardians/?offset=1") == {
            "items": [{"name": "Bob"}],
            "limit": 20,
            "offset": 1,
            "total": 2,
        }

    def test_limit(self, get):
        assert get("/guardians/?limit=1") == {
            "items": [{"name": "Marge"}],
            "limit": 1,
            "offset": 0,
            "total": 2,
        }

    def test_limit_and_offset(self, get):
        assert get("/guardians/?limit=10&offset=0") == {
            "items": [{"name": "Marge"}, {"name": "Bob"}],
            "limit": 10,
            "offset": 0,
            "total": 2,
        }


@pytest.mark.usefixtures("simpsons", "belchers")
class TestFiltering:
    @pytest.fixture
    def filter_guardians(self, get):
        def _filter_guardians(filters: dict, expected_status_code: int = 200):
            return get(
                f"/guardians/?filters={json.dumps(filters)}",
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
            {"name": "Bob"},
            {"name": "Marge"},
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

    def test_bad_json(self, get):
        get("/guardians/?filters=notjson", expected_status_code=400)

    def test_column_does_not_exist(self, filter_guardians):
        filter_guardians({"nope": "fail"}, expected_status_code=400)
        filter_guardians({"nope.nested": "fail"}, expected_status_code=400)
        filter_guardians({"children.nope": "fail"}, expected_status_code=400)


@pytest.mark.usefixtures("simpsons", "belchers")
class TestSort:
    def test_sort(self, get, marge, bart, maggie, lisa):
        assert get(f"/guardians/{marge.id}/children/?sort=name") == [
            {"name": bart.name},
            {"name": lisa.name},
            {"name": maggie.name},
        ]
        assert get(f"/guardians/{marge.id}/children/?sort=age") == [
            {"name": maggie.name},
            {"name": lisa.name},
            {"name": bart.name},
        ]

    def test_sort_asc(self, get, marge, maggie, lisa, bart):
        assert get(f"/guardians/{marge.id}/children/?sort=age__asc") == [
            {"name": maggie.name},
            {"name": lisa.name},
            {"name": bart.name},
        ]
        assert get(
            f"/guardians/{marge.id}/children/?sort=name__asc",
        ) == [{"name": bart.name}, {"name": lisa.name}, {"name": maggie.name}]

    def test_sort_desc(self, get, marge, lisa, maggie, bart):
        assert get(
            f"/guardians/{marge.id}/children/?sort=age__desc",
        ) == [{"name": bart.name}, {"name": lisa.name}, {"name": maggie.name}]
        assert get(
            f"/guardians/{marge.id}/children/?sort=name__desc",
        ) == [{"name": maggie.name}, {"name": lisa.name}, {"name": bart.name}]

    def test_nested_sort(self, get):
        assert get(f"/guardians/?sort=family.surname") == [
            {"name": "Bob"},
            {"name": "Marge"},
        ]

    def test_bad_sort(self, get):
        get(f"/guardians/?sort=name__fail", expected_status_code=400)
        get(f"/guardians/?sort=fail", expected_status_code=400)
        get(f"/guardians/?sort=family.fail", expected_status_code=400)
        get(f"/guardians/?sort=double.fail", expected_status_code=400)

    def test_change_operator_separator(
        self, get, monkeypatch, marge, lisa, bart, maggie
    ):
        monkeypatch.setattr(BaseApiView, "operator_separator", "|")
        assert get(
            f"/guardians/{marge.id}/children/?sort=age|desc",
        ) == [{"name": bart.name}, {"name": lisa.name}, {"name": maggie.name}]
        assert get(
            f"/guardians/{marge.id}/children/?sort=name|desc",
        ) == [{"name": maggie.name}, {"name": lisa.name}, {"name": bart.name}]


@pytest.mark.usefixtures("simpsons", "belchers")
class TestSearch:
    def test_search(self, get, marge):
        assert get(f"/guardians/?search=marge") == [{"name": "Marge"}]
        assert get(f"/guardians/?search=nobody") == []
        assert get(f"/guardians/{marge.id}/children/?search=bart") == [{"name": "Bart"}]
        assert get(f"/guardians/{marge.id}/children/?search=nope") == []

    def test_unsupported_search(self, get, marge, bart, monkeypatch):
        monkeypatch.setattr(GuardianApiView, "searchable_columns", [])
        get(f"/guardians/?search=marge", expected_status_code=400)


class TestCallbacks:
    @pytest.fixture
    def pre_callback_patch(self):
        with patch.object(PreCallback, "execute") as patched:
            yield patched

    @pytest.fixture
    def post_callback_patch(self):
        with patch.object(PostCallback, "execute") as patched:
            yield patched

    def test_create_callbacks(
        self, post, user, pre_callback_patch, post_callback_patch
    ):
        post("/guardians/", json={"name": "Jill"})
        pre_callback_patch.assert_called_once()
        post_callback_patch.assert_called_once()

    def test_update_callbacks(
        self, put, guardian, pre_callback_patch, post_callback_patch
    ):
        put(f"/guardians/{guardian.id}/", json={"name": "updated"})
        pre_callback_patch.assert_called_once()
        post_callback_patch.assert_called_once()

    def test_patch_callbacks(
        self, put, patch, guardian, pre_callback_patch, post_callback_patch
    ):
        patch(f"/guardians/{guardian.id}/", json={"name": "patched"})
        pre_callback_patch.assert_called_once()
        post_callback_patch.assert_called_once()

    def test_delete_callbacks(
        self, client, guardian, pre_callback_patch, post_callback_patch
    ):
        client.delete(f"/guardians/{guardian.id}/")
        pre_callback_patch.assert_called_once()
        post_callback_patch.assert_called_once()


@pytest.mark.usefixtures("simpsons", "belchers")
class TestNestedApis:
    def test_get(self, get, bart, maggie, lisa, marge, skateboard, bob):
        children = (bart, maggie, lisa)
        assert get(f"/guardians/") == [{"name": marge.name}, {"name": bob.name}]
        assert get(f"/guardians/{marge.id}/children/") == [
            {"name": child.name} for child in children
        ]
        assert get(f"/guardians/{marge.id}/children/{bart.id}/toy/") == {
            "name": skateboard.name
        }


class TestBlueprintRegistering:
    def test_str_pk_patch_creation(self):
        return

    def test_int_pk_patch_update(self):
        return


class TestUtils:
    def test_get_url_rule(self):
        assert (
            get_url_rule(ToyApiView, None)
            == "/guardians/<int:guardian_model_id>/children/<int:child_model_id>/toy/"
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
        with pytest.raises(
            MuckImplementationError,
            match="The ToyModel model does not have a foreign key.*",
        ):
            get_fk_column(parent_model=GuardianModel, child_model=ToyModel)

    def test_get_query_filters_from_request_path(self, app):
        with app.test_request_context("/guardians/65/children/22/toy/"):
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


@pytest.mark.usefixtures("simpsons", "belchers")
class TestBaseQueryKwargs:
    @pytest.fixture(autouse=True)
    def patch_get_base_query_kwargs(self, simpson_family, monkeypatch):
        monkeypatch.setattr(
            BaseApiView,
            "get_base_query_kwargs",
            lambda self: {"family_id": simpson_family.id},
        )

    def test_get(self, get, marge, lisa):
        assert get("/guardians/") == [{"name": "Marge"}]
        assert get(f"/guardians/{marge.id}/children/") == [
            {"name": "Bart"},
            {"name": "Maggie"},
            {"name": "Lisa"},
        ]
        assert get(f"/guardians/{marge.id}/children/{lisa.id}/toy/") == {
            "name": "Saxophone"
        }

    def test_put(self, put, marge, bart, db, belcher_family, simpson_family):
        assert put(f"/guardians/{marge.id}/", json={"name": "Marjory"})
        db.session.refresh(marge)
        assert marge.name == "Marjory"
        assert put(
            f"/guardians/{marge.id}/children/{bart.id}/",
            json={"name": "Bartholomew", "guardian_id": marge.id},
        )
        assert put(
            f"/guardians/{marge.id}/children/{bart.id}/toy/",
            json={"name": "Scooter", "child_id": bart.id},
        )
        assert put(
            f"/guardians/{marge.id}/children/{bart.id}/toy/",
            json={
                "name": "Scooter",
                "child_id": bart.id,
            },
        )

    def test_patch(self, patch, marge, bart, skateboard, db):
        assert patch(f"/guardians/{marge.id}/", json={"name": "Marjory"})
        db.session.refresh(marge)
        assert marge.name == "Marjory"
        assert patch(
            f"/guardians/{marge.id}/children/{bart.id}/",
            json={"name": "Bartholomew"},
        )
        assert patch(
            f"/guardians/{marge.id}/children/{bart.id}/toy/",
            json={"name": "Scooter"},
        )


class TestOpenAPI:
    def test_openapi_marshmallow(self, app, snapshot):
        if muck := app.extensions.get("muck"):
            assert snapshot == muck.openapi_spec_dict


class TestCommands:
    def test_openapi(self, cli_runner, snapshot):
        from flask_muck.commands import openapi_spec

        result = cli_runner.invoke(openapi_spec)
        assert snapshot == result.output
