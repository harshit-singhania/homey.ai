#!/bin/bash

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting Homey.ai locally..."

# Ensure Prisma client is generated (just in case)
prisma generate

# Run the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
