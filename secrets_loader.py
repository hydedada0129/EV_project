# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "dropbox/refresh-token"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    
    # print("Using credentials from:", session.get_credentials())

    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    
    return secret
    
    # Your code goes here.
if __name__ == '__main__':
    secrets = get_secret()
    print(secrets)