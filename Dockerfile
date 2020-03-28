# test THIS code using docker
FROM python:3.7 AS test-stage
WORKDIR /app/kitir
RUN pip install pytest pytz requests
COPY kitir /app/kitir
RUN pytest

# creates a new image from python which installs the latest released kitir package from PyPi (not from code)
FROM python:3.7 as deploy-stage
RUN pip install kitir