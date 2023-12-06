[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI Testing](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml)
[![CodeQL](https://github.com/dtiesling/flask-muck/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/dtiesling/flask-muck/actions/workflows/github-code-scanning/codeql)
[![Docs Deploy](https://github.com/dtiesling/flask-muck/actions/workflows/docs.yml/badge.svg)](https://github.com/dtiesling/flask-muck/actions/workflows/docs.yml)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![Static Badge](https://img.shields.io/badge/Flask-v2%20%7C%20v3-red)](https://flask.palletsprojects.com/en/3.0.x/)
[![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/)
![downloads](https://img.shields.io/pypi/dm/flask-muck)
[![pypi version](https://img.shields.io/pypi/v/flask-muck)](https://pypi.org/project/Flask-Muck/)
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)


# Flask-Muck

![Logo](https://dtiesling.github.io/flask-muck/img/logo.png)

With Flask-Muck you don't have to worry about the CRUD.

Flask-Muck is a batteries-included framework for automatically generating RESTful APIs with Create, Read, 
Update and Delete (CRUD) endpoints in a Flask/SqlAlchemy application stack in as little as 9 lines of code. 



```python
from flask import Blueprint
from flask_muck.views import FlaskMuckApiView
import marshmallow as ma
from marshmallow import fields as mf

from myapp import db


class MyModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)


class MyModelSchema(ma.Schema):
    id = mf.Integer(dump_only=True)
    name = mf.String()


class MyModelApiView(FlaskMuckApiView):
    api_name = "my-model"
    session = db.session
    Model = MyModel
    ResponseSchema = MyModelSchema
    CreateSchema = MyModelSchema
    PatchSchema = MyModelSchema
    UpdateSchema = MyModelSchema
    searchable_columns = [MyModel.name]


blueprint = Blueprint("api", __name__, url_prefix="/api/")
MyModelApiView.add_rules_to_blueprint(blueprint)

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

## Documentation

Please visit the docs at [https://dtiesling.github.io/flask-muck/](https://dtiesling.github.io/flask-muck/) for explanation of all features and 
advanced usage guides.

There are also examples of complete Flask apps using Flask-Muck in the [examples](./examples) directory.

## Install

Flask-Muck is in Beta and does not have a standard version available for install yet. A standard release on PyPi is coming soon.

`pip install flask-muck`

Flask-Muck supports Python >= 3.9

## Issues

Submit any issues you may encounter on [GitHub](https://github.com/dtiesling/flask-muck/issues). Please search for 
similar issues before submitting a new one.

## Support
Post any questions you have as a [GitHub issue](https://github.com/dtiesling/flask-muck/issues) and add the "question" label.

## License

MIT licensed. See the [LICENSE](./LICENSE) file for more details.




## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/samdatkins"><img src="https://avatars.githubusercontent.com/u/20110283?v=4?s=100" width="100px;" alt="atkins"/><br /><sub><b>atkins</b></sub></a><br /><a href="https://github.com/dtiesling/flask-muck/commits?author=samdatkins" title="Documentation">📖</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
