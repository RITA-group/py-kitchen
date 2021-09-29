FROM python:3.9-alpine

RUN apk add --no-cache \
    build-base \
    bash \
    linux-headers && \
    pip3 install --upgrade pip


# At this point heavy lifting is done and everything below will build fast.

# Copy python requirements file
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Remove pip cache. We are not going to need it anymore
RUN rm -r /root/.cache

# Add our application files
#RUN mkdir /tmp/cuisson
#RUN mkdir /cuisson
COPY ./cuisson /cuisson
WORKDIR /cuisson

ENV PYTHONUNBUFFERED 1
EXPOSE 8080

CMD ["python3", "prod_server.py"]

