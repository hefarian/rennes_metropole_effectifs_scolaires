# Run tests with coverage using Docker
docker-compose --profile api run --rm api pytest tests/ --cov=api
