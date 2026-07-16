import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

class KiroAWSHelper:
    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.profile = os.getenv('AWS_PROFILE', 'default')
        self.use_localstack = os.getenv('USE_LOCALSTACK', 'false').lower() == 'true'
        
        # Use Kiro's credential system
        self.kiro_config_path = os.path.join('.kiro', 'kiro-aws-config.json')
        self._load_kiro_config()
        
        if self.use_localstack:
            self.endpoint_url = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
        else:
            self.endpoint_url = None
    
    def _load_kiro_config(self):
        if os.path.exists(self.kiro_config_path):
            with open(self.kiro_config_path, 'r') as f:
                config = json.load(f)
                kiro_aws = config.get('kiro', {}).get('aws', {})
                self.region = kiro_aws.get('region', self.region)
                self.profile = kiro_aws.get('profile', self.profile)
    
    def get_session(self):
        return boto3.Session(profile_name=self.profile)
    
    def get_client(self, service_name):
        session = self.get_session()
        return session.client(
            service_name,
            region_name=self.region,
            endpoint_url=self.endpoint_url
        )
    
    def get_resource(self, service_name):
        session = self.get_session()
        return session.resource(
            service_name,
            region_name=self.region,
            endpoint_url=self.endpoint_url
        )

# Quick setup function
def setup_aws():
    return KiroAWSHelper()