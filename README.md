# Translucify: A Translucent Log Generation Algorithm

## Introduction

This is a hybrid TypeScript + Python app that uses React as the frontend and Flask as the API backend.

## How It Works

The React frontend is mapped under `frontend/`.
The Python/Flask server is mapped under `backend/`.

On localhost, the rewrite will be made to the `127.0.0.1:5000` port, which is where the Flask server is running.

## Getting Started

### Frontend

For the frontend, install the dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) with your browser to see the result.

### Backend

For the backend Flask Application, run:

```
flask run --debug
```

to start the development server. The Flask server will be running on [http://127.0.0.1:5000](http://127.0.0.1:5000).

To start the Celery broker, first run the Redis queue in the Docker container:

```
docker run -d -p 6379:6379 redis
```

Then, execute the following command to start Celery from the `backend/` folder.

```
celery -A app.celery worker --loglevel INFO
```

### Connecting with the PADS remote microservice

Connect to the RWTH VPN using Cisco AnyConnect. Then, run the `ssh-forward.sh` shell file to set up a bidirectional SSH connection.

In the remote server, run the shell file `start_application_terminals.sh` in the `/projects/ba/Translucify-Transformer-Service` directory.
