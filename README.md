# Nondb

A simple, filesystem-based document store for Pydantic-modeled JSON data.

## Purpose

Nondb is a lightweight document database that uses the filesystem for storage and Pydantic models for data validation and serialization. It provides a simple interface for storing, retrieving, and querying JSON documents while leveraging Pydantic's powerful data validation capabilities.

Perfect for:
- Small to medium-sized applications that need structured data storage
- Prototypes and development environments  
- Applications that benefit from human-readable, file-based data storage
- Projects that want type-safe data handling with automatic validation

## Features

- **Pydantic Integration**: Automatic JSON serialization/deserialization using Pydantic models
- **Type Safety**: Full type checking and validation through Pydantic
- **Filesystem Storage**: Human-readable JSON files organized in directories
- **Flexible Keys**: Customizable key expressions using JMESPath syntax
- **Secondary Indexing**: Create indices on any field for fast lookups
- **Multiple Tables**: Support for multiple data models in a single database
- **Simple API**: Intuitive interface for CRUD operations
- **No Dependencies**: Minimal external dependencies (just Pydantic and JMESPath)
- **Python 3.13+**: Built for modern Python

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

### Working with Different Key Expressions

```python
class Product(BaseModel):
    sku: str
    name: str
    price: float
    category: str

# Use SKU as the primary key
products = db.table(Product, key_expr="sku")

product = Product(sku="LAPTOP-001", name="Gaming Laptop", price=1299.99, category="electronics")
products.save(product)

# Fetch by SKU
laptop = products.fetch("LAPTOP-001")
```

### Secondary Indexing

```python
# Create indices (best to do this before adding records)
age_index = users.index("age")
category_index = products.index("category")

# Add some users (index will be automatically updated)
users.save(User(id=1, name="Alice", email="alice@example.com", age=30))
users.save(User(id=2, name="Bob", email="bob@example.com", age=25))
users.save(User(id=3, name="Carol", email="carol@example.com", age=30))

# Add some products
products.save(Product(sku="LAPTOP-001", name="Gaming Laptop", price=1299.99, category="electronics"))
products.save(Product(sku="BOOK-001", name="Python Guide", price=29.99, category="books"))

# Find all users of a specific age
thirty_year_olds = age_index.get("30")

# Find products by category
electronics = category_index.get("electronics")

# If you create an index after records exist, rebuild it:
# age_index.rebuild_index()
```

### Multiple Tables

```python
class Order(BaseModel):
    order_id: str
    user_id: int
    product_sku: str
    quantity: int
    total: float

# Each model gets its own table
orders = db.table(Order, key_expr="order_id")

order = Order(
    order_id="ORD-001", 
    user_id=1, 
    product_sku="LAPTOP-001", 
    quantity=1, 
    total=1299.99
)
orders.save(order)
```

### Advanced Key Expressions

```python
class BlogPost(BaseModel):
    author: str
    title: str
    slug: str
    content: str
    published: bool

# Use slug as key
posts = db.table(BlogPost, key_expr="slug")

# Or use a compound expression
posts_by_author = db.table(BlogPost, key_expr="author")
```

### Database Operations

```python
# Get table statistics
stats = users.stat()
print(f"Records: {stats['num_records']}")
print(f"Indices: {stats['indices']}")

# List all keys
user_ids = users.keys()

# Delete records
users.delete(user)

# Drop entire table
db.drop(User)
```

## API Reference

### NoDB

- `NoDB(path: str)` - Initialize database at given path
- `table(schema: type[BaseModel], key_expr: str = "id") -> NoTable` - Get/create table
- `drop(schema: type[BaseModel], raiseOnMissing: bool = False)` - Drop table

### NoTable

- `save(record: T)` - Save a record
- `fetch(key: str) -> T` - Fetch record by key
- `all() -> list[T]` - Get all records
- `keys() -> list[str]` - Get all keys
- `delete(record: T)` - Delete a record
- `index(index_expr: str) -> NoIndex` - Create/get index
- `stat() -> dict` - Get table statistics

### NoIndex

- `get(index_key: str) -> list[T]` - Get records by index key
- `put(record: T)` - Update index for record
- `delete(record: T)` - Remove record from index
- `rebuild_index()` - Rebuild index from all table records (use when creating index after records exist)

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