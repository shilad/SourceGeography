#!/bin/sh

PSQL_HOST=whois.clkcwsu8xzv8.us-east-1.rds.amazonaws.com
PSQL_USER=shilad
PSQL_PW=shiladsen
PSQL_DB=whois

yum update -y &&
yum install git python-pip python-psycopg2 -y &&
rm -rf /root/SourceGeography &&
git clone https://github.com/shilad/SourceGeography &&
cd /root/SourceGeography/src/main/python &&
python ./create_whois_db.py $PSQL_HOST $PSQL_USER $PSQL_PW $PSQL_DB &&
shutdown -h now