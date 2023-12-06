# Supporting Logical Data Separation (Multi-tenancy)

A common architecture in web applications is multi-tenancy through logical separation. `FlaskMuckApiView` includes a method, `get_base_query_kwargs`, which can be overridden to generate a set of arguments passed to all queries. This method enables filtering of resources to those available to a user, preventing resource leakage between tenants.

The `get_base_query_kwargs` should return a dictionary of keyword arguments. These kwargs are applied to CRUD operations at the SqlAlchemy level. For example, the GET /<resource\>/ endpoint will generate the query `Model.query.filter_by(**get_base_query_kwargs()).all()` instead of `Model.query.all()`. The keyword arguments are also applied when creating or updating a model.

```python
from flask_login import current_user
from flask_muck import FlaskMuckApiView

class MyApiView(FlaskMuckApiView):
    ...
    
    def get_base_query_kwargs(self):
        return {"organization_id": current_user.organization_id}#(1)!
```

1. Assumes the resource has an `organization_id` column and it will be filtered by the current user's organization ID.

## Example Usage

!!! note
    This example builds upon the [quickstart](quickstart.md) example. It will be more comprehensible if you have read through the [quickstart](quickstart.md).

Imagine a customer support platform where each user belongs to a single organization. Nearly all resources in the application are associated with an organization, and users should only access resources within their organization.

The SqlAlchemy models might look like this:

```python title="myapp/models.py"
from myapp import db

class Organization(db.Model):
    """Customer support organization containing users and support tickets."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    
class User(db.Model):
    """User responsible for responding to support tickets in their organization."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, nullable=False)
    organization_id = db.Column(db.ForeignKey(Organization.id))
    organization = db.relationship(Organization)

class SupportTicket(db.Model):
    """Support ticket submitted for an organization."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_number = db.Column(db.Integer, nullable=False)
    organization_id = db.Column(db.ForeignKey(Organization.id))
    organization = db.relationship(Organization)

class NewsfeedItem(db.Model):
    """Newsfeed item with platform information (e.g., release notes), available to all users regardless of organization."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String, nullable=False)
```

Since we have views that need to be filtered by organization and others that do not, two base classes will be created:

```python title="myapp/baseviews.py"
from flask_login import login_required, current_user
from flask_muck import FlaskMuckApiView
from myapp import db

class BaseApiView(FlaskMuckApiView):
    session = db.session
    decorators = [login_required]#(1)!

class OrganizationResourceApiView(BaseApiView):
    def get_base_query_kwargs(self):
        return {"organization_id": current_user.organization_id}#(2)!
```

1. Flask-Login enforces user authentication by adding the `login_required` decorator.
2. Flask-Login provides access to the current user, allowing views to filter by the current organization.

Now, simply choose the appropriate base view class based on whether the resource should be filtered by the current user's organization:

```python title="views.py"
from myapp.baseviews import BaseApiView, OrganizationResourceApiView
from myapp.models import SupportTicket, NewsfeedItem

class SupportTicketsApiView(OrganizationResourceApiView):
    Model = SupportTicket
    ...#(1)!

class NewsfeedItemApiview(BaseApiView):
    Model = NewsfeedItem
    ...#(2)!
```

1. The remainder of the `SupportTicketsApiView` configuration goes here.
2. The remainder of the `NewsfeedItemApiview` configuration goes here.