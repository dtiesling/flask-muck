from typing import Any, Union

from sqlalchemy.orm import DeclarativeBase  # type: ignore

JsonDict = dict[str, Any]
ResourceId = Union[str, int]
SqlaModelType = type[DeclarativeBase]
SqlaModel = DeclarativeBase
