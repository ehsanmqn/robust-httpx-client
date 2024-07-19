FROM python:3.10-slim
ENV PYTHONUNBUFFERED 1

RUN mkdir /robust-httpx-client

WORKDIR /robust-httpx-client

ADD . /robust-httpx-client

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
