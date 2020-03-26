FROM python:3.7

COPY . /ovisbot

WORKDIR /ovisbot

RUN pip install -e .