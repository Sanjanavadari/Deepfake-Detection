FROM python:3.11-slim-bookworm

WORKDIR /app

# OpenCV headless runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt

# CPU-only PyTorch wheels via extra index (see requirements.txt header)
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY src/ /app/src/

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=/tmp/predictions.db

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
