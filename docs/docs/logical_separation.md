# Supporting Logical Data Separation (Multi-tenancy)

A common architecture in web applications is multi-tenancy through logical separation. The FlaskMuckApiView includes 
a method, `get_base_query_kwargs`, that can be overridden to generate a set of arguments that will be passed to all queries. 
This allows you to filter resources to only those that should be available to a user and prevent resources from leaking 
between tenants. 

The `get_base_query_kwargs` should return a dictionary of keyword arguments. Those kwargs will
be applied to CRUD operations at the SqlAlchemy level. For example the GET /<resource\>/ endpoint will generate 
the query `Model.query.filter_by(**get_base_query_kwargs()).all()` instead of `Model.query.all()`. The keyword arguments
will also be applied when creating or updating a model.

```python
from flask_login import current_user
from flask_muck import FlaskMuckApiView


class MyApiView(FlaskMuckApiView):
    ...
    
    def get_base_query_kwargs(self):
        return {"organization_id": current_user.organization_id}#(1)!
```

1. Assumes the resource has the `organization_id` column and it will be filtered by the current user's organization id.


## Example Usage

!!! note
    This example expands on the example in the [quickstart](quickstart.md). If you have not read through the
    [quickstart](quickstart.md) this will make more sense if you do.

Assume we have a customer support platform where each user belongs to a single organization. Nearly all resources in the 
application are associated with an organization and when the user accesses them they should only see resources in the
same organization as them.

The SqlAlchemy models will look something like this.

```python title="myapp/models.py"
from myapp import db

class Organization(db.model):
    """Customer support organization that contains users and support tickets."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    
class User(db.Model):
    """User that is responsible for responding to support tickets in their organization."""
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
    """A newsfeed item with information about the platform (i.e. release notes). Available to all users regardless of 
    organization.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String, nullable=False)
    
```

Since we'll have views that need to be filtered by organization and others that do not two base classes will be created.

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

1. Flask-Login is used to enforce user authentication by adding the login_required decorator.
2. Flask-Login is used to give the views access to the current user and therefore the current organization to filter by.

Now all we need to do is choose the correct base view class based on whether the resource should be filtered by the current 
user's organization.

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

1. Remainder of the SupportTicketsApiView configuration goes here.
2. Remainder of the NewsfeedItemApiview configuration goes here.


