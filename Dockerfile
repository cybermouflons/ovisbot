FROM python:3.7

COPY . /ovisbot

WORKDIR /ovisbot

RUN pip install pipenv
RUN pipenv install -e .