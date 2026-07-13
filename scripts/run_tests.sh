#!/bin/bash
set -e

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed."
    exit 1
fi

echo "Running tests with coverage inside docker..."
docker-compose --profile api run --rm api pytest tests/ --cov=api
