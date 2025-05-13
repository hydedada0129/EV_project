#FROM docker/whalesay:latest
#LABEL Name=wordpressdocker Version=0.0.1
#RUN apt-get -y update && apt-get install -y fortunes
#CMD ["sh", "-c", "/usr/games/fortune -a | cowsay"]

FROM wordpress:latest

USER root

RUN apt-get update && apt-get install -y python3 python3-pip
COPY 'generate excel.py' /var/www/html/scripts/
RUN pip3 install mysql-connector-python

USER www-data

CMD ["apache2-foreground"]

