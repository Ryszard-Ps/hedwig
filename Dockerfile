FROM python:2.7.12
MAINTAINER sezzhltd@gmail.com

EXPOSE 5000
RUN apt-get update && apt-get install -y ghostscript
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY ./dev_requirements.txt /usr/src/app/dev_requirements.txt
RUN pip install --editable /usr/src/app
RUN pip install -r /usr/src/app/dev_requirements.txt
RUN pip install --user healpy
COPY . /usr/src/app

CMD ["python", "/usr/src/app/scripts/hedwigctl", "test_server"]
