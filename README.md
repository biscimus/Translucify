# Translucifer: A Translucent Log Generation Algorithm

### Using HPC

#### Sign-In/Out

-   Turn on the RWTH VPN (Cisco AnyConnect) with the username `am106666` and the Cisco AnyConnect password. You will need the IdM SelfService MFA key in Google Authenticator.
-   In Powershell, type `ssh -l am106666 login18-1.hpc.itc.rwth-aachen.de` to connect. Type in your RegApp password and your HPC SSH MFA key in Google Authenticator. You can connect to other logic nodes listed [here](https://help.itc.rwth-aachen.de/service/rhr4fjjutttf/article/fc0bcd64e4df4d06bac1e3d1fc473309/).
-   Type `exit` to stop the remote connection.

#### Running Jobs

## Introduction

This is a hybrid TypeScript + Python app that uses React as the frontend and Flask as the API backend.

## How It Works

The React frontend is mapped under `frontend/`.
The Python/Flask server is mapped under `backend/`.

On localhost, the rewrite will be made to the `127.0.0.1:5000` port, which is where the Flask server is running.

## Getting Started

For the frontend, install the dependencies:

```bash
npm install
# or
yarn
# or
pnpm install
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173) with your browser to see the result.

For the backend, run:

```
flask run --debug
```

to start the development server. The Flask server will be running on [http://127.0.0.1:5000](http://127.0.0.1:5000).
