FROM python:3.9-slim

WORKDIR /opt

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY *.py ./
