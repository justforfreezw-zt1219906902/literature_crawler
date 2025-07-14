# Paper Crawler

This project is a Flask-based web application designed to crawl and process scientific datasets from various online sources. It uses a modular architecture to support different crawling protocols and includes functionalities for data cleaning, storage, and task management.

## Features

- **Web Crawling:** Utilizes Selenium to scrape data from scientific journals and websites.
- **Data Processing:** Cleans and processes crawled data into a structured format.
- **Database Support:** Uses SQLAlchemy and Flask-Migrate to manage a PostgreSQL database.
- **Cloud Storage:** Integrates with Aliyun, Azure, and Google Cloud for flexible file storage.
- **Task Management:** Manages crawling tasks with Celery for asynchronous processing.
- **Docker Support:** Includes a Dockerfile for easy containerization and deployment.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd datasets-crawler
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    - Copy the `.env.template` file to a new file named `.env`.
    - Update the `.env` file with your configuration, including database credentials and cloud storage keys.

## Usage

1.  **Initialize the database:**
    ```bash
    flask db upgrade
    ```

2.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The application will be accessible at `http://localhost:9001`.

## Deployment

This project can be deployed using Docker.

1.  **Build the Docker image:**
    ```bash
    docker build -t datasets-crawler .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 9001:9001 --env-file .env datasets-crawler
    ```

The `entrypoint.sh` script will handle database migrations and start the Gunicorn server.

## Dependencies

- **Flask:** Web framework
- **Selenium:** Web crawling
- **SQLAlchemy:** Database ORM
- **Celery:** Asynchronous task queue
- **Pandas:** Data manipulation
- **BeautifulSoup4:** HTML parsing
- **Gunicorn:** WSGI HTTP Server
- **Psycopg2:** PostgreSQL adapter for Python
- **Cloud Storage Libraries:** `oss2`, `azure-storage-blob`, `google-cloud-storage`
