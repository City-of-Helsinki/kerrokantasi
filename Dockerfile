
FROM python:3.6

WORKDIR /usr/src/app

ENV ALLOWED_HOSTS [0.0.0.0]

RUN apt-get update && apt-get install -y libgdal20 libpq-dev

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "manage.py", "runserver", "0.0.0.0:8000"]
