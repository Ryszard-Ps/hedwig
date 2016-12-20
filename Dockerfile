FROM python:2.7.12
MAINTAINER sezzhltd@gmail.com

EXPOSE 5000
EXPOSE 5678
ENV PYTHONPATH=/usr/src/app/lib
ENV HEDWIG_DIR=/usr/src/app
RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

# ghostscript
RUN apt-get update && apt-get install -y \
  apt-utils \
  python-dev \
  libmysqlclient-dev \
  ghostscript \
  graphviz \
  cron

COPY ./requirements_server.txt /usr/src/app/requirements_server.txt
# COPY ./cron-task/hedwig-cron /etc/cron.d/hedwig-cron
# COPY ./cron-task/hello-cron /etc/cron.d/hello-cron
COPY . /usr/src/app

RUN touch /var/log/cron.log
# RUN chmod 0644 /etc/cron.d/hello-cron
# RUN chmod 0644 /etc/cron.d/hedwig-cron
RUN pip install --upgrade pip \
  && pip install http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#md5=3df394d89300db95163f17c843ef49df \
  && pip install -r /usr/src/app/requirements_server.txt \
  && pip install --editable /usr/src/app

CMD ["python", "/usr/src/app/scripts/hedwigctl", "test_server"]
