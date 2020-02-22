FROM python:3.7

COPY ./bot/requirements.txt requirements.txt

RUN pip install -r requirements.txt