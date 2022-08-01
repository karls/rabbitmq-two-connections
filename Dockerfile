FROM python:3.10.4-slim-bullseye

ENV POETRY_HOME=/tmp/poetry
ENV PATH=$POETRY_HOME/bin:$PATH
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install --no-install-recommends curl && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python - && \
    poetry config virtualenvs.create false

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root

COPY . .

ENTRYPOINT [ "python", "-W", "always::DeprecationWarning", "-m" ]
