FROM python:3.10

COPY ./requirements.txt /src/requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r /src/requirements.txt

COPY . /src

EXPOSE 5000

ENV MY_ENV=celery

WORKDIR src