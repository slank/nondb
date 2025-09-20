#!/usr/bin/env python3
"""
Smoke test script for NonDB package artifacts.

This script validates that built package artifacts (wheels and source distributions)
contain all expected files and can be imported correctly.

Usage:
    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
    uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py
"""

import sys
import tempfile
import traceback

from pydantic import BaseModel


def test_basic_import():
    """Test that NonDB can be imported."""
    try:
        import nondb  # noqa # pylint: disable=unused-import
        from nondb import NonDB  # noqa # pylint: disable=unused-import

        print("✓ NonDB module imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import NonDB: {e}")
        return False


def test_core_classes():
    """Test that core classes can be imported and instantiated."""
    try:
        from nondb.NonIndex import NonIndex  # noqa # pylint: disable=unused-import
        from nondb.NonTable import NonTable  # noqa # pylint: disable=unused-import
        from nondb.Storage import Storage  # noqa # pylint: disable=unused-import

        print("✓ Core classes imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import core classes: {e}")
        return False


def test_basic_functionality():
    """Test basic NonDB functionality."""
    from nondb import NonDB

    try:
        # Define a test model
        class TestModel(BaseModel):
            id: int
            name: str

        # Create a temporary database
        with tempfile.TemporaryDirectory() as temp_dir:
            db = NonDB(temp_dir)
            table = db.table(TestModel)

            # Test basic operations
            record = TestModel(id=1, name="test")
            table.save(record)

            fetched = table.fetch("1")
            assert fetched is not None
            assert fetched.id == 1
            assert fetched.name == "test"

        print("✓ Basic functionality test passed")
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False


def test_indexing():
    """Test indexing functionality."""
    from nondb import NonDB

    try:
        class User(BaseModel):
            id: int
            name: str
            category: str

        with tempfile.TemporaryDirectory() as temp_dir:
            db = NonDB(temp_dir)
            table = db.table(User)

            # Save test data
            table.save(User(id=1, name="Alice", category="admin"))
            table.save(User(id=2, name="Bob", category="user"))

            # Test indexing
            index = table.index("category")
            index.rebuild_index()

            admins = index.get("admin")
            assert len(admins) == 1

        print("✓ Indexing test passed")
        return True
    except Exception as e:
        print(f"✗ Indexing test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests."""
    print("Running NonDB smoke tests...")

    tests = [
        test_basic_import,
        test_core_classes,
        test_basic_functionality,
        test_indexing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        print("✗ Some tests failed")
        sys.exit(1)
    else:
        print("✓ All smoke tests passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
