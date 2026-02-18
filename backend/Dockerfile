FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY rag/download_model.py .
RUN python download_model.py

COPY . .

EXPOSE 8080
ENV FASTEMBED_CACHE_PATH=/app/fastembed_cache
CMD exec uvicorn server:app --host 0.0.0.0 --port $PORT
