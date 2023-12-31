# How to Use the REST API

Having created a REST API, it's time to put it to use. This section covers each operation generated by Flask-Muck, complete with example cURL commands and descriptions.

For this example, let's assume we have created a ToDo list application. Below is the API for managing Todo list items.

```python
class TodoApiView(FlaskMuckApiView):
    session = db.session
    api_name = "todos"
    Model = TodoModel
    ResponseSchema = TodoSchema
    CreateSchema = TodoSchema
    PatchSchema = TodoSchema
    UpdateSchema = TodoSchema
    searchable_columns = [TodoModel.text]
```

### Create a Resource

This operation creates a single new resource. The `CreateSchema` validates the request body, and the `ResponseSchema` serializes the newly created resource in the response body.

???+ example
    ```bash title="cURL Command"
    curl -X POST --location "http://127.0.0.1:5000/api/v1/todos" \
        -H "Content-Type: application/json" \
        -d "{
                \"text\": \"Pick up bread and milk.\"
            }"
    ```
    
    ```json title="JSON Response Body"
    {
        "id": 1,
        "text": "Pick up bread and milk.",
        "completed": false
    }
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-201-green)
    

### List All Resources (Flat)

This returns a flat list of all resources. The `ResponseSchema` serializes the resources in the response body.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos" \
        -H "Accept: application/json"
    ```
    
    ```json title="JSON Response Body"
    [
        {
            "id": 1,
            "text": "Pick up bread and milk.",
            "completed": false
        },
        {
            "id": 2,
            "text": "Take out garbage.",
            "completed": false
        }
    ]
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### List All Resources (Paginated)

This returns a paginated set of resources. The `ResponseSchema` serializes the resources in the response body. To trigger a paginated response, provide the `limit` and/or `offset` query string parameters.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?limit=2&offset=1" \
        -H "Accept: application/json"
    ```
    
    ```json title="JSON Response Body"
    {
        "items": [
            {
                "id": 2,
                "text": "Take out garbage.",
                "completed": false
            },
            {
                "id": 3,
                "text": "Paint the fence.",
                "completed": false
            }
        ],
        "limit": 2,
        "offset": 1,
        "total": 2
    }
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### Search All Resources

This operation returns a list of resources matching the provided search query. The search term is matched against `searchable_columns` using an ILIKE query. The `ResponseSchema` serializes the resources in the response body.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?search=garbage" \
        -H "Accept: application/json"
    ```
    
    ```json title="JSON Response Body"
    [
        {
            "id": 2,
            "text": "Take out garbage.",
            "completed": false
        }
    ]
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### Filter All Resources

This returns a list of resources matching the provided filters. The `filters` query string parameter is a JSON-encoded object used to filter the resources. Filtering can be done against any column on the model and supports filtering against relationships using dot notation. Operators are supported using the syntax: `<column>__<operator>` for more complex filtering. A list of available operators is provided in the table below. The `ResponseSchema` serializes the resources in the response body.

| Operator | Description              |
|----------|--------------------------|
| None     | Equals                   |
| `ne`     | Not Equals               |
| `lt`     | Less Than                |
| `lte`    | Less Than or Equal To    |
| `gt`     | Greater Than             |
| `gte`    | Greater Than or Equal To |
| `in`     | In                       |
| `not_in` | Not In                   |

An example of a complex filter using operators and relationships is `filters={"list.priority__gte": 5}`, filtering ToDo items whose related list has a priority greater than or equal to 5.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?filters=%7B%22text%22%3A+%22Take+out+garbage+again%22%7D" \
        -H "Accept: application/json"
    ```
    _query string decodes to `filters={"text": "Take out garbage again"}`_ 
        
    ```json title="JSON Response Body"
    [
        {
            "id": 2,
            "text": "Take out garbage.",
            "completed": false
        }
    ]
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### Sort All Resources

This operation returns a list of resources sorted by the provided column. Use dot notation to sort by a related column and the `asc` or `desc` suffix to specify the sort order. The `ResponseSchema` serializes the resources in the response body. The default sort direction depends on your database. A complex example of sorting by a related column is `sort=list.priority__desc`.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?sort=text__desc" \
        -H "Accept: application/json"
    ``` 
    
    ```json title="JSON Response Body"
    [
        {
            "id": 2,
            "text": "Take out garbage.",
            "completed": false
        },
        {
            "id": 1,
            "text": "Pick up bread and milk.",
            "completed": false
        }
    ]
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

!!! tip
    You can use any combination of search, filter, sort, and pagination query string

 parameters together.

### Fetch a Resource

This returns a single resource by its primary key. The `DetailSchema` serializes the response. If `DetailSchema` does not exist, Flask-Muck falls back to using the `ResponseSchema`.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos/1" \
        -H "Accept: application/json"
    ```

    ```json title="JSON Response Body"
    {
        "id": 1,
        "text": "Pick up bread and milk.",
        "completed": false
    }
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### Update a Resource

This updates a single resource by its primary key. The `UpdateSchema` validates the request body. The update endpoint adheres to PUT semantics, intending to replace the entire resource with the provided data. For partial updates, use the PATCH endpoint. The `ResponseSchema` serializes the response.

???+ example
    ```bash title="cURL Command"
    curl -X PUT --location "http://127.0.0.1:5000/api/v1/todos/1" \
        -H "Content-Type: application/json" \
        -d "{
                \"text\": \"Updated todo item\",
                \"completed\": true 
            }"
    ```

    ```json title="JSON Response Body"
    {
        "id": 1,
        "text": "Updated todo item",
        "completed": true
    }
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### Patch a Resource

This updates a single resource by its primary key. The PATCH endpoint adheres to PATCH semantics, intended for partial updates. If the `PatchSchema` does not exist, Flask-Muck falls back to using the `UpdateSchema`. The schema is initialized with `partial=True` to allow partial updates. The `ResponseSchema` serializes the response.

???+ example
    ```bash title="cURL Command"
    curl -X PATCH --location "http://127.0.0.1:5000/api/v1/todos/1" \
        -H "Content-Type: application/json" \
        -d "{
                \"completed\": true 
            }"
    ```
        
    ```json title="JSON Response Body"
    {
        "id": 1,
        "text": "Pick up bread and milk.",
        "completed": true
    }
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### Delete a Resource

This deletes a single resource by its primary key. The `ResponseSchema` serializes the response. Optionally, the `DeleteSchema` can validate the request body if additional custom logic occurs during a delete operation. If the schema does not exist, the resource is deleted. The response is always empty.

???+ example
    ```bash title="cURL Command"
    curl -X DELETE --location "http://127.0.0.1:5000/api/v1/todos/1"
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-204-green)