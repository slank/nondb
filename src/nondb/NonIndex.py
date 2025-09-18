import os
from abc import ABC, abstractmethod
from shutil import rmtree

import jmespath
from pydantic import BaseModel

from .Storage import Storage


class IIndexed[T](ABC):
    @abstractmethod
    def key_for(self, record: T) -> str: ...

    @property
    @abstractmethod
    def schema(self) -> type[T]: ...

    @property
    @abstractmethod
    def storage(self) -> Storage: ...

    @abstractmethod
    def all(self) -> list[T]: ...


class NonIndex[T: BaseModel]:
    def __init__(self, table: IIndexed, schema: type[T], index_expr: str) -> None:
        self.table = table
        self.schema = schema
        self.storage = table.storage.add_child(f"_index@{index_expr}")
        self.index_expr = jmespath.compile(index_expr)

    # internal symlink management methods

    def _link(self, index_key: str, primary_key: str) -> None:
        index_key_storage = self.storage.add_child(str(index_key))
        os.symlink(
            self.table.storage.path / f"{primary_key}.json",
            index_key_storage.path / f"{primary_key}.json",
        )

    def _unlink(self, index_key: str, primary_key: str) -> None:
        index_key_storage = self.storage.add_child(str(index_key))
        symlink_path = index_key_storage.path / f"{primary_key}.json"
        if symlink_path.exists() and symlink_path.is_symlink():
            symlink_path.unlink()
            # If the index key directory is empty after removing the symlink, remove it
            if not any(index_key_storage.path.iterdir()):
                index_key_storage.path.rmdir()

    def _unlinkAll(self, primary_key: str) -> None:
        """Remove all symlinks for the given primary key across all index keys."""
        for index_key_dir in self.storage.path.iterdir():
            if index_key_dir.is_dir():
                self._unlink(index_key_dir.name, primary_key)

    # record management methods

    def key_for(self, record: T) -> str:
        """Get the index key for the given record."""
        return self.index_expr.search(record.model_dump())

    def put(self, record: T) -> None:
        """Update the index for the given record."""
        primary_key = self.table.key_for(record)
        self._unlinkAll(primary_key)  # Clean up existing symlinks
        index_key = self.key_for(record)
        self._link(index_key, primary_key)

    def get(self, index_key: str) -> list[T]:
        """Get records matching the given index key."""
        items = []
        for item in (self.storage.path / str(index_key)).glob("*.json"):
            with open(item) as f:
                items.append(self.schema.model_validate_json(f.read()))
        return items

    def delete(self, record: T) -> None:
        """Remove the given record from the index."""
        primary_key = self.table.key_for(record)
        index_key = self.key_for(record)
        self._unlink(index_key, primary_key)

    # index management utilities

    def remove_index(self) -> None:
        """Remove the entire index."""
        if self.storage.path.exists():
            rmtree(self.storage.path)

    def rebuild_index(self) -> None:
        """Rebuild the index from the table."""
        self.remove_index()
        Storage.ensure_dir(self.storage.path)
        for record in self.table.all():
            self.put(record)

    def vacuum_index(self) -> None:
        """Remove broken symlinks and empty directories."""
        for index_key_dir in self.storage.path.iterdir():
            if index_key_dir.is_dir():
                for symlink in index_key_dir.iterdir():
                    if symlink.is_symlink() and not symlink.exists():
                        symlink.unlink()
                # If the directory is empty after removing broken symlinks, remove it
                if not any(index_key_dir.iterdir()):
                    index_key_dir.rmdir()
