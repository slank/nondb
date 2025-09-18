from functools import lru_cache
from pathlib import Path
from shutil import rmtree


def cn(name: str, file_ext: str) -> str:
    """Construct a canonical name with the given file extension."""
    name = str(name)
    if name.endswith(f".{file_ext}"):
        return name
    return f"{name}.{file_ext}"


class Storage:
    """A simple file-based storage system."""

    def __init__(self, path: Path, file_ext: str = "json") -> None:
        self.path = self.ensure_dir(path)
        self.file_ext = file_ext
        self.children: dict[str, Storage] = {}

    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """Ensure the given path is a directory, creating it if necessary."""
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            return path
        raise NotADirectoryError(f"{path} is not a directory")

    # Document management

    def names(self) -> list[Path]:
        """List all documents."""
        return list(self.path.glob(f"*.{self.file_ext}"))

    def read(self, name: str) -> str:
        """Read a document."""
        path = self.path / cn(name, self.file_ext)
        with open(path, "r") as f:
            return f.read()

    def all(self) -> list[str]:  # FIXME: make this a generator
        """Read all documents."""
        items = []
        for path in self.names():
            with open(path, "r") as f:
                items.append(f.read())
        return items

    def write(self, name: str, data: str) -> None:
        """Write a document."""
        path = self.path / cn(name, self.file_ext)
        with open(path, "w") as f:
            f.write(data)

    def delete(self, name: str) -> None:
        """Delete a document."""
        path = self.path / cn(name, self.file_ext)
        if path.exists():
            path.unlink()

    # Storage management

    def remove_storage(self) -> None:
        """Remove the entire storage directory and its contents."""
        for child in self.children.values():
            child.remove_storage()
        self.children = {}
        rmtree(self.path)

    def add_child(self, name: str) -> "Storage":
        """Get or create a child storage."""
        if name not in self.children.keys():
            self.children[name] = Storage(self.path / name)
        return self.children[name]
