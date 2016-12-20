# Use phusion/passenger-full as base image. To make your builds reproducible, make
# sure you lock down to a specific version, not to `latest`!
# See https://github.com/phusion/passenger-docker/blob/master/Changelog.md for
# a list of version numbers.
# FROM phusion/passenger-full:0.9.19
# FROM phusion/baseimage:0.9.19
# Or, instead of the 'full' variant, use one of these:
FROM phusion/passenger-customizable:0.9.19
MAINTAINER sezzhltd@gmail.com

# Set correct environment variables.
ENV HOME=/root

# Use baseimage-docker's init process.
CMD ["/sbin/my_init"]

# If you're using the 'customizable' variant, you need to explicitly opt-in
# for features. Uncomment the features you want:
#
#   Build system and git.
RUN /pd_build/utilities.sh

#   Python support.
RUN /pd_build/python.sh

# ...app build instructions...

EXPOSE 5000
EXPOSE 5678
ENV PYTHONPATH=/home/app/hedwig/lib \
  HEDWIG_DIR=/home/app/hedwig \
  TZ='Etc/UTC'

RUN mkdir -p /home/app/hedwig
WORKDIR /home/app/hedwig

# necessary dependencies from apt-get
RUN apt-get update && apt-get install -y \
apt-utils \
python-dev \
libmysqlclient-dev \
ghostscript \
graphviz \
python-pip

COPY . /home/app/hedwig

RUN pip install --upgrade pip \
  && pip install http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#md5=3df394d89300db95163f17c843ef49df \
  && pip install -r /home/app/hedwig/requirements_server.txt \
  && pip install --editable /home/app/hedwig

COPY ./cron-task/hedwig-cron /etc/cron.d/hedwig-cron
COPY ./app/hedwig.sh /etc/service/app/run
COPY ./app/hedwig_poll.sh /etc/service/app-poll/run

RUN chmod 644 /etc/service/app/run \
  && chmod +x /etc/service/app/run \
  && chmod 644 /etc/service/app-poll/run \
  && chmod +x /etc/service/app-poll/run \
  && chmod 644 /etc/cron.d/hedwig-cron \
  && touch /var/log/cron.log

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# CMD ["python", "/usr/src/app/scripts/hedwigctl", "test_server"]
