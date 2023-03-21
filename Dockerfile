FROM alpine:3.17

ARG PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /flow-app

# build-base provides gcc dependency
# py3-pandas necessary to prevent >1hr build time on rpi
RUN apk add --update --no-cache build-base python3-dev py3-pip py3-pandas

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
COPY bot-credentials.json .

# TODO get env variables
CMD ["python", "./main.py"]