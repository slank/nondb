from pathlib import Path

from pydantic import BaseModel

from .NoTable import NoTable
from .Storage import Storage


class NoDB:
    def __init__(self, path: str) -> None:
        self.storage = Storage(Path(path))
        self.tables = {}

    def table(self, schema: type[BaseModel], key_expr: str = "id") -> NoTable:
        """Get or create a table for the given schema."""
        table_name = schema.__name__
        if table_name not in self.tables.keys():
            self.tables[table_name] = NoTable(self.storage, schema, key_expr)
        return self.tables[table_name]

    def drop(self, schema: type[BaseModel], raiseOnMissing: bool = False) -> None:
        """Drop the table for the given schema."""
        table_name = schema.__name__
        if table_name in self.tables:
            self.tables[table_name].storage.remove_storage()
            del self.tables[table_name]
        elif raiseOnMissing:
            raise KeyError(f"Table {table_name} does not exist.")
