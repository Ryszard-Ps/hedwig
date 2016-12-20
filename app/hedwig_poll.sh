#!/bin/sh
exec python /home/app/hedwig/scripts/hedwigctl poll all --pidfile /home/app/hedwig/scripts/poll.pid --pause 15 --logfile /home/app/hedwig/scripts/poll.log
