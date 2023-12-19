from typing import Any, Union

from marshmallow import Schema
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase  # type: ignore


JsonDict = dict[str, Any]
ResourceId = Union[str, int]
SqlaModelType = type[DeclarativeBase]
SqlaModel = DeclarativeBase
SerializerType = Union[type[Schema], type[BaseModel]]
