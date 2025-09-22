import boto3
import json
import tarfile
from sagemaker.huggingface import HuggingFaceModel
import sagemaker
import time

def deploy_with_correct_path():
    region = 'us-east-1'
    session = boto3.Session(region_name=region)
    sagemaker_session = sagemaker.Session(boto_session=session)
    
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    current_arn = identity['Arn']
    role_name = current_arn.split('/')[1]
    account_id = identity['Account']
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    
    bucket_name = "grc-compliance-data-1756738456"
    s3 = session.client('s3')
    
    # Upload model to the expected path
    print("Creating and uploading model to correct path...")
    
    with tarfile.open("outputs/compliance-final.tar.gz", "w:gz") as tar:
        tar.add("outputs/compliance-tinyllama-lora/final", arcname=".")
    
    # Upload to demo-model folder with today's date
    s3_key = "demo-model/compliance-20250901.tar.gz"
    model_data = f"s3://{bucket_name}/{s3_key}"
    
    s3.upload_file("outputs/compliance-final.tar.gz", bucket_name, s3_key)
    print(f"Model uploaded to: {model_data}")
    
    # Deploy with HuggingFace
    huggingface_model = HuggingFaceModel(
        model_data=model_data,
        role=role_arn,
        transformers_version='4.26.0',
        pytorch_version='1.13.1',
        py_version='py39',
        sagemaker_session=sagemaker_session
    )
    
    endpoint_name = f"grc-compliance-working-{int(time.time())}"
    
    print(f"Deploying endpoint: {endpoint_name}")
    
    predictor = huggingface_model.deploy(
        initial_instance_count=1,
        instance_type='ml.t2.medium',
        endpoint_name=endpoint_name,
        wait=False
    )
    
    deployment_info = {
        "endpoint_name": endpoint_name,
        "model_data": model_data,
        "status": "deploying",
        "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('outputs/sagemaker_working.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"Deployment initiated: {endpoint_name}")
    print("Status: Creating endpoint (8-12 minutes)")

if __name__ == "__main__":
    deploy_with_correct_path()
