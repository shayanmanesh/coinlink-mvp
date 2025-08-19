FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY backend backend/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the application
CMD python -m uvicorn backend.api.main_production:app --host 0.0.0.0 --port ${PORT:-8000}