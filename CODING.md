# Higurashi Python Coding Conventions

This document describes the coding conventions and style guidelines for the Higurashi project's Python codebase.

---

## Table of Contents

1. [Code Style](#code-style)
2. [Naming Conventions](#naming-conventions)
3. [Type Hints](#type-hints)
4. [Documentation](#documentation)
5. [Imports](#imports)
6. [Error Handling](#error-handling)
7. [Database and ORM](#database-and-orm)
8. [Module Organization](#module-organization)
9. [Testing](#testing)

---

## Code Style

### General Formatting

- **Indentation**: 4 spaces (no tabs)
- **Line length**: Flexible, but prefer readability over strict limits
- **Blank lines**: Use blank lines to separate logical sections
- **Parentheses style**: Opening parenthesis on same line, closing on new line for multi-line constructs

```python
# Multi-line function call
result = some_function(
        param1,
        param2,
        param3 )

# Multi-line conditional
if( condition_a
        and condition_b
        and condition_c ):
    do_something()
```

### Parentheses in Conditionals

Always use parentheses around conditions in `if`, `while`, and similar statements:

```python
# Correct
if( x > 0 ):
    pass

# Incorrect
if x > 0:
    pass
```

### String Formatting

- Prefer f-strings for string interpolation
- Use `%` formatting for legacy compatibility where needed

```python
# Preferred
error_msg = f'"{name}" is not a valid tag name'

# Legacy style (acceptable in existing code)
filename = '%016x.%s' % ( obj_id, extension, )
```

---

## Naming Conventions

### General Rules

- **Classes**: PascalCase (e.g., `Database`, `ThumbRequest`, `ImageFile`)
- **Functions/Methods**: snake_case (e.g., `get_file`, `check_tag_name`, `init`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `VERSION`, `REVISION`, `MIN_THUMB_EXP`)
- **Private attributes**: Single or double underscore prefix (e.g., `__tag`, `_construct_session_object`)
- **Module-level private variables**: Single underscore prefix (e.g., `_LIBRARY`, `_DEBUG_TIME_OVERRIDE`)

### Method Name Patterns

Follow these conventions for method naming:

- **Getters**: `get_*()` (e.g., `get_name()`, `get_type()`, `get_id()`)
- **Setters**: `set_*()` (e.g., `set_name()`, `set_priority()`)
- **Boolean queries**: `is_*()` or `has_*()` (e.g., `is_relation_ordered()`)
- **Listing operations**: `list_*()` (e.g., `list_streams()`, `list_tags()`)
- **Creation operations**: `make_*()` or `create_*()` (e.g., `make_tag()`, `create_album()`)
- **Action operations**: Verb form (e.g., `register_file()`, `assign()`, `enable_write_access()`)

### Special Naming Patterns

- **Database constraint classes**: Suffix with `Constraint` (e.g., `TagConstraint`, `NameConstraint`)
- **Configuration classes**: Suffix with `Config` (e.g., `MainConfig`, `ImageDbDataConfig`)
- **Interface classes**: Suffix with `_interface` or `Interface` (e.g., `Albums_interface`, `JsonInterface`)
- **Internal helper methods**: Prefix with single underscore (e.g., `_get_stream()`, `_list_streams()`)
- **Private implementation methods**: Prefix with double underscore (e.g., `__add_constraints`, `__assign_duplicate`)

---

## Type Hints

### Required Usage

Type hints are **required** for:

- All public function/method signatures
- Function parameters and return types
- Class attributes when not obvious from context

### Special Cases

- `__init__` methods: Type parameters but **do not** add return type annotations
- Private methods (starting with `_` or `__`): Type hints recommended but not required

### Type Hint Style

Use the `typing` module for complex types:

```python
from typing import Optional, List, Dict, Tuple, Union, NamedTuple

# Regular methods - include return type
def get_file( self, file_id: int ) -> Optional[File]:
    pass

# __init__ methods - NO return type annotation
def __init__( self, db: Database, session_id: str ):
    self.db = db
    self.session_id = session_id

def list_tags( self ) -> List[Tag]:
    pass

def get_metadata( self ) -> Dict[str, Any]:
    pass

ObjectTypeSelect = Union[ObjectType, ObjectClass, List[ObjectType], List[ObjectClass]]
```

### Multi-line Type Imports

For long type import lists, use backslash continuation:

```python
from typing import \
        Optional, \
        NamedTuple, \
        List, \
        Dict, \
        Tuple
```

### Type Aliases

Create type aliases for complex or repeated type combinations:

```python
ObjectTypeSelect = Union[ObjectType, ObjectClass, List[ObjectType], List[ObjectClass]]
```

---

## Documentation

### Docstring Style

Use **Google-style docstrings** with the following format:

```python
def method_name( param1: Type1, param2: Type2 ) -> ReturnType:
    """ Brief one-line description.

    Longer description if needed, explaining behavior, side effects,
    and any important details. Can span multiple lines.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: Description of when this is raised
    """
```

### Key Documentation Rules

1. **Space between quotes and content**: Always include a space after opening `"""` and before closing `"""`
2. **Document all public APIs**: Any method or function without a leading underscore should be documented
3. **Skip private methods**: Single or double underscore prefixed methods typically don't need docstrings
4. **Module docstrings**: Add module-level docstrings for scripts and top-level modules
5. **Class docstrings**: Document the class purpose, key attributes, and usage examples

### Examples Section

For complex classes, include an `Example:` section:

```python
class Database( Session ):
    """ Primary interface for interacting with the Higurashi database.

    The Database class provides all high-level operations for managing files,
    tags, albums, and queries. It handles content-addressable storage with
    automatic deduplication based on file hashes.

    Example:
        db = hdbfs.Database()
        db.enable_write_access()

        # Register a file
        f = db.register_file('/path/to/image.jpg')

        # Tag it
        tag = db.make_tag('vacation')
        f.assign(tag)

        # Commit changes
        db.close()

    Attributes:
        albums: Albums_interface for album operations
        tbcache: Thumbnail cache manager
    """
```

### NamedTuple Documentation

Document NamedTuple attributes in the class docstring:

```python
class ThumbRequest( NamedTuple ):
    """ Represents a thumbnail generation request.

    Used by the thumbnail generation system to track which thumbnails need to
    be generated for which images.

    Attributes:
        prio: Priority level (ImageRequestPriority enum)
        exps: List of exponent values for thumbnail sizes (e.g., [8, 9, 10]
            for sizes 256, 512, 1024), or None if metadata needs initialization
        file: The ImageFile that needs thumbnails
    """
    prio: ImageRequestPriority
    exps: Optional[List[int]]
    file: ImageFile
```

---

## Imports

### Import Organization

Organize imports in three groups, separated by blank lines:

1. **Standard library imports**
2. **Third-party library imports**
3. **Local/project imports**

```python
# Standard library
import os
import re
import datetime

# Third-party
from sqlalchemy import and_
import cherrypy

# Local
import hdbfs
import hdbfs.model as model
from hdbfs.session import Session
from hdbfs.objects.file import File
```

### Import Styles

- **Prefer explicit imports**: `from module import Class` over `import module`
- **Module aliases**: Use `as` for commonly referenced modules (e.g., `import hdbfs.model as model`)
- **Avoid star imports**: Except for specific internal APIs (e.g., `from hdbfs.defs import *`)

### Relative vs Absolute Imports

Use absolute imports from the package root:

```python
# Correct
import hdbfs.model as model
from hdbfs.session import Session

# Avoid relative imports
from .model import Object
from ..session import Session
```

---

## Error Handling

### Exception Handling

- **Avoid bare `except:` clauses**: Always specify exception types
- **Document TODO for technical debt**: Mark bare excepts with TODO comments

```python
# Bad - needs fixing
try:
    result = operation()
except:  # TODO: Determine specific exceptions to catch
    handle_error()

# Good
try:
    result = operation()
except (ValueError, KeyError) as e:
    handle_error( e )
```

### Assertions vs Error Returns

- **Avoid assertions for input validation**: Use proper error returns or raise exceptions
- **Assertions are for invariants**: Use only for internal consistency checks during development

```python
# Bad - replaced during cleanup
assert user_input is not None

# Good - proper error handling
if user_input is None:
    return json_err('value', 'user_input cannot be None')
```

### Error Return Conventions

For JSON APIs, use standardized error response helpers:

```python
def json_ok( **args: Any ) -> Dict[str, Any]:
    """ Create a successful JSON response. """
    args['result'] = 'ok'
    return args

def json_err( err: Union[str, Exception], emsg: Optional[str] = None ) -> Dict[str, Any]:
    """ Create an error JSON response. """
    # Implementation...
```

---

## Database and ORM

### SQLAlchemy Conventions

- **Use declarative base**: All model classes inherit from `Base`
- **Explicit table names**: Always specify `__tablename__`
- **Type annotations on models**: Use Python type hints alongside SQLAlchemy types

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional

Base = declarative_base()

class Object( Base ):
    __tablename__ = 'objects'

    object_id = Column( Integer, primary_key=True )
    name = Column( String, nullable=True )
    object_type = Column( Integer, nullable=False )
```

### Enum Usage

Use Python `Enum` classes for type-safe constants:

```python
from enum import Enum

class ObjectType( Enum ):
    NILL = 0
    FILE = 10000
    DUPLICATE = 10001
    ALBUM_FREE = 20000
    # ...

    def get_class( self ) -> ObjectClass:
        return ObjectClass( self.value // 100 )
```

### Query Patterns

- **Use SQLAlchemy query API**: Prefer ORM queries over raw SQL
- **Filter chaining**: Chain filters for readability
- **Subqueries**: Use `.subquery()` for complex queries

```python
result = session.model.query( model.Object ) \
    .filter( model.Object.object_type == ObjectType.FILE.value ) \
    .filter( model.Object.name.like( pattern ) ) \
    .order_by( model.Object.object_id ) \
    .first()
```

---

## Module Organization

### Package Structure

The project follows a layered architecture:

```
lib/
├── hdbfs/              # Core database library
│   ├── objects/        # Object model classes
│   ├── imgdb/          # Image-specific functionality
│   └── legacy/         # Backward compatibility
├── higu/               # Web server
└── json_interface/     # JSON RPC API
```

### Module Responsibilities

- **`hdbfs`**: Core database operations, object model, session management
- **`hdbfs.objects`**: Object classes (File, Album, Tag, etc.)
- **`hdbfs.imgdb`**: Image-specific functionality (thumbnails, EXIF, metadata)
- **`hdbfs.legacy`**: Migration and backward compatibility code
- **`higu`**: Web server and HTTP endpoints
- **`json_interface`**: JSON RPC API layer

### File Naming

- **Module files**: snake_case (e.g., `web_session.py`, `thumb_generator.py`)
- **Package init**: `__init__.py` for package exports

---

## Testing

### Test Organization

- **Test directory**: All tests in `test/` directory
- **Test file naming**: `*_cases.py` (e.g., `query_cases.py`, `imgdb_cases.py`)
- **Test utilities**: Shared utilities in `testutil.py`

### Test Base Class

Extend the project's `TestCase` class:

```python
import unittest
from test.testutil import TestCase

class MyTestCase( TestCase ):

    def test_something( self ):
        # Test implementation
        pass
```

### Test Data

- **Test data location**: `test/data/` directory
- **Consistent test files**: Use predefined test images (e.g., `red_sq.png`, `blue_sq.png`)
- **Hash constants**: Define expected hashes in test base class

---

## Additional Conventions

### Global State

- **Module-level globals**: Use single underscore prefix (e.g., `_LIBRARY`)
- **Global functions**: Provide `init()` and `dispose()` for setup/teardown

```python
_LIBRARY = None

def init( library_path=None ):
    """ Initialize the hdbfs library with a database path. """
    global _LIBRARY
    _LIBRARY = library_path
    # ...

def dispose():
    """ Clean up and dispose of library resources. """
    global _LIBRARY
    _LIBRARY = None
    # ...
```

### Context Managers

Use context managers for resource management:

```python
class _AccessContext:
    """ Context instance for accessing a session. """

    def __enter__(self):
        # Setup
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        pass
```

### Decorators

Use decorators for cross-cutting concerns:

```python
class SessionObject:

    @staticmethod
    def _with_access():
        """ Decorator to ensure session access for method calls. """
        def decorator( func ):
            def wrapper( self, *args, **kwargs ):
                with self.session._access():
                    return func( self, *args, **kwargs )
            return wrapper
        return decorator

    @_with_access()
    def get_name( self ):
        return self.obj.name
```

---

## TODO Comments

Document technical debt and future improvements:

```python
# TODO: Determine specific exceptions to catch here
# TODO: Re-enable proper exception handling after refactor
# TODO: Verify NULL handling in parent lookups
```

---

## Summary

Key principles for Higurashi Python code:

1. **Explicit is better than implicit**: Use type hints, explicit imports, and clear naming
2. **Document public APIs**: Google-style docstrings for all public methods
3. **Consistent naming**: Follow established patterns for getters, setters, and operations
4. **Type safety**: Use type hints and avoid dynamic typing where possible
5. **Clean error handling**: No bare excepts, proper exception types
6. **SQLAlchemy best practices**: Use ORM patterns, explicit table names, type-safe enums
7. **Test everything**: Unit tests for all major functionality

---

**Last Updated**: 2026-08-26
