import tempfile
from pathlib import Path
from shutil import rmtree
from unittest import TestCase

from src.nondb.Storage import Storage, cn


class TestStorage(TestCase):
    def setUp(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_storage"
        self.storage = Storage(self.storage_path)

    def tearDown(self):
        """Clean up after each test."""
        if self.storage_path.exists():
            rmtree(self.storage_path)

    def test_write_and_read(self):
        # Test writing to and then reading from a document.
        self.storage.write("test", "data")
        read_data = self.storage.read("test")
        self.assertEqual(read_data, "data")

    def test_names_and_all(self):
        # Test that names returns correct file paths and all returns document contents.
        self.storage.write("first", "data1")
        self.storage.write("second", "data2")
        names = self.storage.names()
        self.assertEqual(len(names), 2)
        contents = self.storage.all()
        self.assertIn("data1", contents)
        self.assertIn("data2", contents)

    def test_child_storage(self):
        # Test creating a child storage, then writing and reading within it.
        child_storage = self.storage.add_child("child1")
        child_storage.write("child_file", "child_data")
        read_child = child_storage.read("child_file")
        self.assertEqual(read_child, "child_data")
        self.assertTrue(child_storage.path.exists())

    def test_delete(self):
        # Test deleting a document.
        self.storage.write("to_delete", "delete_me")
        file_path = self.storage.path / "to_delete.json"
        self.assertTrue(file_path.exists())
        self.storage.delete("to_delete")
        self.assertFalse(file_path.exists())

    def test_remove_storage(self):
        # Test recursive removal of storage including child directories.
        self.storage.write("file", "value")
        child_storage = self.storage.add_child("sub")
        child_storage.write("child_file", "child_value")
        self.assertTrue(self.storage.path.exists())
        self.assertTrue(child_storage.path.exists())
        self.storage.remove_storage()
        self.assertFalse(self.storage.path.exists())

    def test_cn_with_existing_extension(self):
        # Test that cn returns name unchanged when it already has the correct extension
        result = cn("test.json", "json")
        self.assertEqual(result, "test.json")

        result = cn("file.txt", "txt")
        self.assertEqual(result, "file.txt")

    def test_cn_without_extension(self):
        # Test that cn adds extension when name doesn't have it.
        result = cn("test", "json")
        self.assertEqual(result, "test.json")

    def test_ensure_dir_with_file_path(self):
        # Test that ensure_dir raises NotADirectoryError when path exists but is a file
        # Create a file at the path
        file_path = Path(self.temp_dir) / "not_a_directory.txt"
        file_path.touch()

        with self.assertRaises(NotADirectoryError) as context:
            Storage.ensure_dir(file_path)

        self.assertIn("is not a directory", str(context.exception))
