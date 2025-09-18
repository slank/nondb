import jmespath
from pydantic import BaseModel

from .NonIndex import IIndexed, NonIndex
from .Storage import Storage


class NonTable[T: BaseModel](IIndexed[T]):
    def __init__(self, db_storage: Storage, schema: type[T], key_expr: str):
        self.db_storage = db_storage
        self._schema = schema
        self._jmespath = jmespath.compile(key_expr)
        self._indices: dict[str, NonIndex] = {}

    @property
    def schema(self) -> type[T]:
        return self._schema

    @property
    def key_expr(self) -> str:
        return self._jmespath.expression

    @key_expr.setter
    def _key_expr(self, expr: str) -> None:
        self._jmespath = jmespath.compile(expr)

    @property
    def storage(self) -> Storage:
        return self.db_storage.add_child(self.schema.__name__)

    def key_for(self, record: T) -> str:
        return self._jmespath.search(record.model_dump())

    def fetch(self, key: str) -> T:
        return self.schema.model_validate_json(self.storage.read(key))

    def all(self) -> list[T]:
        return [self.schema.model_validate_json(item) for item in self.storage.all()]

    def keys(self) -> list[str]:
        return [file.stem for file in self.storage.names()]

    def save(self, record: T) -> None:
        key = self.key_for(record)
        self.storage.write(str(key), record.model_dump_json())
        for index in self._indices.values():
            index.put(record)

    def delete(self, record: T) -> None:
        self.storage.delete(self.key_for(record))
        for index in self._indices.values():
            index.delete(record)

    def index(self, index_expr: str) -> "NonIndex[T]":
        if index_expr not in self._indices:
            self._indices[index_expr] = NonIndex(self, self.schema, index_expr)
        return self._indices[index_expr]

    def stat(self) -> dict:
        return {
            "path": str(self.storage.path),
            "record_type": self.schema.__name__,
            "key_expr": self.key_expr,
            "num_records": len(self.keys()),
            "indices": list(self._indices.keys()),
        }
