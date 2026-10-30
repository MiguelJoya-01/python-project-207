# Page Analyzer

[![hexlet-check](https://github.com/MiguelJoya-01/python-project-207/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/MiguelJoya-01/python-project-207/actions)

Page Analyzer is a web application built with Flask that allows users to add websites, check their availability, and collect basic SEO information from their pages.

The project was developed as part of the Python programming course at Códica.

## Features

- Add and store website URLs.
- Validate URLs before saving them.
- Prevent duplicate URLs.
- View a list of registered websites.
- Check website availability and HTTP status codes.
- Extract basic SEO information:
  - Page title
  - Main heading (`h1`)
  - Meta description
- View the history of checks for each website.
- Store application data in a PostgreSQL database.

## Technologies

- Python 3.12.3
- Flask
- PostgreSQL
- Psycopg
- Requests
- Beautiful Soup 4
- Bootstrap
- Gunicorn
- Ruff
- uv

## Installation

### Requirements

- Python 3.12.3
- PostgreSQL
- [uv](https://docs.astral.sh/uv/)

### 1. Clone the repository

```bash
git clone https://github.com/MiguelJoya-01/python-project-207.git
cd python-project-207
```

### 2. Install dependencies

```bash
make install
```

### 3. Configure environment variables

Create a `.env` file in the project root and set your database connection string:

```env
DATABASE_URL=postgresql:///page_analyzer
```

Make sure PostgreSQL is running and that the database exists.

### 4. Create the database tables

```bash
psql -d "$DATABASE_URL" -f database.sql
```

### 5. Run the application

```bash
make dev
```

The development server will be available at:

`http://127.0.0.1:5000`

## Available Commands

The project includes a Makefile with the following commands:

| Command | Description |
|---|---|
| `make install` | Install project dependencies using uv. |
| `make dev` | Run the Flask development server. |
| `make lint` | Check the code with Ruff. |
| `make start` | Run the application with Gunicorn. |
| `make build` | Execute the build script. |
| `make render-start` | Start the application with Gunicorn on the configured port. |

## Build

The `build.sh` script automates the build process. It installs uv if necessary, installs the project dependencies, and creates the database tables using `database.sql`.

Run it with:

```bash
make build
```

## Database

The application uses PostgreSQL to store website information and their verification history.

The database schema is defined in `database.sql` and includes two tables:

- `urls`: stores registered websites and their creation dates.
- `url_checks`: stores the results of website checks, including HTTP status codes and SEO information.

## Automated Checks

The project uses GitHub Actions to run the automated checks configured in the repository.

You can also run the code linter locally with:

```bash
make lint
```

## Deployment

The application is deployed on Render:

[Page Analyzer](https://python-project-207-94zu.onrender.com)

## About the Project

This project was developed as a practical exercise in building a web application with Python and Flask. It brings together topics such as routing, database management, HTTP requests, HTML parsing, and deployment.
