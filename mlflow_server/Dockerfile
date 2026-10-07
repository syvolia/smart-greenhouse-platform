FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /mlflow

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Artifact destination inside the container; mounted to ./mlflow/artifacts on the host.
RUN mkdir -p /mlflow/artifacts

EXPOSE 5000

# The actual command is supplied by docker-compose (so env vars can drive
# the backend-store-uri without rebuilding the image).
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]