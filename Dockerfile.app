FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Waiting for PostgreSQL..."\n\
while ! nc -z $DB_HOST $DB_PORT; do\n\
  sleep 0.1\n\
done\n\
echo "PostgreSQL started"\n\
\n\
echo "Creating Debezium connector..."\n\
CONNECTOR_CONFIG=$(cat /app/debezium/postgres-connector.json | \\\n\
  sed "s/\${DB_HOST}/$DB_HOST/g" | \\\n\
  sed "s/\${DB_PORT}/$DB_PORT/g" | \\\n\
  sed "s/\${DB_USER}/$DB_USER/g" | \\\n\
  sed "s/\${DB_PASSWORD}/$DB_PASSWORD/g" | \\\n\
  sed "s/\${DB_NAME}/$DB_NAME/g")\n\
\n\
curl -X POST -H "Content-Type: application/json" \\\n\
  --data "$CONNECTOR_CONFIG" \\\n\
  http://debezium:8083/connectors\n\
\n\
echo "Running data seeding script..."\n\
python /app/scripts/seed_data.py\n\
\n\
echo "Starting FastAPI application..."\n\
exec uvicorn apps.main:app --host 0.0.0.0 --port 8000 --reload\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run entrypoint script
CMD ["/app/entrypoint.sh"] 