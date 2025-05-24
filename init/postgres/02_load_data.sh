#!/bin/bash
set -e

# Install required Python packages
pip install pandas==2.1.0 psycopg2-binary==2.9.9 python-dotenv==1.0.0

# Wait for PostgreSQL to be ready
until pg_isready -h localhost -p 5432 -U admin; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

# Run the data loading script
python /scripts/load_data.py 