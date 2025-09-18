import tempfile
from pathlib import Path
from shutil import rmtree
from unittest import TestCase

from pydantic import BaseModel

from src.nondb.NoTable import NoTable
from src.nondb.Storage import Storage


class TestModel(BaseModel):
    id: int
    name: str
    email: str


class PersonModel(BaseModel):
    id: str
    first_name: str
    last_name: str
    age: int


class TestNoTable(TestCase):
    def setUp(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_storage"
        self.storage = Storage(self.storage_path)
        self.table = NoTable(self.storage, TestModel, "id")

    def tearDown(self):
        """Clean up after each test."""
        if self.storage_path.exists():
            rmtree(self.storage_path)

    def test_init(self):
        """Test NoTable initialization."""
        self.assertEqual(self.table.db_storage, self.storage)
        self.assertEqual(self.table.schema, TestModel)
        self.assertEqual(self.table.key_expr, "id")
        self.assertEqual(self.table._indices, {})

    def test_key_expr_property(self):
        """Test key_expr getter and setter."""
        self.assertEqual(self.table.key_expr, "id")

        # Test with different expression
        table2 = NoTable(self.storage, TestModel, "name")
        self.assertEqual(table2.key_expr, "name")

    def test_storage_property(self):
        """Test storage property returns child storage with schema name."""
        expected_path = self.storage_path / "TestModel"
        self.assertEqual(str(self.table.storage.path), str(expected_path))

    def test_key_for(self):
        """Test _key_for method extracts correct key from record."""
        record = TestModel(id=123, name="John Doe", email="john@example.com")
        key = self.table.key_for(record)
        self.assertEqual(key, 123)

        # Test with string key
        person_table = NoTable(self.storage, PersonModel, "id")
        person_record = PersonModel(
            id="abc123", first_name="Jane", last_name="Smith", age=30
        )
        person_key = person_table.key_for(person_record)
        self.assertEqual(person_key, "abc123")

        # Test with nested key expression
        nested_table = NoTable(self.storage, PersonModel, "first_name")
        nested_key = nested_table.key_for(person_record)
        self.assertEqual(nested_key, "Jane")

    def test_save_and_fetch(self):
        """Test saving and fetching records."""
        record = TestModel(id=123, name="John Doe", email="john@example.com")

        # Save the record
        self.table.save(record)

        # Check the file was created
        expected_file = self.table.storage.path / "123.json"
        self.assertTrue(expected_file.exists())

        # Fetch the record
        fetched_record = self.table.fetch("123")
        self.assertEqual(fetched_record.id, 123)
        self.assertEqual(fetched_record.name, "John Doe")
        self.assertEqual(fetched_record.email, "john@example.com")

    def test_fetch_nonexistent_record(self):
        """Test fetching a non-existent record raises appropriate error."""
        with self.assertRaises(FileNotFoundError):
            self.table.fetch("nonexistent")

    def test_all(self):
        """Test retrieving all records from table."""
        # Initially empty
        all_records = self.table.all()
        self.assertEqual(len(all_records), 0)

        # Add some records
        record1 = TestModel(id=1, name="Alice", email="alice@example.com")
        record2 = TestModel(id=2, name="Bob", email="bob@example.com")
        record3 = TestModel(id=3, name="Charlie", email="charlie@example.com")

        self.table.save(record1)
        self.table.save(record2)
        self.table.save(record3)

        # Fetch all records
        all_records = self.table.all()
        self.assertEqual(len(all_records), 3)

        # Verify all records are present (order might vary)
        ids = {record.id for record in all_records}
        self.assertEqual(ids, {1, 2, 3})

    def test_keys(self):
        """Test retrieving all keys from table."""
        # Initially empty
        keys = self.table.keys()
        self.assertEqual(len(keys), 0)

        # Add some records
        record1 = TestModel(id=100, name="Alice", email="alice@example.com")
        record2 = TestModel(id=200, name="Bob", email="bob@example.com")

        self.table.save(record1)
        self.table.save(record2)

        # Get keys
        keys = self.table.keys()
        self.assertEqual(set(keys), {"100", "200"})

    def test_delete(self):
        """Test deleting records."""
        record = TestModel(id=456, name="Test User", email="test@example.com")

        # Save and verify it exists
        self.table.save(record)
        self.assertEqual(len(self.table.keys()), 1)

        # Delete the record
        self.table.delete(record)

        # Verify it's gone
        self.assertEqual(len(self.table.keys()), 0)
        expected_file = self.table.storage.path / "456.json"
        self.assertFalse(expected_file.exists())

    def test_delete_nonexistent_record(self):
        """Test deleting a non-existent record doesn't raise error."""
        record = TestModel(id=456, name="Test User", email="test@example.com")
        # Should not raise an error
        self.table.delete(record)

    def test_index_creation(self):
        """Test creating and using indices."""
        # Create an index on the 'name' field
        name_index = self.table.index("name")

        # Verify index is stored in _indices
        self.assertIn("name", self.table._indices)
        self.assertEqual(self.table._indices["name"], name_index)

        # Verify same index is returned for subsequent calls
        same_index = self.table.index("name")
        self.assertIs(name_index, same_index)

    def test_index_with_records(self):
        """Test index functionality with actual records."""
        # Add some records
        record1 = TestModel(id=1, name="Alice", email="alice@example.com")
        record2 = TestModel(id=2, name="Bob", email="bob@example.com")

        # Create index before saving (should handle updates)
        name_index = self.table.index("name")

        self.table.save(record1)
        self.table.save(record2)

        # Index should have been updated with the records
        self.assertEqual(len(self.table._indices), 1)

    def test_stat(self):
        """Test stat method returns correct information."""
        # Add some records
        record1 = TestModel(id=1, name="Alice", email="alice@example.com")
        record2 = TestModel(id=2, name="Bob", email="bob@example.com")

        self.table.save(record1)
        self.table.save(record2)

        # Create an index
        self.table.index("name")
        self.table.index("email")

        # Get stats
        stats = self.table.stat()

        self.assertIn("path", stats)
        self.assertEqual(stats["record_type"], "TestModel")
        self.assertEqual(stats["key_expr"], "id")
        self.assertEqual(stats["num_records"], 2)
        self.assertEqual(set(stats["indices"]), {"name", "email"})

    def test_save_updates_indices(self):
        """Test that saving records updates all indices."""
        # Create multiple indices
        name_index = self.table.index("name")
        email_index = self.table.index("email")

        record = TestModel(id=1, name="Alice", email="alice@example.com")

        # Save record - should update all indices
        self.table.save(record)

        # Verify indices were updated (this tests the integration)
        self.assertEqual(len(self.table._indices), 2)

    def test_delete_removes_from_indices(self):
        """Test that deleting records removes them from all indices."""
        # Create indices
        name_index = self.table.index("name")
        email_index = self.table.index("email")

        record = TestModel(id=1, name="Alice", email="alice@example.com")
        self.table.save(record)

        # Delete record - should remove from all indices
        self.table.delete(record)

        # Verify record is gone
        self.assertEqual(len(self.table.keys()), 0)

    def test_different_key_expressions(self):
        """Test NoTable with different key expressions."""
        # Test with string key
        person_table = NoTable(self.storage, PersonModel, "id")
        person = PersonModel(id="person123", first_name="John", last_name="Doe", age=25)

        person_table.save(person)
        fetched_person = person_table.fetch("person123")
        self.assertEqual(fetched_person.id, "person123")

        # Test with different field as key
        name_table = NoTable(self.storage, PersonModel, "first_name")
        name_table.save(person)
        fetched_by_name = name_table.fetch("John")
        self.assertEqual(fetched_by_name.first_name, "John")

    def test_save_overwrites_existing_record(self):
        """Test that saving with same key overwrites existing record."""
        record1 = TestModel(id=1, name="Alice", email="alice@example.com")
        record2 = TestModel(id=1, name="Alice Updated", email="alice.new@example.com")

        # Save first record
        self.table.save(record1)
        self.assertEqual(len(self.table.keys()), 1)

        # Save second record with same key
        self.table.save(record2)
        self.assertEqual(len(self.table.keys()), 1)  # Still only one record

        # Verify the record was updated
        fetched = self.table.fetch("1")
        self.assertEqual(fetched.name, "Alice Updated")
        self.assertEqual(fetched.email, "alice.new@example.com")
