# Authentication Example

If you have not already explored the [quickstart example](../00_quickstart/README.md) please start there to get an understanding 
of the endpoints available.

This example expands on the ToDo API from the quickstart and adds authentication. In this example 
[Flask-Login](https://pypi.org/project/Flask-Login/) is used to handle auth and it is added to the views by simply
adding the `login_required` decorator to the list of decorators in the `BaseApiView`.

You can see the auth in action by testing the curl commands from the [quickstart example](../00_quickstart/README.md#curl-commands)
in conjunction with the login/logout curl commands below.

Authentication is session based and stored in a cookie. You'll need to use a REST client (i.e. Postman) or configure 
curl to store/use cookies in order to test authenticated requests.

## Prequisites 

- [Python 3.11](https://www.python.org/downloads/)
- [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)

## Start The REST API.

`pipenv run python3 app.py`

## CURL Commands

### Login
`curl -X POST --location "http://127.0.0.1:5000/api/v1/login"`

### Logout
`curl -X POST --location "http://127.0.0.1:5000/api/v1/logout"`


