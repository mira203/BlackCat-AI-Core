FROM python:3.10-slim

# HuggingFace Spaces runs as non-root user 1000
RUN useradd -m -u 1000 user
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY --chown=user . .

USER user

# HuggingFace Spaces exposes port 7860
EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
