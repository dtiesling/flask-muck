[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI Testing](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/)

# Flask-Muck

![Logo](./docs/docs/img/logo.png)

Flask-Muck is a batteries-included framework for automatically generating RESTful APIs with Create, Read, 
Update and Delete (CRUD) endpoints in a Flask/SqlAlchemy application stack. 

With Flask-Muck you don't have to worry about the CRUD. 

```python
from flask import Blueprint
from flask_muck.views import MuckApiView
import marshmallow as ma
from marshmallow import fields as mf

from myapp import db

class MyModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class MyModelSchema(ma.Schema):
    id = mf.Integer(dump_only=True)
    name = mf.String()

class MyModelApiView(MuckApiView):
    api_name = "my-model"
    session = db.session
    Model = MyModel
    ResponseSchema = MyModelSchema
    CreateSchema = MyModelSchema
    PatchSchema = MyModelSchema
    UpdateSchema = MyModelSchema
    searchable_columns = [MyModel.name]

blueprint = Blueprint("api", __name__, url_prefix="/api/")
MyModelApiView.add_crud_to_blueprint(blueprint)

# Available Endpoints:
# CREATE             | curl -X POST "/api/v1/my-model" -H "Content-Type: application/json" \-d "{\"name\": \"Ayla\"}"
# LIST ALL           | curl -X GET "/api/v1/my-model" -d "Accept: application/json"
# LIST ALL PAGINATED | curl -X GET "/api/v1/my-model?limit=100&offset=50" -d "Accept: application/json"
# SEARCH             | curl -X GET "/api/v1/my-model?search=ayla" -d "Accept: application/json"
# FILTER             | curl -X GET "/api/v1/my-model?filter={\"name\": \"Ayla\"}" -d "Accept: application/json"
# SORT               | curl -X GET "/api/v1/my-model?sort=name" -d "Accept: application/json"
# FETCH              | curl -X GET "/api/v1/my-model/1" -d "Accept: application/json"
# UPDATE             | curl -X PUT "/api/v1/my-model" -H "Content-Type: application/json" \-d "{\"name\": \"Ayla\"}"
# PATCH              | curl -X PATCH "/api/v1/my-model" -H "Content-Type: application/json" \-d "{\"name\": \"Ayla\"}"
# DELETE             | curl -X DELETE "/api/v1/my-model/1"
```

## Features
- Automatic generation of CRUD endpoints.
- Built-in search, filter, sort and pagination when listing resources.
- Support for APIs with nested resources (i.e. /api/classrooms/12345/students).
- Fully compatible with any other Flask method-based or class-based views. Mix & match with your existing views.
- Pre and post callbacks configurable on all manipulation endpoints. Allow for adding arbitrary logic before and after Create, Update or Delete operations.


## Install

Flask-Muck is in Beta and does not have a standard version available for install yet. A standard release on PyPi is coming soon.

`pip install flask-muck`

Flask-Muck supports Python >= 3.9

## Issues

Submit any issues you may encounter on [GitHub](https://github.com/dtiesling/flask-muck/issues). Please search for 
similar issues before submitting a new one.

## Documentation

Refer to the [examples](./examples) directory for more information on usage and available features.

Full documentation is a work-in-progress but will be completed soon. It can be found [here](https://dtiesling.github.io/flask-muck/). 

## License

MIT licensed. See the [LICENSE](./LICENSE) file for more details.



