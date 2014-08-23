#!/bin/bash

dir=$(cd $(dirname "$0") && pwd)

NUM_INSTANCES=19

while true; do

    aws ec2 run-instances \
        --image-id ami-76817c1e \
        --count ${NUM_INSTANCES} \
        --key-name sources-keypair \
        --user-data file://${dir}/lookup_domains.sh \
        --instance-type t2.micro \
        --subnet-id subnet-18171730 \
        --instance-initiated-shutdown-behavior terminate \
        --associate-public-ip-address

    sleep 3450

    ids=$( aws ec2 describe-instances | grep InstanceId | sed -e 's/.*: "//' | sed -e 's/",//' | tr '\n' ' ')
    aws ec2 terminate-instances --instance-ids ${ids}

    sleep 300
done
