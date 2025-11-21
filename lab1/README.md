# PR Lab 1 – HTTP File Server (Sockets + Docker)

## The Task

Implement an HTTP File server using **raw TCP sockets** that:
- Handles one HTTP request at a time.
- Serves files from a chosen directory (`.html`, `.png`, `.pdf`).
- Returns a **404 custom page** for missing or unsupported files.
- Provides directory listings for nested folders.
- Runs inside **Docker** using **Docker Compose**.
- Includes a simple **Python client** for testing.

## Overview

This project implements a minimal HTTP file server using raw TCP sockets (no frameworks!), plus an optional HTTP client and Docker support for quick testing.

## Table of Contents

- [Overview](#overview)
- [Directory structure](#directory-structure)
- [Setup and Running](#setup-and-running)
  - [Using Docker Compose](#using-docker-compose)
  - [Running Manually (no Docker)](#running-manually-no-docker)
- [Making Requests](#making-requests)
  - [From Browser](#from-browser)
  - [Using the Client](#using-the-client)
- [Sample Content](#sample-content)
- [Screenshots](#screenshots)
- [Project Details](#project-details)

---

## Directory Structure

```
pr-lab1/
├─ server.py            # HTTP server implementation
├─ client.py            # HTTP client (optional)
├─ Dockerfile
├─ docker-compose.yml
├─ README.md
└─ content/
   ├─ index.html
   ├─ image.png
   ├─ sample.pdf
   └─ books/
      ├─ book1.pdf
      └─ cover.png
```

---

## Setup and Running

### Using Docker Compose (Recommended)

1. **Start server:**
   ```bash
   docker compose up --build
   # Server runs at: http://localhost:8080
   ```

2. **Open `http://localhost:8080/` in your browser** for a beautiful directory listing and file server UI.

**Server command inside container:**
```bash
python /app/server.py /data --host 0.0.0.0 --port 8080
```

### Running Manually (No Docker)

1. **Start server:**
   ```bash
   python3 server.py ./content --host 0.0.0.0 --port 8080
   ```

2. **Access server:**  
   Visit `http://localhost:8080` in your web browser.

---

## Making Requests

### From Browser

- **404 Example:**  
  `http://localhost:8080/nonexistent.file`

- **HTML File:**  
  `http://localhost:8080/index.html`

- **PDF File:**  
  `http://localhost:8080/sample.pdf`

- **PNG File:**  
  `http://localhost:8080/image.png`

- **Directory Browsing:**  
  `http://localhost:8080/books/`


---

### Using the Client

Fetch files or directories using the custom CLI client:
```bash
python3 client.py 127.0.0.1 8080 /path/in/server/ downloads_dir
```
**Examples:**
```bash
python3 client.py 127.0.0.1 8080 / downloads           # Fetches directory listing
python3 client.py 127.0.0.1 8080 /books/ downloads     # Fetches subdirectory
python3 client.py 127.0.0.1 8080 /image.png downloads  # Fetches image
python3 client.py 127.0.0.1 8080 /sample.pdf downloads # Fetches PDF
```
All files will be saved in the specified local `downloads_dir`.

---

## Sample Content

- `index.html` – Modern styled homepage (includes feature list and images)
- `image.png` – Example image resource
- `sample.pdf` – Example PDF file
- `books/` – Subdirectory containing more files (book1.pdf, cover.png)

---


## Screenshots
**Screenshot – directory listing:**
![image](screenshots/directory.png)
**Screenshot – opening a .pdf file:**
![image](screenshots/open-file.png)
**Screenshot – opening a .png file:**
![image](screenshots/open-photo.png)
**Screenshot – 404 page:**
![image](screenshots/404error.png)








> The project demonstrates practical understanding of TCP sockets, HTTP fundamentals, and Docker workflow.
