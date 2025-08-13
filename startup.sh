#!/bin/bash
PORT=${PORT:-600}
echo "Starting app on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --timeout 600 app.server:app
