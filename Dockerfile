FROM python:3.8

ARG TOKEN

ENV TOKEN=$TOKEN

WORKDIR /flow-app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY main.py .

# TODO get env variables
CMD ["python", "./main.py"]