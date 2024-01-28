import json

from flask import current_app
from flask.cli import with_appcontext, AppGroup
from rich import print_json

muck_cli = AppGroup("muck")


@muck_cli.command()  # type: ignore
@with_appcontext
def openapi_spec() -> None:
    """Print OpenAPI spec JSON for this app's API."""
    muck = current_app.extensions.get("muck")
    if muck is None:
        print("No Flask-Muck extension initialized in this app")
    print_json(json.dumps(muck.spec.to_dict(), indent=2))
