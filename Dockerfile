# ==============================================================================
# SANADSQUAD EVIDENCE-FIRST V2 — SELF-CONTAINED OFFLINE DOCKERFILE
# Multi-stage/monolithic single-image deployment with bundled Ollama and qwen3.5:4b
# ==============================================================================

FROM python:3.12-slim-bookworm

LABEL maintainer="SanadSquad Senior Engineering Team" \
      version="2.0.0" \
      description="Self-contained, offline-capable SanadSquad Evidence-First V2 content pipeline with pre-baked local Ollama and qwen3.5:4b model." \
      license="Apache-2.0"

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    procps \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Copy pinned Ollama binary and shared runner libraries (verified via docker/bootstrap.sh)
COPY docker/bin/ollama /usr/local/bin/ollama
COPY docker/lib/ollama /usr/local/lib/ollama
RUN chmod +x /usr/local/bin/ollama && ldconfig

# Create unprivileged application user
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser -s /bin/bash appuser

# Set up application and model directories
WORKDIR /app
RUN mkdir -p /app/models /app/output /home/appuser/.ollama && \
    chown -R appuser:appuser /app /home/appuser

# Pre-bake qwen3.5:4b model weights and manifests into image layers
COPY docker/models /app/models
RUN chown -R appuser:appuser /app/models

# Install locked Python dependencies from requirements.txt during build
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create helper wrappers in /usr/local/bin
RUN printf '#!/bin/sh\nexec python -m pytest "$@"\n' > /usr/local/bin/pytest && \
    chmod +x /usr/local/bin/pytest

# Copy pipeline source code and configurations
COPY content_pipeline /app/content_pipeline
COPY source_snapshots /app/source_snapshots
COPY knowledge /app/knowledge
COPY instructions /app/instructions
COPY skills /app/skills
COPY schemas /app/schemas
COPY docs /app/docs
COPY tests /app/tests
COPY audit /app/audit
COPY brand-voice.md kb.json plan.json content-types.json pyproject.toml pytest.ini run_week.py run_piece.py /app/
COPY sources.json source.json marketing-rules.md writing-quality-rules.json audits.json company-contact.json /app/
COPY docker/entrypoint.sh /entrypoint.sh

# Fix ownership and permissions
RUN chmod +x /entrypoint.sh && \
    chown -R appuser:appuser /app /home/appuser

# Runtime environment configuration
USER appuser
ENV HOME=/home/appuser
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=127.0.0.1:11434
ENV OLLAMA_MODELS=/app/models
ENV OLLAMA_MODEL=qwen3.5:4b
ENV OUTPUT_BASE=/app/output

VOLUME ["/app/output"]

ENTRYPOINT ["/entrypoint.sh"]
