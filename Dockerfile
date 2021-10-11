FROM python:3.9-alpine

RUN apk add --no-cache \
    build-base \
    bash \
    linux-headers

#RUN pip3 install grpcio

# Setup cloud run credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/keys/service_account_key.json"

# Copy python requirements file
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Remove pip cache. We are not going to need it anymore
RUN rm -r /root/.cache

ENV PYTHONUNBUFFERED 1


# Add our application files
COPY ./cuisson /code
WORKDIR /code

EXPOSE 8080

CMD ["python3", "prod_server.py"]
