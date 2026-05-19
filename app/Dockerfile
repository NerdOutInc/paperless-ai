FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user with writable home directory for model cache
RUN useradd -r -m -s /bin/false appuser && \
    chmod 700 /home/appuser

# Point all model/cache env vars at appuser's home so the pre-download
# lands there and runtime reads/writes go to the same place.
ENV HF_HOME=/home/appuser/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/sentence_transformers

# Pre-download embedding model during build (80MB), then hand
# the entire home tree to appuser so runtime can write lock/meta files.
ARG EMBEDDING_MODEL=all-MiniLM-L6-v2
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')" && \
    chown -R appuser:appuser /home/appuser
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL}

COPY *.py .
COPY static ./static
COPY search_pages ./search_pages

USER appuser

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

CMD ["python", "main.py"]
