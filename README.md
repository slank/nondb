# Nondb

A simple, filesystem-based document store for Pydantic-modeled JSON data.

## Purpose

Nondb is a lightweight document database that uses the filesystem for storage and Pydantic models for data validation and serialization. It provides a simple interface for storing, retrieving, and querying JSON documents while leveraging Pydantic's powerful data validation capabilities.

Perfect for:
- Small to medium-sized applications that need structured data storage
- Prototypes and development environments  
- Applications that benefit from human-readable, file-based data storage

## Features

- **Pydantic Integration**: Automatic JSON serialization/deserialization using Pydantic models
- **Type Safety**: Full type checking and validation through Pydantic
- **Filesystem Storage**: Human-readable JSON files organized in directories
- **Flexible Keys**: Customizable key expressions using JMESPath syntax
- **Secondary Indexing**: Create indices on any field for fast lookups
- **Multiple Tables**: Support for multiple data models in a single database
- **Simple API**: Intuitive interface for CRUD operations

## Installation

```bash
pip install nondb
```

Or install from source:

```bash
git clone https://github.com/slank/nondb.git
cd nondb
pip install -e .
```

## Usage Examples

### Basic Usage

```python
from pydantic import BaseModel
from nondb import NoDB

# Define your data model
class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

# Initialize database
db = NoDB("./my_database")

# Get a table for your model
users = db.table(User, key_expr="id")

# Create and save records
user = User(id=1, name="Alice Smith", email="alice@example.com", age=30)
users.save(user)

# Fetch records
retrieved_user = users.fetch("1")
print(retrieved_user.name)  # Alice Smith

# Get all records
all_users = users.all()
```

### Secondary Indexing

```python
# Create indices (best to do this before adding records)
age_index = users.index("age")

# Add some users (index will be automatically updated)
users.save(User(id=1, name="Alice", email="alice@example.com", age=30))
users.save(User(id=2, name="Bob", email="bob@example.com", age=25))
users.save(User(id=3, name="Carol", email="carol@example.com", age=30))

# Find all users of a specific age
thirty_year_olds = age_index.get("30")

# If you create an index after records exist, rebuild it:
# age_index.rebuild_index()
```

## Contributing Tips

We welcome contributions! Here's how to get started:

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/slank/nondb.git
   cd nondb
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run tests**:
   ```bash
   python -m unittest discover tests/ -v
   ```

### Code Style

- We use Black for code formatting
- Type hints are required for all public APIs
- Follow PEP 8 naming conventions
- Write docstrings for all public methods

### Testing

- Add tests for all new features
- Maintain test coverage above 90%
- Tests are located in the `tests/` directory
- Use descriptive test names and docstrings

### Submitting Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with tests

3. **Run the test suite**:
   ```bash
   python -m unittest discover tests/ -v
   ```

4. **Format your code**:
   ```bash
   black src/ tests/
   ```

5. **Submit a pull request** with:
   - Clear description of changes
   - Tests for new functionality
   - Updated documentation if needed

### Areas for Contribution

- **Performance improvements**: Optimize file I/O operations
- **Query capabilities**: Enhanced filtering and search
- **Documentation**: More examples and tutorials
- **Error handling**: Better error messages and recovery
- **Concurrent access**: Thread-safe operations
- **Data migration**: Tools for schema evolution

### Reporting Issues

When reporting bugs, please include:
- Python version
- Nondb version
- Minimal reproduction case
- Error messages and stack traces
- Expected vs actual behavior

## License

MIT License - see LICENSE file for details.