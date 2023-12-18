"""
@author: @healbert
@date: 2023-12-18

This script manages S3 bucket lifecycle rules, automating the application of specific configurations to S3 buckets.
It allows users to append lifecycle rules to existing buckets, ensuring modularity and ease of use without creating
IAM roles or attaching policies.
"""
import boto3


def get_s3_client() -> boto3.client:
    """
    Creates an S3 client.

    :return: S3 client.
    :rtype: boto3.client
    """
    return boto3.client('s3')


def check_existing_mpu_rule(current_rules: list) -> bool:
    """
    Checks if an existing rule for incomplete multipart upload deletion is present.

    :param current_rules: Current lifecycle rules for the bucket.
    :type current_rules: list
    :return: True if a rule for deleting incomplete multipart uploads exists, False otherwise.
    :rtype: bool
    """
    for rule in current_rules:
        if 'AbortIncompleteMultipartUpload' in rule:
            return True
    return False


def list_buckets(s3_client: boto3.client):
    """
    Lists buckets using an S3 client.

    :param s3_client: The S3 client.
    :type s3_client: boto3.client
    :return: List of bucket names.
    :rtype: list
    """
    response = s3_client.list_buckets()
    return [bucket['Name'] for bucket in response['Buckets']]


def get_current_lifecycle(s3_client: boto3.client, bucket_name: str):
    """
    Gets the current lifecycle configuration for a bucket.

    :param s3_client: The S3 client with assumed role credentials.
    :type s3_client: boto3.client
    :param bucket_name: The name of the S3 bucket.
    :type bucket_name: str
    :return: Current lifecycle rules for the bucket.
    :rtype: list
    """
    try:
        current_lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        return current_lifecycle.get('Rules', [])
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            return []
        raise e


def check_and_append_lifecycle_rule(s3_client: boto3.client, bucket_name: str, current_rules: list,
                                    new_lifecycle_rule: dict) -> None:
    """
    Checks if a lifecycle rule exists and appends it to the bucket if not present.

    :param s3_client: The S3 client.
    :type s3_client: boto3.client
    :param bucket_name: The name of the S3 bucket.
    :type bucket_name: str
    :param current_rules: Current lifecycle rules for the bucket.
    :type current_rules: list
    :param new_lifecycle_rule: The new lifecycle rule to be appended.
    :type new_lifecycle_rule: dict
    """
    if rule_id_exists(current_rules, new_lifecycle_rule['ID']):
        print(f"Policy '{new_lifecycle_rule['ID']}' already exists in bucket '{bucket_name}'. No action taken.")
    else:
        current_rules.append(new_lifecycle_rule)
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={'Rules': current_rules}
        )
        print(f"Appended new lifecycle rule to bucket {bucket_name}")


def rule_id_exists(current_rules: list, new_rule_name: str) -> bool:
    """
    Checks if a rule ID already exists among the current rules.

    :param current_rules: List of current lifecycle rules.
    :type current_rules: list
    :param new_rule_name: The ID of the new rule to check for existence.
    :type new_rule_name: str
    :return: True if the rule ID already exists, False otherwise.
    :rtype: bool
    """
    for rule in current_rules:
        if new_rule_name == rule['ID']:
            return True
    return False


def main():
    """
    Orchestrates the setup of S3 bucket lifecycle rules.
    """
    s3_client = get_s3_client()
    new_lifecycle_rule = {
        "ID": "delete-incomplete-mpu-7days",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
    }
    buckets = list_buckets(s3_client)

    for bucket_name in buckets:
        current_rules = get_current_lifecycle(s3_client, bucket_name)

        # Check if an existing policy for incomplete multipart uploads deletion exists
        existing_mpu_policy = check_existing_mpu_rule(current_rules)
        if existing_mpu_policy:
            print(f"Bucket '{bucket_name}' already has a policy to delete incomplete multipart uploads.")
        else:
            # No existing policy found, add the new lifecycle rule
            check_and_append_lifecycle_rule(s3_client, bucket_name, current_rules, new_lifecycle_rule)

    print("Script completed successfully.")


if __name__ == "__main__":
    main()
