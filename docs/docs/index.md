# Welcome to Flask-Muck
![Logo](img/logo.png)

[![CI Testing](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/dtiesling/flask-muck/actions/workflows/test.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/)



Flask-Muck is a batteries-included framework for automatically generating RESTful APIs with Create, Read, 
Update and Delete (CRUD) endpoints in a Flask/SqlAlchemy application stack. 

## Features
- Automatic generation of CRUD endpoints.
- Built-in search, filter, sort and pagination when listing resources.
- Support for APIs with nested resources (i.e. /api/class/<ID>/students).
- Fully compatible with any other Flask method-based or class-based views. Mix & match with your existing views.
- Pre and post callbacks configurable on all manipulation endpoints that allow for arbitrary logic before and after Create, Update or Delete operations.

## License
Flask-Muck is distributed under the [MIT](https://spdx.org/licenses/MIT.html) license.

