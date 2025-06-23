from typing import Any, Union

from marshmallow import Schema
from pydantic import BaseModel

try:
    # SQLAlchemy 2.x compatibility
    from sqlalchemy.orm import DeclarativeBase  # type: ignore
except ImportError:
    # SQLAlchemy 1.4.x compatibility
    from sqlalchemy.orm import declarative_base  # type: ignore

    DeclarativeBase = declarative_base()


JsonDict = dict[str, Any]
ResourceId = Union[str, int]
SqlaModelType = type[DeclarativeBase]
SqlaModel = DeclarativeBase
SerializerType = Union[type[Schema], type[BaseModel]]
