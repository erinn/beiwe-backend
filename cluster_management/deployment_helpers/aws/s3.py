import json
from deployment_helpers.aws.boto_helpers import create_s3_client, create_s3_resource
from deployment_helpers.constants import get_global_config
from deployment_helpers.general_utils import random_alphanumeric_string, log

GLOBAL_CONFIGURATION = get_global_config()

def s3_create_bucket(bucket_name):
    kwargs = {}
    # If region is us-east-1, then we cannot send this argument, or else the create_bucket command will fail
    if GLOBAL_CONFIGURATION["AWS_REGION"] != 'us-east-1':
        kwargs = {'CreateBucketConfiguration': {'LocationConstraint': GLOBAL_CONFIGURATION["AWS_REGION"]}}
    s3_client = create_s3_client()
    s3_client.create_bucket(ACL='private', Bucket=bucket_name, **kwargs)

def block_public_access(bucket_name):
    '''
    Block all public access to the S3 bucket containing sensitive data.
    '''
    s3_client = create_s3_client()

    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'RestrictPublicBuckets': True,
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True
        }
    )

def s3_encrypt_bucket(bucket_name):
    '''
    Set the policy for the given bucket to enable encryption of data at rest.
    '''
    s3_client = create_s3_client()

    # Add default encryption of data.
    s3_client.put_bucket_encryption(Bucket=bucket_name,
                                    ServerSideEncryptionConfiguration={
                                        'Rules': [
                                            { 'ApplyServerSideEncryptionByDefault': {
                                                'SSEAlgorithm': 'aws:kms',
                                                }
                                            },
                                        ]
                                    })

def s3_require_tls(bucket_name):
    '''
    This enforces encryption of data in transit for any calls.
    '''

    s3_client = create_s3_client()

    # Policy that enforces the use of TLS/SSL for all actions.
    bucket_policy = {
        'Version': '2012-10-17',
        'Id': 'Policy1565726245376',
        'Statement': [
            {
                'Sid': 'Stmt1565726242462',
                'Effect': 'Deny',
                'Principal': '*',
                'Action': '*',
                'Resource': 'arn:aws:s3:::{}/*'.format(bucket_name),
                'Condition': {
                    'Bool': {
                        'aws:SecureTransport': 'false'
                    }
                }
            }
        ]
    }

    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))

def check_bucket_name_available(bucket_name):
    s3_resource = create_s3_resource()
    return s3_resource.Bucket(bucket_name) not in s3_resource.buckets.all()

def clean_eb_bucket_name(eb_environment_name):
    return eb_environment_name

def create_data_bucket(eb_environment_name):
    for i in range(10):
        name = "beiwe-data-{}-{}".format(eb_environment_name, random_alphanumeric_string(63))[:63].lower()
        log.info("checking availability of bucket name '%s'" % name)
        if check_bucket_name_available(name):
            s3_create_bucket(name)
            s3_encrypt_bucket(name)
            s3_require_tls(name)
            block_public_access(name)
            return name
    raise Exception("Was not able to construct a bucket name that is not in use.")
