import tempfile
from pathlib import Path
from shutil import rmtree
from unittest import TestCase

from pydantic import BaseModel

from src.nondb.NonIndex import NonIndex
from src.nondb.NonTable import NonTable
from src.nondb.Storage import Storage


class TestModel(BaseModel):
    id: int
    name: str
    category: str


class TestNoIndex(TestCase):
    def setUp(self):
        """Set up a temporary directory and test data for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_storage"
        self.storage = Storage(self.storage_path)
        self.table = NonTable(self.storage, TestModel, "id")

        # Add test records
        self.record1 = TestModel(id=1, name="Alice", category="admin")
        self.record2 = TestModel(id=2, name="Bob", category="user")
        self.record3 = TestModel(id=3, name="Charlie", category="admin")

        self.table.save(self.record1)
        self.table.save(self.record2)
        self.table.save(self.record3)

        self.index = NonIndex(self.table, TestModel, "category")

    def tearDown(self):
        """Clean up after each test."""
        if self.storage_path.exists():
            rmtree(self.storage_path)

    def test_init(self):
        """Test NoIndex initialization."""
        index = NonIndex(self.table, TestModel, "category")

        self.assertEqual(index.table, self.table)
        self.assertEqual(index.schema, TestModel)
        self.assertEqual(index.index_expr.expression, "category")

        # Check storage path
        expected_path = self.table.storage.path / "_index@category"
        self.assertEqual(index.storage.path, expected_path)

    def test_update_creates_symlink(self):
        """Test that update creates proper symlinks."""
        self.index.put(self.record1)

        # Check symlink exists
        admin_dir = self.index.storage.path / "admin"
        symlink_path = admin_dir / "1.json"

        self.assertTrue(symlink_path.exists())
        self.assertTrue(symlink_path.is_symlink())

    def test_update_removes_old_symlinks(self):
        """Test that update removes old symlinks when record changes."""
        self.index.put(self.record1)

        # Verify initial symlink
        old_symlink = self.index.storage.path / "admin" / "1.json"
        self.assertTrue(old_symlink.exists())

        # Update record with different category
        updated_record = TestModel(id=1, name="Alice", category="user")
        self.index.put(updated_record)

        # Old symlink should be removed, new one created
        self.assertFalse(old_symlink.exists())
        new_symlink = self.index.storage.path / "user" / "1.json"
        self.assertTrue(new_symlink.exists())

    def test_rebuild_index(self):
        """Test rebuilding the entire index."""
        self.index.rebuild_index()

        # Check that symlinks were created for all records
        admin_dir = self.index.storage.path / "admin"
        user_dir = self.index.storage.path / "user"

        self.assertTrue(admin_dir.exists())
        self.assertTrue(user_dir.exists())

        # Admin should have 2 records (Alice and Charlie)
        admin_files = list(admin_dir.glob("*.json"))
        self.assertEqual(len(admin_files), 2)

        # User should have 1 record (Bob)
        user_files = list(user_dir.glob("*.json"))
        self.assertEqual(len(user_files), 1)

    def test_get_records_by_index_key(self):
        """Test retrieving records by index key."""
        self.index.rebuild_index()

        # Get admin records
        admin_records = self.index.get("admin")
        self.assertEqual(len(admin_records), 2)
        admin_ids = {record.id for record in admin_records}
        self.assertEqual(admin_ids, {1, 3})

        # Get user records
        user_records = self.index.get("user")
        self.assertEqual(len(user_records), 1)
        self.assertEqual(user_records[0].id, 2)

    def test_get_nonexistent_key(self):
        """Test getting records for non-existent key."""
        self.index.rebuild_index()
        empty_records = self.index.get("nonexistent")
        self.assertEqual(empty_records, [])

    def test_remove_record(self):
        """Test removing a record from the index."""
        self.index.rebuild_index()

        # Verify record exists
        admin_records = self.index.get("admin")
        self.assertEqual(len(admin_records), 2)

        # Remove one record
        self.index.delete(self.record1)

        # Verify record was removed
        admin_records = self.index.get("admin")
        self.assertEqual(len(admin_records), 1)
        self.assertEqual(admin_records[0].id, 3)

    def test_vacuum_removes_broken_symlinks(self):
        """Test that vacuum removes broken symlinks and empty directories."""
        self.index.rebuild_index()

        # Manually break a symlink by deleting the target file
        target_file = self.table.storage.path / "1.json"
        target_file.unlink()

        # Run vacuum
        self.index.vacuum_index()

        # Broken symlink should be removed
        broken_symlink = self.index.storage.path / "admin" / "1.json"
        self.assertFalse(broken_symlink.exists())

        # Directory should still exist since it has other files
        admin_dir = self.index.storage.path / "admin"
        self.assertTrue(admin_dir.exists())

    def test_vacuum_removes_empty_directories(self):
        """Test that vacuum removes empty directories after cleaning broken symlinks."""
        # Create index with single record
        single_index = NonIndex(self.table, TestModel, "name")
        single_index.put(self.record1)

        # Break the symlink
        target_file = self.table.storage.path / "1.json"
        target_file.unlink()

        # Run vacuum
        single_index.vacuum_index()

        # Empty directory should be removed
        alice_dir = single_index.storage.path / "Alice"
        self.assertFalse(alice_dir.exists())

    def test_key_for(self):
        """Test key_for method extracts the correct value from records."""
        # Test with existing records
        self.assertEqual(self.index.key_for(self.record1), "admin")
        self.assertEqual(self.index.key_for(self.record2), "user")
        self.assertEqual(self.index.key_for(self.record3), "admin")

        # Test with a new record
        new_record = TestModel(id=4, name="David", category="guest")
        self.assertEqual(self.index.key_for(new_record), "guest")

    def test_key_for_with_different_index_expression(self):
        """Test key_for with different index expressions."""
        # Create index on 'name' field
        name_index = NonIndex(self.table, TestModel, "name")
        self.assertEqual(name_index.key_for(self.record1), "Alice")
        self.assertEqual(name_index.key_for(self.record2), "Bob")

        # Create index on 'id' field
        id_index = NonIndex(self.table, TestModel, "id")
        self.assertEqual(id_index.key_for(self.record1), 1)
        self.assertEqual(id_index.key_for(self.record2), 2)

    def test_remove_index(self):
        """Test removing the entire index."""
        # Build the index first
        self.index.rebuild_index()

        # Verify index exists and has content
        self.assertTrue(self.index.storage.path.exists())
        admin_dir = self.index.storage.path / "admin"
        user_dir = self.index.storage.path / "user"
        self.assertTrue(admin_dir.exists())
        self.assertTrue(user_dir.exists())

        # Remove the index
        self.index.remove_index()

        # Verify index directory is completely removed
        self.assertFalse(self.index.storage.path.exists())

    def test_remove_index_when_empty(self):
        """Test removing index when it's empty."""
        # Create empty index storage directory
        self.index.storage.path.mkdir(parents=True, exist_ok=True)
        self.assertTrue(self.index.storage.path.exists())

        # Remove the index
        self.index.remove_index()

        # Verify directory is removed
        self.assertFalse(self.index.storage.path.exists())

    def test_remove_index_when_nonexistent(self):
        """Test removing index when it doesn't exist."""
        # Ensure index doesn't exist
        if self.index.storage.path.exists():
            rmtree(self.index.storage.path)
        self.assertFalse(self.index.storage.path.exists())

        # Should not raise an error when removing non-existent index
        try:
            self.index.remove_index()
        except FileNotFoundError:
            self.fail("remove_index() raised FileNotFoundError unexpectedly")
