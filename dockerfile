# Dockerfile (FastAPI backend)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./malppot/requirements.txt ./malppot/requirements.txt
RUN pip install --no-cache-dir -r ./malppot/requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "malppot.main:app", "--host", "0.0.0.0", "--port", "8000"]