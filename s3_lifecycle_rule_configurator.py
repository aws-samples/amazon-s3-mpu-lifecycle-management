"""
@author: @healbert
@date: 2023-12-18

This script manages S3 bucket lifecycle rules, automating the application of specific configurations to S3 buckets.
It allows users to append lifecycle rules to existing buckets, ensuring modularity and ease of use without creating
IAM roles or attaching policies.
"""
from typing import Iterable

import boto3


def list_buckets(s3_client: boto3.client) -> dict[str, list]:
    """
    Lists buckets using an S3 client.

    :param s3_client: The S3 client.
    :type s3_client: boto3.client
    :return: List of bucket names.
    :rtype: dict[str, list]
    """
    # Get the list of bucket names and their regions
    names = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
    regions = [s3_client.get_bucket_location(Bucket=b)['LocationConstraint'] or 'us-east-1' for b in names]

    # Construct a dictionary mapping the buckets for each region
    buckets = {}
    for region in set(regions):
        buckets[region] = [name for i, name in enumerate(names) if regions[i] == region]

    return buckets


def is_region_opt_in(account_client: boto3.client, region: str) -> bool:
    """
    Determine whether the given region is opt-in

    :param account_client: The account client.
    :type account_client: boto3.client
    :param region: The iterable with the regions to check.
    :type region: Iterable
    :return: Flag indicating whether the region is opt-in
    :rtype: bool
    """
    status = account_client.get_region_opt_status(RegionName=region).get('RegionOptStatus', 'ENABLED')
    return status != 'ENABLED_BY_DEFAULT'


def get_current_lifecycle(s3_client: boto3.client, bucket_name: str) -> list[dict]:
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
    # Add the policy if its ID is not already present in the bucket rules
    if any([new_lifecycle_rule['ID'] == rule['ID'] for rule in current_rules]):
        print(f"Policy '{new_lifecycle_rule['ID']}' already exists in bucket '{bucket_name}'. No action taken.")
    else:
        current_rules.append(new_lifecycle_rule)
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={'Rules': current_rules}
        )
        print(f"Appended new lifecycle rule to bucket {bucket_name}")


def main():
    """
    Orchestrates the setup of S3 bucket lifecycle rules.
    """
    global_s3_client = boto3.client('s3')
    account_client = boto3.client('account')
    new_lifecycle_rule = {
        "ID": "delete-incomplete-mpu-7days",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
    }
    buckets = list_buckets(global_s3_client)

    for region, bucket_names in buckets.items():
        # Opt-in regions require us to use regional endpoints
        # We'll use the global one with the rest of regions for efficiency
        s3_client = global_s3_client
        if is_region_opt_in(account_client, region):
            s3_client = boto3.client('s3', region_name=region)

        for bucket_name in bucket_names:
            current_rules = get_current_lifecycle(s3_client, bucket_name)

            # Add the multipart-related rule if not already present
            if any(['AbortIncompleteMultipartUpload' in rule for rule in current_rules]):
                print(f"Bucket '{bucket_name}' already has a policy to delete incomplete multipart uploads.")
            else:
                # No existing policy found, add the new lifecycle rule
                check_and_append_lifecycle_rule(s3_client, bucket_name, current_rules, new_lifecycle_rule)

    print("Script completed successfully.")


if __name__ == "__main__":
    main()
