# ⚡ Powerplant Coding Challenge API

This is a REST API that exposes the `/productionplan` endpoint to calculate an optimal power production plan based on provided fuel and powerplant data.

---

## Quick Start Guide

### Option 1: Run with Docker (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Pablo-Garcia-Perez/powerplant-coding-challenge
    cd powerplant-coding-challenge
    ```

2.  **Build and start the service**:
    ```bash
    docker-compose up --build
    ```

API will be available at: `http://localhost:8888`

---

### Option 2: Run with Python virtual environment

1.  **Create a virtual environment (optional but recommended)**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies (Linux-based)**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Launch the Django server in port 8888**:
    ```bash
    python src/manage.py runserver 8888
    ```

API will be available at: `http://127.0.0.1:8888`

---

## 📌 API Endpoint

### `POST /productionplan`

* **Method**: `POST`
* **Content-Type**: `application/json`

#### Example Usage (must be within the project main directory):

```bash
curl -X POST http://localhost:8888/productionplan -H "Content-Type: application/json" --data @example_payloads/payload3.json
curl -X POST http://127.0.0.1:8888/productionplan -H "Content-Type: application/json" --data @example_payloads/payload3.json

  ```