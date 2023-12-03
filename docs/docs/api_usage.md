# How to use the REST API

Now that a REST API has been created, it's time to use it. This section will cover each of the operations Flask-Muck
generates with example curl commands and descriptions.

For the purposes of this example, assume we have created a ToDo list application. The API for working with Todo list items 
is below.

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


### Create a resource

Creates of a single new resource. The `CreateSchema` is used to validate the request body and the `ResponseSchema`
is used to serialize the newly created resource in the response body.

??? example
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
    

### List all resources (flat)

Returns a flat list of all resources. The `ResponseSchema` is used to serialize the resources in the response body.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos" \
        -d "Accept: application/json"
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

### List all resources (paginated)

Returns a paginated set of resources. The `ResponseSchema` is used to serialize the resources in the response body. To 
trigger the paginated response, the `limit` and/or `offset` querystring parameters must be provided.

???+ example
    ```bash title="cURL Command"
    cURL -X GET --location "http://127.0.0.1:5000/api/v1/todos?limit=2&offset=1" \
        -d "Accept: application/json"
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

### Search all resources

Returns a list of resources that match the provided search query. The search term is matched against the `searchable_columns`
using an ILIKE query. The `ResponseSchema` is used to serialize the resources in the response body.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?search=garbage" \
        -d "Accept: application/json"
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

### Filter all resources

Returns a list of resources that match the provided filters. The `filters` querystring parameter is a JSON encoded object
that is used to filter the resources. Filtering can be done against any column on the model and also supports filtering
against relationships using dot notation. Operators are supported using the following syntax: `<column>__<operator>` to do 
more complex filtering. A list of available operators is in the table directly below. The `ResponseSchema` is used to
serialize the resources in the response body.

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

An example of a complex filter using operators and relationships is `filters={"list.priority__gte": 5}`. This would filter the
ToDo items whose related list has a priority greater than or equal to 5.

??? example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?filters=%7B%22text%22%3A+%22Take+out+garbage+again%22%7D" \
        -d "Accept: application/json"
    ```
    _querystring urldecodes to `filters={"text": "Take out garbage again"}`_ 
        
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

### Sort all resources

Return a list of resources sorted by the provided column. Using dot notation you can sort by a related column. 
Use the `asc` or `desc` operator suffix to specify the sort order. The `ResponseSchema` is used to serialize the 
resources in the response body. Default sort direction is dependent on your datbabase.A complex example of sorting by a 
related column is `sort=list.priority__desc`.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos?sort=text__desc" \
        -d "Accept: application/json"
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
    Any combination of the search, filter, sort, and pagination querystring parameters can be used together.

### Fetch a resource


Return a single resource by its primary key. The `DetailSchema` is used to serialize the response. If `DetailSchema` 
does not exist Flask-Muck falls back to using the `ResponseSchema`.

???+ example
    ```bash title="cURL Command"
    curl -X GET --location "http://127.0.0.1:5000/api/v1/todos/1" \
        -d "Accept: application/json"
    ```

    ```json title="JSON Response Body"
    {
        "id": 1,
        "text": "Pick up bread and milk.",
        "completed": false
    }
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-200-green)

### Update a resource

Update a single resource by its primary key. The `UpdateSchema` is used to validate the request body. The update endpoint 
adheres to PUT semantics and is intended to replace the entire resource with the provided data. 
If you want to do a partial update use the PATCH endpoint. The `ResponseSchema` is used to serialize the response.

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

### Patch a resource

Update a single resource by its primary key. The patch endpoint adheres to PATCH semantics and is intended to partially 
update the resource with the provided data. If you want to do a full update use the PUT endpoint. The `PatchSchema` is
used to validate the request body, if the schema does not exist Flask-Muck falls back to using the `UpdateSchema`. 
Regardless of which schema is used the schema is initialized with `partial=True` which allows for partial updates. The
`ResponseSchema` is used to serialize the response.

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

### Delete a resource

Delete a single resource by its primary key. The `ResponseSchema` is used to serialize the response. Optionally, the
`DeleteSchema` can be used to validate the request body in the case that additional custom logic occurs during a delete
operation. If the schema does not exist the resource is deleted. The response is always empty.

???+ example
    ```title="cURL Command"
    curl -X DELETE --location "http://127.0.0.1:5000/api/v1/todos/1"
    ```
    ![Static Badge](https://img.shields.io/badge/Status_Code-204-green)