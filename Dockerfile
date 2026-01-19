FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl openssh-client && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/$(dpkg --print-architecture)/kubectl" && \
    chmod +x kubectl && mv kubectl /usr/local/bin/ && \
    pip install --no-cache-dir paramiko && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server.py .

EXPOSE 3000

CMD ["python3", "server.py"]
