# NonDB - Document Store for Pydantic Models

NonDB is a Python library that provides a filesystem-based JSON document store for Pydantic models with indexing capabilities. It's designed as a lightweight alternative to traditional databases for applications that need structured data persistence without the overhead of a full database server.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap and Dependencies
- **CRITICAL**: The project requires Python 3.13, but the validation environment uses Python 3.12. To work with Python 3.12, temporarily modify `pyproject.toml` to change `requires-python = ">=3.13"` to `requires-python = ">=3.12"`.
- **Network Issues Workaround**: If pip install fails with timeout errors, use: `pip install --user --cache-dir /tmp/pip-cache <package_name>`
- Install core dependencies: `pip install --user --cache-dir /tmp/pip-cache pydantic jmespath`
- Install development dependencies: `pip install --user --cache-dir /tmp/pip-cache black coverage mypy`
- For the example application: `pip install --user --cache-dir /tmp/pip-cache nicegui`

### Build and Test
- **No build step required** - This is a pure Python library with no compilation
- Run tests: `PYTHONPATH=./src python3 -m unittest discover -s tests -p "test_*.py" -v`
  - **Timing**: Tests complete in <1 second (54 tests)
  - **NEVER CANCEL**: Although fast, always let tests complete fully
- Run tests with coverage: `PYTHONPATH=./src coverage run -m unittest discover -s tests -p "test_*.py"`
  - **Timing**: Coverage collection completes in <1 second
- Generate coverage report: `coverage report`

### Code Quality and Validation
- Format code: `black --check src tests examples` (validates formatting)
- Apply formatting: `black src tests examples`
- Type checking: `mypy src` (expect minor warnings about jmespath types)
- **ALWAYS** run all validation steps before committing: 
  1. `black --check src tests examples`
  2. `mypy src`
  3. `PYTHONPATH=./src python3 -m unittest discover -s tests -p "test_*.py" -v`

### Manual Validation and Testing Scenarios

**CRITICAL**: After making any changes, ALWAYS perform manual validation by:

1. **Basic Library Functionality Test**:
   ```python
   cd /home/runner/work/nondb/nondb
   PYTHONPATH=./src python3 -c "
   from nondb import NoDB
   from pydantic import BaseModel
   
   class TestModel(BaseModel):
       id: int
       name: str
   
   db = NoDB('/tmp/test_db')
   table = db.table(TestModel)
   record = TestModel(id=1, name='Test')
   table.save(record)
   fetched = table.fetch('1')
   print('SUCCESS: Library works correctly')
   print(f'Saved and retrieved: {fetched}')
   "
   ```

2. **Example Web Application Test**:
   ```bash
   # Start the example application
   cd /home/runner/work/nondb/nondb
   PYTHONPATH=./src python3 examples/proto.py &
   
   # Wait 3 seconds for startup, then test in browser
   # Navigate to http://localhost:8080
   # Verify "Main Page" appears with "Name" input field and "Click Me" button
   # Enter a name in the input field and click "Click Me" button
   # Application should respond (check console output)
   
   # Stop the application
   kill %1
   ```

3. **Index Functionality Test**:
   ```python
   PYTHONPATH=./src python3 -c "
   from nondb import NoDB
   from pydantic import BaseModel
   
   class User(BaseModel):
       id: int
       name: str
       category: str
   
   db = NoDB('/tmp/test_index_db')
   table = db.table(User)
   
   # Save test data
   table.save(User(id=1, name='Alice', category='admin'))
   table.save(User(id=2, name='Bob', category='user'))
   table.save(User(id=3, name='Charlie', category='admin'))
   
   # Test indexing
   category_index = table.index('category')
   category_index.rebuild_index()
   
   # Verify index works
   admins = category_index.get('admin')
   print(f'SUCCESS: Found {len(admins)} admin users')
   assert len(admins) == 2
   print('Index functionality validated')
   "
   ```

## Project Structure and Navigation

### Core Components
- `src/nondb/` - Main library code
  - `NoDB.py` - Main database class for managing tables
  - `NoTable.py` - Table implementation for storing Pydantic models
  - `NoIndex.py` - Indexing system using filesystem symlinks
  - `Storage.py` - Low-level filesystem storage abstraction
- `tests/nondb/` - Comprehensive test suite (54 tests with 100% coverage on core modules)
- `examples/proto.py` - NiceGUI web application example demonstrating library usage

### Key Areas for Development Work
- **Storage System**: `Storage.py` handles file-based persistence with JSON serialization
- **Table Operations**: `NoTable.py` manages CRUD operations and integrates with indexing
- **Indexing**: `NoIndex.py` uses filesystem symlinks for efficient lookups
- **Database Interface**: `NoDB.py` provides the main API for creating and managing tables

### Common Development Patterns
- All models inherit from Pydantic's `BaseModel`
- Tables are created per Pydantic schema type
- Indexing uses JMESPath expressions for field extraction
- Storage uses hierarchical directory structure with JSON files
- Tests use temporary directories and cleanup in tearDown methods

## Dependency Information

### Runtime Dependencies
- `pydantic>=2.11.7` - Data validation and serialization
- `jmespath>=1.0.1` - JSON path expressions for indexing

### Development Dependencies  
- `black` - Code formatting
- `coverage` - Test coverage measurement
- `mypy` - Static type checking (expect warnings about jmespath types)

### Example Dependencies
- `nicegui` - Web UI framework for the example application

## Common Tasks and Troubleshooting

### If Tests Are Failing
1. Ensure PYTHONPATH includes src: `PYTHONPATH=./src`
2. Verify all dependencies are installed
3. Check that temporary directories are being cleaned up properly

### If Example Application Won't Start
1. Verify nicegui is installed: `pip install --user nicegui`
2. Check that port 8080 is available
3. Ensure PYTHONPATH is set correctly

### If Type Checking Has Issues
- Expected warnings about jmespath types can be ignored
- Focus on type issues in the actual nondb code
- The codebase uses Python 3.13+ type syntax (generics, etc.)

### Network/Installation Issues
- Use `--cache-dir /tmp/pip-cache` flag with pip for network timeouts
- Use `--user` flag to install in user directory if permissions are restricted
- Consider using `--default-timeout=200` for slow connections

## File Locations Reference

### Configuration Files
- `pyproject.toml` - Project metadata and dependencies (modify Python version requirement if needed)
- `.vscode/settings.json` - VS Code configuration for unittest discovery
- `.gitignore` - Excludes Python cache files and db.sqlite3

### Generated Files (Do Not Commit)
- `.coverage` - Coverage data file
- `/tmp/test_*` - Temporary test databases
- `__pycache__/` directories
- `*.pyc` files

Always clean up temporary test files and exclude build artifacts from commits.