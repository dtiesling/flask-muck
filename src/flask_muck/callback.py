from abc import ABC, abstractmethod
from enum import Enum

from flask_muck.types import SqlaModel, JsonDict


class CallbackType(Enum):
    pre = "pre"
    post = "post"


class FlaskMuckCallback(ABC):
    """The base class for implementing Flask Muck callbacks."""

    def __init__(self, resource: SqlaModel, kwargs: JsonDict):
        self.resource = resource
        self.kwargs = kwargs

    @abstractmethod
    def execute(self) -> None:
        """This method executes the desired callback functionality. It must be overridden in concrete subclasses."""
        ...
