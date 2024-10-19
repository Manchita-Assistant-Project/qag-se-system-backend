FROM python:3.9-slim

WORKDIR /code

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    musl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app /code/app
COPY ./files /code/files

COPY ./client_secrets.json /code/client_secrets.json
COPY ./credentials.json /code/credentials.json
COPY ./*.json /code/

EXPOSE 8000

# CMD ["sh", "-c", "python3 -u -m app.generator.loader && python3 -u -m app.generator.generator && uvicorn app.fastapi.main:app --host 0.0.0.0 --port 8000 --reload"]
# CMD ["sh", "-c", "python3 -u -m app.generator.generator && uvicorn app.fastapi.main:app --host 0.0.0.0 --port 8000 --reload"]
CMD ["sh", "-c", "uvicorn app.fastapi.main:app --host 0.0.0.0 --port 8000 --reload"]
# CMD ["sh", "-c", "python -u -m app.generator.pipeline"]
