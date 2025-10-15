# Copilot Instructions for app-sso

This document outlines essential knowledge for AI coding agents to be immediately productive in the `app-sso` codebase.

## 1. Project Overview

`app-sso` is a Flask application providing Single Sign-On (SSO) functionality using OAuth 2.0 with Microsoft and Google. It leverages `Authlib` for OAuth integration and `Flask-SQLAlchemy` for database interactions with PostgreSQL. The entire application stack is containerized using Docker and orchestrated with Docker Compose.

## 2. Architecture Highlights

*   **`app.py`**: The central Flask application file. It defines:
    *   OAuth configurations for Microsoft and Google using `Authlib`.
    *   The `User` SQLAlchemy model for storing authenticated user information.
    *   Routes for the main page (`/`), OAuth login initiation (`/login/microsoft`, `/login/google`), OAuth callbacks (`/authorize/microsoft`, `/authorize/google`), and logout (`/logout`).
    *   A custom Flask CLI command `flask init-db` for database table creation.
    *   `ProxyFix` middleware is applied to handle requests correctly when behind a reverse proxy like Nginx.
*   **`templates/`**: Contains Jinja2 templates (`login.html`, `profile.html`) for the user interface.
*   **`Dockerfile`**: Builds the Docker image for the Flask application, installing dependencies from `requirements.txt` and setting up the `entrypoint.sh`.
*   **`docker-compose.yml`**: Defines three services:
    *   `nginx`: A reverse proxy (Nginx) handling external traffic and forwarding to the `webapp`.
    *   `webapp`: The Flask application, running with Gunicorn. It depends on the `db` service.
    *   `db`: A PostgreSQL database service, with data persistence managed by a Docker volume.
*   **`entrypoint.sh`**: An executable script run inside the `webapp` container. Its primary responsibilities are:
    *   Waiting for the PostgreSQL database to become available using `pg_isready`.
    *   Executing `flask init-db` to create necessary database tables.
    *   Starting the Gunicorn server to run the Flask application.

## 3. Critical Developer Workflows

### 3.1. Local Development Setup

To run the application locally using Docker Compose:

1.  **Environment Variables**: Ensure a `.env` file exists in the project root with the following variables configured:
    *   `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME` (for PostgreSQL connection)
    *   `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` (for Microsoft OAuth)
    *   `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (for Google OAuth)
    *   `DB_HOST` should typically be `db` when running with `docker-compose`.
2.  **Build and Run**: Execute the following command from the project root:
    ```bash
    docker-compose up --build
    ```
    This will build the `webapp` image (if not already built or `image` is commented out), start all services, and initialize the database.
3.  **Access Application**: The application will be accessible via Nginx, typically on `http://localhost` or `https://localhost` (depending on Nginx configuration in `nginx/nginx.conf`).

### 3.2. Database Management

*   **Initialization**: Database tables are automatically created on container startup by `entrypoint.sh` calling `flask init-db`.
*   **Migrations**: There is no explicit database migration tool (like Flask-Migrate) configured. Schema changes would currently require manual `db.drop_all()` and `db.create_all()` or direct SQL.

## 4. Project-Specific Conventions

*   **OAuth Manual Configuration**: Both Microsoft and Google OAuth providers are registered with `Authlib` using full manual configuration, including `authorize_url`, `access_token_url`, `userinfo_endpoint`, and `jwks_uri`.
*   **Nonce Validation**: Nonce values are generated and stored in the Flask session during the OAuth authorization request and validated upon callback to mitigate CSRF attacks.
*   **Environment-driven Configuration**: All sensitive credentials and configuration parameters are expected to be provided via environment variables, loaded using `python-dotenv`.

## 5. Key Files and Directories

*   `app.py`: Main application logic.
*   `requirements.txt`: Python dependencies.
*   `Dockerfile`: Docker image definition for the Flask app.
*   `docker-compose.yml`: Docker Compose orchestration file.
*   `entrypoint.sh`: Container startup script.
*   `templates/`: HTML templates.
*   `.env`: (Expected) Environment variables.
*   `nginx/nginx.conf`: (Expected, based on `docker-compose.yml`) Nginx configuration for reverse proxy.
