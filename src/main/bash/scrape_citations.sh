#!/bin/bash

set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1
echo BEGIN

PSQL_HOST=whois.clkcwsu8xzv8.us-east-1.rds.amazonaws.com
PSQL_USER=shilad
PSQL_PW=shiladsen
PSQL_DB=whois

yum update -y &&
yum install git postgresql-devel python-pip python-psycopg2 -y &&
pip install chardet &&
rm -rf /root/SourceGeography &&
cd /root &&
git clone https://github.com/shilad/SourceGeography &&
cd /root/SourceGeography/src/main/python &&
python ./download_urls.py $PSQL_HOST $PSQL_USER $PSQL_PW $PSQL_DB &&
shutdown -h now