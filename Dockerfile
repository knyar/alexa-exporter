FROM python:3.9-alpine
RUN pip install pipenv

RUN addgroup -S exporter && adduser -h /home/exporter -S exporter -G exporter

WORKDIR /app
ADD . .

RUN pipenv install --system

EXPOSE 5000
USER exporter
CMD python3 app.py
