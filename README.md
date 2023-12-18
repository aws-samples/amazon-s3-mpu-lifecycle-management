# S3 Bucket Lifecycle Rule Configurator

This sample code Python script enables the automation of S3 bucket lifecycle rule configurations, particularly focusing on the automatic deletion of incomplete multipart uploads after a specified period. 

## Overview

The script streamlines the process of managing S3 bucket lifecycle rules without creating IAM roles or attaching policies. It iterates through the existing buckets in the specified AWS account, appends a defined lifecycle rule to each bucket, and ensures the application of specific configurations for managing incomplete multipart uploads.

## Features

- Automates the addition of lifecycle rules to existing S3 buckets.
- Deletes incomplete multipart uploads based on a user-defined rule.
- Streamlines configuration without the need for IAM roles or attached policies.

## Requirements

- Python 3.x
- AWS account credentials with necessary permissions
- Boto3 library

## Usage

1. Ensure you have Python 3.x installed.
2. Install the required libraries by running `pip install boto3` in your terminal.
3. Configure your AWS credentials using `aws configure`.
4. Run the script by executing `python s3_lifecycle_rule_configurator.py`.
5. Review the output log for details on applied lifecycle rules.

## Example

```bash
python s3_lifecycle_rule_configurator.py
```

## Script Output

Upon running the script, you'll see output similar to the following:

```bash
python3 s3_lifecycle_rule_configurator.py

Bucket 'bucket-1' already has a policy to delete incomplete multipart uploads.
Bucket 'bucket-2' already has a policy to delete incomplete multipart uploads.
Bucket 'bucket-3' already has a policy to delete incomplete multipart uploads.
Bucket 'bucket-4' already has a policy to delete incomplete multipart uploads.
Bucket 'bucket-5' already has a policy to delete incomplete multipart uploads.
Bucket 'bucket-6' already has a policy to delete incomplete multipart uploads.
...
Appended new lifecycle rule to bucket 'new-bucket-1'
Appended new lifecycle rule to bucket 'new-bucket-2'
Appended new lifecycle rule to bucket 'new-bucket-3'
Appended new lifecycle rule to bucket 'new-bucket-4'
Script completed successfully.
```