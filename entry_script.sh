#!/bin/sh
#*******************************************************************************
#entry_script.sh
#*******************************************************************************

#Purpose:
#This script allows running the AWS Lambda Runtime Interface Emulator when used
#locally, and otherwise runs normally on AWS Lambda. This was adapted from:
#https://docs.aws.amazon.com/lambda/latest/dg/images-test.html
#Author:
#AWS and Cedric H. David, 2018-2024


#*******************************************************************************
#Entry script
#*******************************************************************************
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
  exec /usr/bin/aws-lambda-rie /usr/bin/python3 -m awslambdaric $@
else
  exec /usr/bin/python3 -m awslambdaric $@
fi


#*******************************************************************************
#End
#*******************************************************************************
