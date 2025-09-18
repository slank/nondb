import tempfile
from pathlib import Path
from shutil import rmtree
from unittest import TestCase

from pydantic import BaseModel

from src.nondb.NoDB import NoDB
from src.nondb.NoTable import NoTable


class TestModel(BaseModel):
    id: int
    name: str
    email: str


class AnotherTestModel(BaseModel):
    id: str
    value: float


class TestNoDB(TestCase):
    def setUp(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_db"
        self.db = NoDB(str(self.db_path))

    def tearDown(self):
        """Clean up after each test."""
        if self.db_path.exists():
            rmtree(self.db_path)

    def test_init(self):
        """Test NoDB initialization."""
        # Test that the database is initialized with correct path
        self.assertEqual(str(self.db.storage.path), str(self.db_path))
        self.assertEqual(self.db.tables, {})

        # Test with different path
        other_path = Path(self.temp_dir) / "other_db"
        other_db = NoDB(str(other_path))
        self.assertEqual(str(other_db.storage.path), str(other_path))

    def test_table_creation(self):
        """Test creating tables with different schemas."""
        # Test creating a table with default key expression
        table = self.db.table(TestModel)

        self.assertIsInstance(table, NoTable)
        self.assertEqual(table.schema, TestModel)
        self.assertEqual(table.key_expr, "id")
        self.assertIn("TestModel", self.db.tables)
        self.assertEqual(self.db.tables["TestModel"], table)

    def test_table_with_custom_key_expr(self):
        """Test creating a table with custom key expression."""
        table = self.db.table(TestModel, "email")

        self.assertEqual(table.key_expr, "email")

    def test_table_reuse(self):
        """Test that calling table() multiple times returns the same instance."""
        table1 = self.db.table(TestModel)
        table2 = self.db.table(TestModel)

        self.assertIs(table1, table2)
        self.assertEqual(len(self.db.tables), 1)

    def test_multiple_tables(self):
        """Test creating multiple tables with different schemas."""
        table1 = self.db.table(TestModel)
        table2 = self.db.table(AnotherTestModel)

        self.assertNotEqual(table1, table2)
        self.assertEqual(len(self.db.tables), 2)
        self.assertIn("TestModel", self.db.tables)
        self.assertIn("AnotherTestModel", self.db.tables)

    def test_table_name_based_on_schema(self):
        """Test that table names are based on schema class names."""
        table = self.db.table(TestModel)
        self.assertIn("TestModel", self.db.tables)

        table2 = self.db.table(AnotherTestModel)
        self.assertIn("AnotherTestModel", self.db.tables)

    def test_drop_existing_table(self):
        """Test dropping an existing table."""
        # Create and populate a table
        table = self.db.table(TestModel)
        test_record = TestModel(id=1, name="John", email="john@example.com")
        table.save(test_record)

        # Verify table exists and has data
        self.assertIn("TestModel", self.db.tables)
        self.assertEqual(len(table.keys()), 1)

        # Drop the table
        self.db.drop(TestModel)

        # Verify table is removed
        self.assertNotIn("TestModel", self.db.tables)

        # Verify storage directory is removed
        table_storage_path = self.db.storage.add_child("TestModel").path
        self.assertFalse(table_storage_path.exists())

    def test_drop_nonexistent_table_default(self):
        """Test dropping a table that doesn't exist (default behavior)."""
        # Should not raise an exception
        self.db.drop(TestModel)
        self.assertEqual(len(self.db.tables), 0)

    def test_drop_nonexistent_table_raise_on_missing(self):
        """Test dropping a table that doesn't exist with raiseOnMissing=True."""
        with self.assertRaises(KeyError) as context:
            self.db.drop(TestModel, raiseOnMissing=True)

        self.assertIn("Table TestModel does not exist", str(context.exception))

    def test_drop_multiple_tables(self):
        """Test dropping multiple tables."""
        # Create multiple tables
        table1 = self.db.table(TestModel)
        table2 = self.db.table(AnotherTestModel)

        # Add data to both
        test_record1 = TestModel(id=1, name="John", email="john@example.com")
        test_record2 = AnotherTestModel(id="test", value=42.0)
        table1.save(test_record1)
        table2.save(test_record2)

        self.assertEqual(len(self.db.tables), 2)

        # Drop first table
        self.db.drop(TestModel)
        self.assertEqual(len(self.db.tables), 1)
        self.assertNotIn("TestModel", self.db.tables)
        self.assertIn("AnotherTestModel", self.db.tables)

        # Drop second table
        self.db.drop(AnotherTestModel)
        self.assertEqual(len(self.db.tables), 0)

    def test_integration_with_table_operations(self):
        """Test integration between NoDB and table operations."""
        # Create table and add data
        table = self.db.table(TestModel)
        test_record = TestModel(id=1, name="Alice", email="alice@example.com")
        table.save(test_record)

        # Verify data exists
        retrieved = table.fetch("1")
        self.assertEqual(retrieved.name, "Alice")
        self.assertEqual(retrieved.email, "alice@example.com")

        # Create another table
        another_table = self.db.table(AnotherTestModel, "id")
        another_record = AnotherTestModel(id="key1", value=99.5)
        another_table.save(another_record)

        # Verify both tables work independently
        self.assertEqual(len(table.keys()), 1)
        self.assertEqual(len(another_table.keys()), 1)

        retrieved_another = another_table.fetch("key1")
        self.assertEqual(retrieved_another.value, 99.5)

    def test_table_persistence_across_nodb_instances(self):
        """Test that tables persist when creating new NoDB instances."""
        # Create table and add data
        table = self.db.table(TestModel)
        test_record = TestModel(id=1, name="Bob", email="bob@example.com")
        table.save(test_record)

        # Create new NoDB instance with same path
        new_db = NoDB(str(self.db_path))
        new_table = new_db.table(TestModel)

        # Verify data persists
        retrieved = new_table.fetch("1")
        self.assertEqual(retrieved.name, "Bob")
        self.assertEqual(retrieved.email, "bob@example.com")

    def test_drop_table_after_recreation(self):
        """Test dropping a table after recreating NoDB instance."""
        # Create table and add data
        table = self.db.table(TestModel)
        test_record = TestModel(id=1, name="Charlie", email="charlie@example.com")
        table.save(test_record)

        # Create new NoDB instance and recreate table reference
        new_db = NoDB(str(self.db_path))
        new_table = new_db.table(TestModel)

        # Verify data exists
        self.assertEqual(len(new_table.keys()), 1)

        # Drop table from new instance
        new_db.drop(TestModel)

        # Verify table is removed
        self.assertNotIn("TestModel", new_db.tables)
        table_storage_path = new_db.storage.add_child("TestModel").path
        self.assertFalse(table_storage_path.exists())

    def test_key_expr_variations(self):
        """Test different key expressions work correctly."""

        # Test with nested field path
        class NestedModel(BaseModel):
            id: int
            metadata: dict

        table = self.db.table(NestedModel, "metadata.key")
        self.assertEqual(table.key_expr, "metadata.key")

        # Test with simple field
        table2 = self.db.table(TestModel, "name")
        self.assertEqual(table2.key_expr, "name")

    def test_concurrent_table_access(self):
        """Test accessing the same table schema with different key expressions."""
        # This should reuse the same table instance, so key_expr won't change
        table1 = self.db.table(TestModel, "id")
        table2 = self.db.table(TestModel, "email")  # This should return table1

        self.assertIs(table1, table2)
        self.assertEqual(table1.key_expr, "id")  # Should keep original key_expr
