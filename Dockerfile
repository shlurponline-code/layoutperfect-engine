FROM python:3.12-slim
RUN apt-get update && apt-get install -y fonts-freefont-ttf && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-8000}
