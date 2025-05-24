#!/usr/bin/env bash

#cd /home/oem/wordpress-docker
cd /home/ubuntu/wordpress-docker/wp-data/scripts
source venv/bin/activate

source aws_credentials.env
# echo "AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID"

# echo $VIRTUAL_ENV
/home/ubuntu/wordpress-docker/wp-data/scripts/venv/bin/python3 main.py
