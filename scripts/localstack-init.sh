#!/bin/bash
# LocalStack initialization — create S3 bucket

awslocal s3 mb s3://vantict-data
echo "LocalStack initialized: S3 bucket created"
