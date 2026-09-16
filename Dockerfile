FROM python:3.12-slim
RUN apt-get update && apt-get install -y fonts-freefont-ttf fonts-noto-cjk fonts-wqy-zenhei fonts-arphic-uming fonts-wqy-zenhei fonts-arphic-uming && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
ENTRYPOINT ["python", "api_server.py"]
