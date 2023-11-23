[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI Testing](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml)

# flask-muck
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
    name = mf.String(required=True)

class MyModelApiView(MuckApiView):
    api_name = "my-model"
    Model = MyModel
    ResponseSchema = MyModel
    CreateSchema = MyModel
    PatchSchema = MyModel
    UpdateSchema = MyModel
    searchable_columns = [MyModel.name]

blueprint = Blueprint("api", __name__, url_prefix="/api/")
MyModelApiView.add_crud_to_blueprint(blueprint)

# Available Endpoint
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

## Install

`pip install flask-muck`

Flask-Muck supports Python >= 3.9

## Documentation

Refer to the [examples](./examples) directory for more information on usage and available features.

Full documentation is coming soon. 

## License

MIT licensed. See the [LICENSE](./LICENSE) file for more details.



