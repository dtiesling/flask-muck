# Adding Flask-Muck To An Existing API Example

It's very likely you'll need to add Flask-Muck to an existing Flask API. This example shows how to use the utility
methods to incorporate Flask-Muck into existing api blueprints and bypass the extension.

This example results in the same API as the Quickstart without initializing the extension. 

Below are instruction on running the sample app as well as a list of CURL commands demonstrating the endpoints 
generated by Flask-Muck.

## Prequisites 

- [Python 3.11](https://www.python.org/downloads/)
- [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)

## Start The REST API.

`pipenv run python3 app.py`

## Swagger UI

Go to [http://127.0.0.1:5000/apidocs/](http://127.0.0.1:5000/apidocs/) in a browser.

## CURL Commands

### Create a ToDo item
```
curl -X POST --location "http://127.0.0.1:5000/todos/" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"take out garbage again\"
        }"
```

### List all ToDo items (flat)
```
curl -X GET --location "http://127.0.0.1:5000/todos/" \
    -d "Accept: application/json"
```

### List all ToDo items (paginated)
```
curl -X GET --location "http://127.0.0.1:5000/todos/?limit=2&offset=1" \
    -d "Accept: application/json"
```

### Search ToDo items
```
curl -X GET --location "http://127.0.0.1:5000/todos/?search=garbage" \
    -d "Accept: application/json"
```

### Filter ToDo items
```
curl -X GET --location "http://127.0.0.1:5000/todos/?filters=%7B%22text%22%3A+%22take+out+garbage+again%22%7D" \
    -d "Accept: application/json"
```
_querystring urldecodes to `filters={"text": "take out garbage again"}`_ 

### Sort ToDo items
```
curl -X GET --location "http://127.0.0.1:5000/todos/?sort=text" \
    -d "Accept: application/json"
``` 

### Fetch ToDo item
```
curl -X GET --location "http://127.0.0.1:5000/todos/1/" \
    -d "Accept: application/json"
```

### Update ToDo item
```
curl -X PUT --location "http://127.0.0.1:5000/todos/1/" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"Updated todo item\"
        }"
```

### Patch ToDo item
```
curl -X PATCH --location "http://127.0.0.1:5000/todos/1/" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"Updated todo item\"
        }"
```

### Delete ToDo Item
```
curl -X DELETE --location "http://127.0.0.1:5000/todos/1/"
```
