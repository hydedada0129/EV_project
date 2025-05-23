#!/usr/bin/env bash

cd /home/oem/wordpress-docker

source .venv/bin/activate

source aws_credentials.env
# echo "AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID"

# echo $VIRTUAL_ENV
/home/oem/wordpress-docker/.venv/bin/python main.py
