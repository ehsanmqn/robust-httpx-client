FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV HOSTS="http://192.168.100.26:8000,http://192.168.100.26:8001,http://192.168.100.26:8002"

WORKDIR /robust-httpx-client

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
