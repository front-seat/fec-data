#!/bin/sh

trap gracefulshutdown SIGINT

gracefulshutdown() {
    echo "Gracefully shutting down..."
    kill -TERM 0
}

# Run the python server
export LITESTAR_APP=server.web:app
litestar run --reload --port 3333 &

# Run the vite frontend
npm run dev &

# Wait for all processes to finish
wait
