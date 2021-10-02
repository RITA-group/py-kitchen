FROM python:3.9-alpine

RUN apk add --no-cache \
    build-base \
    bash \
    linux-headers && \
    pip3 install --upgrade pip


# Copy python requirements file
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Remove pip cache. We are not going to need it anymore
RUN rm -r /root/.cache

ENV PYTHONUNBUFFERED 1

# Setup cloud run credentials
ENV KEY_DIR='/keys'
RUN mkdir -p ${KEY_DIR}
ENV GOOGLE_APPLICATION_CREDENTIALS="${KEY_DIR}/service_account_key.json"
ARG _SERVICE_ACCOUNT_KEY
RUN echo ${_SERVICE_ACCOUNT_KEY} | base64 -d > ${GOOGLE_APPLICATION_CREDENTIALS}

# Add our application files
COPY ./cuisson /code
WORKDIR /code

EXPOSE 8080

CMD ["python3", "prod_server.py"]
