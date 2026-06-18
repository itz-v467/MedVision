FROM python:3.11-slim AS builder

WORKDIR /build
COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && pip install --no-cache-dir --prefix=/install -r requirements-ml.txt

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HOME=/data/home
ENV HF_HOME=/data/cache/huggingface
ENV XDG_CACHE_HOME=/data/cache
ENV SENTENCE_TRANSFORMERS_HOME=/data/cache/sentence-transformers
ENV PADDLEX_HOME=/data/cache/paddlex

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r medvision && useradd -r -g medvision medvision

COPY --from=builder /install /usr/local
COPY backend /app/backend

RUN mkdir -p /app/backend/logs /data/uploads /data/home /data/cache/huggingface \
    /data/cache/sentence-transformers /data/cache/paddlex /data/models/imaging \
    && chown -R medvision:medvision /app /data

USER medvision

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')"

CMD ["uvicorn", "backend.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "5000", "--reload"]
