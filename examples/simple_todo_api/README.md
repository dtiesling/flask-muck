# Simple ToDo App API Example

This is a simple example of a complete Flask app hosting a REST API. This example demonstrates the tech stack that 
Flask-Muck sits in and how to set create and register the views.

Below are instructions are running the testing the example.

## Prequisites 

- [Python 3.11](https://www.python.org/downloads/)
- [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)

## Running The App

`pipenv run python3 app.py`

## CURL Commands

### Login
`curl -X POST --location "http://127.0.0.1:5000/api/v1/login"`

### Logout
`curl -X POST --location "http://127.0.0.1:5000/api/v1/logout"`

### Create a ToDo item
```
curl -X POST --location "http://127.0.0.1:5000/api/v1/todos" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"take out garbage again\"
        }"
```

### List all ToDo items (flat)
```
curl -X GET --location "http://127.0.0.1:5000/api/v1/todos" \
    -d "Accept: application/json"
```

### List all ToDo items (paginated)
```
curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?limit=2&offset=1" \
    -d "Accept: application/json"
```

### Get ToDo item
```
curl -X GET --location "http://127.0.0.1:5000/api/v1/todos/1" \
    -d "Accept: application/json"
```

### Update ToDo item
```
curl -X PUT --location "http://127.0.0.1:5000/api/v1/todos/1" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"Updated todo item\"
        }"
```

### Patch ToDo item
```
curl -X PATCH --location "http://127.0.0.1:5000/api/v1/todos/1" \
    -H "Content-Type: application/json" \
    -d "{
            \"text\": \"Updated todo item\"
        }"
```


