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

## Swagger UI

Go to [http://127.0.0.1:5000/apidocs/](http://127.0.0.1:5000/apidocs/) in a browser.

## CURL Commands

### Login
```
curl -X POST -c cookies.txt --location "http://127.0.0.1:5000/auth/login"
```

### Logout
```
curl -X POST -c cookies.txt --location "http://127.0.0.1:5000/auth/logout"
```

### Create a ToDo item
```
curl -X POST -b cookies.txt --location "http://127.0.0.1:5000/todos/" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"take out garbage again\"
        }"
```

### List all ToDo items (flat)
```
curl -X GET -b cookies.txt --location "http://127.0.0.1:5000/todos/" \
    -d "Accept: application/json"
```

### List all ToDo items (paginated)
```
curl -X GET -b cookies.txt --location "http://127.0.0.1:5000/todos/?limit=2&offset=1" \
    -d "Accept: application/json"
```

### Search ToDo items
```
curl -X GET -b cookies.txt --location "http://127.0.0.1:5000/todos/?search=garbage" \
    -d "Accept: application/json"
```

### Filter ToDo items
```
curl -X GET -b cookies.txt --location "http://127.0.0.1:5000/todos/?filters=%7B%22text%22%3A+%22take+out+garbage+again%22%7D" \
    -d "Accept: application/json"
```
_querystring urldecodes to `filters={"text": "take out garbage again"}`_ 

### Sort ToDo items
```
curl -X GET -b cookies.txt --location "http://127.0.0.1:5000/todos/?sort=text" \
    -d "Accept: application/json"
``` 

### Fetch ToDo item
```
curl -X GET -b cookies.txt --location "http://127.0.0.1:5000/todos/1/" \
    -d "Accept: application/json"
```

### Update ToDo item
```
curl -X PUT -b cookies.txt --location "http://127.0.0.1:5000/todos/1/" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"Updated todo item\"
        }"
```

### Patch ToDo item
```
curl -X PATCH -b cookies.txt --location "http://127.0.0.1:5000/todos/1/" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"Updated todo item\"
        }"
```

### Delete ToDo Item
```
curl -X DELETE -b cookies.txt --location "http://127.0.0.1:5000/todos/1/"
```
