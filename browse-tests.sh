#!/usr/bin/env bash

export DJANGO_SETTINGS_MODULE=tests.settings

if [ "$1" ]; then
  addrport=$1
else
  addrport=8000
fi

django-admin runserver --pythonpath . "$addrport"
