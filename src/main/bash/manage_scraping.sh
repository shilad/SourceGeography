#!/bin/bash

dir=$(cd $(dirname "$0") && pwd)

while true; do

    ec2-request-spot-instances ami-76817c1e \
        --region us-east-1  \
        --key shilads-aws-keypair \
        --user-data-file ${dir}/scrape_citations.sh \
        --instance-type t2.micro \
        --subnet subnet-18171730 \
        --iam-profile myRole \
        --associate-public-ip-address true \
        --price .02 \
        --instance-count 100 \
        --instance-type t1.micro \
        --valid-until $(date -uv +1H '+%Y-%m-%dT%H:%M:%SZ') ||
            { echo "spot instance request failed!" >&2; exit 1; }

    sleep 7050

    ids=$( aws ec2 describe-instances | grep InstanceId | sed -e 's/.*: "//' | sed -e 's/",//' | tr '\n' ' ')
    aws ec2 terminate-instances --instance-ids ${ids}

    sleep 300
done
