#!/bin/bash

dir=$(cd $(dirname "$0") && pwd)
REGIONS="us-east-1 us-west-1 us-west-2"

while true; do

    ec2-run-instances ami-76817c1e \
        --region us-east-1  \
        --key shilads-aws-keypair \
        --user-data-file ${dir}/scrape_citations.sh \
        --instance-type t2.micro \
        --subnet subnet-18171730 \
        --iam-profile myRole \
        --associate-public-ip-address true \
        --instance-initiated-shutdown-behavior terminate \
        --instance-count 95 \
        --instance-type t2.micro  ||
            { echo "spot instance request failed!" >&2; exit 1; }

    sleep 7050

    ids=$( aws ec2 describe-instances | grep InstanceId | sed -e 's/.*: "//' | sed -e 's/",//' | tr '\n' ' ')
    aws ec2 terminate-instances --instance-ids ${ids}

    sleep 300
done
