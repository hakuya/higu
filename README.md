# Higurashi

A tag-oriented image organizer with a web interface for managing and browsing your image collection.

## Overview

Higurashi is a self-hosted image management system that helps you organize photos and images using a flexible tag-based system. It uses content hashing to automatically detect duplicates, generates thumbnails on-demand, and provides a powerful query language for finding exactly what you're looking for.

### Key Features

- **Tag-based organization** - Organize images with hierarchical tags (e.g., `category:subcategory`)
- **Duplicate detection** - Automatically identifies duplicate files using CRC32, MD5, and SHA1 hashing
- **Album management** - Group related images into albums with descriptions and metadata
- **Smart queries** - Powerful search syntax with filtering by tags, dates, names, and custom metadata
- **Thumbnail generation** - Automatic thumbnail creation with multiple size options
- **Import tracking** - Keep track of when and how files were added to your library
- **Web interface** - Modern React-based UI for browsing and managing your collection
- **Content-addressable storage** - Files are stored by hash, preventing true duplicates

## Requirements

### System Requirements

- Python 3.6 or higher
- Node.js and npm (for building the web interface)

### Python Dependencies

- **SQLAlchemy** - Database ORM (tested with version 0.5.8+)
- **CherryPy** - Web framework (tested with version 3.1.2+)
- **Pillow** (or PIL) - Image processing (tested with version 1.1.7+)

Install Python dependencies:
```bash
pip install sqlalchemy cherrypy pillow
```

## Installation

### 1. Clone or Download

Extract or checkout the Higurashi repository to a directory on your system.

```bash
git clone <repository-url> higurashi
cd higurashi
```

### 2. Build the Web Interface

Install JavaScript dependencies and build the frontend:

```bash
cd webapp
npm install
npm run build
cd ..
```

This will download all required frontend dependencies (React, Bootstrap, jQuery, etc.) and compile the application into `webapp/build/_bundle.js`.

### 3. Run Tests

Verify that Higurashi works correctly in your environment:

```bash
./run_tests.sh
```

This will test:
- System requirements
- Image database functions
- Core library functionality
- Query system
- Thumbnail generation
- Web session management
- Legacy database migration support

### 4. Configure Your Installation

Copy the test configuration file and customize it:

```bash
cp test.cfg mysite.cfg
```

Edit `mysite.cfg` and set your preferences:

```ini
[main]
# Path to your library (absolute path recommended)
library = /path/to/your/library

[www]
# IP address to bind to (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)
host = 0.0.0.0
# Port to run the web server on
port = 8080
```

### 5. Create Start Scripts

Create convenience scripts for your configuration:

```bash
ln -s start.test.sh start.mysite.sh
ln -s addto.test.sh addto.mysite.sh
ln -s usermod.test.sh usermod.mysite.sh
```

Or create custom scripts that reference your configuration file.

### 6. Start the Server

Launch the web server:

```bash
./start.mysite.sh
```

The interface will be available at `http://localhost:8080` (or whatever host/port you configured).

## Usage

### Adding Images

Use the `insertfile.py` script to add images to your library:

```bash
# Add a single image
python scripts/insertfile.py -c mysite.cfg /path/to/image.jpg

# Add images with tags
python scripts/insertfile.py -c mysite.cfg -t "vacation,beach,2024" image1.jpg image2.jpg

# Create an album with images
python scripts/insertfile.py -c mysite.cfg -a "Beach Trip 2024" -t "vacation" *.jpg

# Add text description to an album
python scripts/insertfile.py -c mysite.cfg -a "Trip" -x description.txt *.jpg
```

#### Options

- `-c, --config` - Configuration file to use
- `-t, --tags` - Comma-separated list of tags to apply (tags must exist)
- `-T, --newtags` - Same as `-t`, but creates tags if they don't exist
- `-a, --album` - Create an album and add files to it
- `-x, --text` - Add a text description file to the album
- `-n, --name-policy` - How to handle filenames (`noreg`, `noset`, `setundef`, `setall`)
- `-r, --recovery` - Recovery mode for re-importing lost file data
- `-p, --pretend` - Dry run mode

### Query Syntax

The search system supports a powerful query language:

#### Basic Search

- `123` - Search by object ID
- `@filename` - Search by filename (wildcards supported)
- `#tagname` - Search for items with this tag (fuzzy matching)

#### Advanced Constraints

- `&name=value` - Exact metadata match
- `&key~pattern` - Metadata pattern match (wildcards with `*`)
- `&date>=2024/01/01` - Metadata comparison (supports `>`, `<`, `>=`, `<=`, `=`, `!=`)
- `&!name` - Items without a name
- `&!!name` - Items with a name

#### Query Modifiers

- `!constraint` - Exclude items matching constraint
- `?constraint` - OR logic (include items matching any constraint)
- `$type:file` - Filter by type (`file`, `album`, `import`)
- `$sort:name` - Sort results (`name`, `add`, `origin`, `rand`)
- `$sort:name:desc` - Sort descending
- `$limit:50` - Limit number of results
- `$range:0:50` - Get a specific range of results
- `$expand` - Include album contents in results
- `$untagged` - Show only untagged items

#### Examples

```
# Find images from 2024 with the beach tag
#beach &origin>=2024/01/01 &origin<2025/01/01

# Find untagged files
$untagged $type:file

# Find files with "sunset" in the name, sorted by date
@*sunset* $sort:origin:desc

# Find all files except those tagged "private"
$type:file !#private
```

### Managing Users

Use the user management script to add, modify, or remove users:

```bash
# Add a user
python scripts/manageusers.py -c mysite.cfg add username

# Change password
python scripts/manageusers.py -c mysite.cfg passwd username

# Set user permissions (0=none, 1=read, 2=edit, 3=admin)
python scripts/manageusers.py -c mysite.cfg setlevel username 2

# List users
python scripts/manageusers.py -c mysite.cfg list

# Delete a user
python scripts/manageusers.py -c mysite.cfg del username
```

## Architecture

### Backend

- **hdbfs** - The core "Higurashi Database FileSystem" library
  - Content-addressable storage with hash-based deduplication
  - SQLAlchemy-based data model
  - Stream management for original files and thumbnails
  - Tag and album management
  - Query engine with constraint system

- **higu** - Web server and session management
  - CherryPy-based HTTP server
  - User authentication and session handling
  - JSON API for frontend communication
  - Background thumbnail generation

### Frontend

- React-based single-page application
- Bootstrap UI components
- jQuery for DOM manipulation and drag-drop
- Tab-based interface for multiple views
- Real-time thumbnail loading with priority system

### Storage

Images are stored in a content-addressable format:
- Database tracks metadata, relationships, and file hashes
- Actual file data stored in `streams/` directory organized by hash
- Multiple streams per file (original + various thumbnail sizes)
- Automatic deduplication - identical files share storage

## Project Structure

```
higu/
├── lib/                    # Python libraries
│   ├── hdbfs/             # Core database and file management
│   ├── higu/              # Web server and configuration
│   └── json_interface/    # JSON API implementation
├── scripts/               # Command-line utilities
│   ├── server.py          # Start the web server
│   ├── insertfile.py      # Add files to library
│   └── manageusers.py     # User management
├── webapp/                # Frontend application
│   ├── src/               # React source code
│   ├── html/              # HTML templates
│   └── build/             # Compiled JavaScript
├── test/                  # Test suite
└── *.cfg                  # Configuration files
```

## Development

Higurashi is a personal project, but contributions are welcome!

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run specific test suites
./run_tests.sh imgdb      # Image database tests
./run_tests.sh hdbfs      # Core library tests
./run_tests.sh query      # Query system tests
./run_tests.sh insert     # Import script tests
./run_tests.sh web        # Web session tests
./run_tests.sh legacy     # Database migration tests
```

### Building the Frontend

```bash
cd webapp
npm run build
```

This compiles the React application into `webapp/build/_bundle.js`.

## Deployment Notes

### Single-User Setup

For personal use on a local machine:
1. Set `host = 127.0.0.1` in your config to only accept local connections
2. Create a single admin user
3. Access via `http://localhost:8080`

### Multi-User Considerations

While multi-user support exists, it has primarily been tested in single-user deployments:
- User authentication is supported with password hashing
- Access levels: none, read-only, edit, admin
- Consider using a reverse proxy (nginx, Apache) with HTTPS for network access
- Session management uses cookies

### Security

If exposing to a network:
- Use HTTPS (configure a reverse proxy)
- Set strong passwords for all users
- Consider firewall rules to limit access
- Review CherryPy security best practices
- The application was designed for trusted users, not hostile environments

## License

Copyright (c) 2026, Erik Miranda
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the conditions in the LICENSE file are met.
