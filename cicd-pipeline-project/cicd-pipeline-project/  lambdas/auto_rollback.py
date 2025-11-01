import json
import boto3
import os
from datetime import datetime

# Initialize AWS clients
ecs_client = boto3.client('ecs')
codedeploy_client = boto3.client('codedeploy')
sns_client = boto3.client('sns')

# Environment variables
CLUSTER_NAME = os.environ.get('CLUSTER_NAME', 'sample-app-cluster')
SERVICE_NAME = os.environ.get('SERVICE_NAME', 'sample-app-service')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    """
    Triggers automatic rollback when CloudWatch alarm is triggered
    """
    try:
        print(f"Rollback triggered by event: {json.dumps(event)}")
        
        # Parse CloudWatch alarm event
        alarm_data = parse_alarm_event(event)
        
        if not alarm_data:
            return create_response(400, 'Invalid alarm event')
        
        # Get current deployment information
        service_info = get_service_deployment_info()
        
        if not service_info:
            send_notification('Rollback Failed', 'Unable to retrieve service deployment information')
            return create_response(500, 'Failed to get service info')
        
        # Perform rollback
        rollback_result = perform_rollback(service_info)
        
        if rollback_result['success']:
            message = f"Rollback completed successfully. Reverted to task definition: {rollback_result['previous_task_def']}"
            send_notification('Rollback Successful', message)
            return create_response(200, message)
        else:
            message = f"Rollback failed: {rollback_result['error']}"
            send_notification('Rollback Failed', message)
            return create_response(500, message)
            
    except Exception as e:
        error_message = f"Critical error during rollback: {str(e)}"
        print(error_message)
        send_notification('Rollback Critical Error', error_message)
        return create_response(500, error_message)

def parse_alarm_event(event):
    """
    Parses CloudWatch alarm event to extract alarm details
    """
    try:
        if 'Records' in event and len(event['Records']) > 0:
            sns_message = json.loads(event['Records'][0]['Sns']['Message'])
            return {
                'alarm_name': sns_message['AlarmName'],
                'new_state': sns_message['NewStateValue'],
                'reason': sns_message['NewStateReason'],
                'timestamp': sns_message['StateChangeTime']
            }
        return None
    except Exception as e:
        print(f"Error parsing alarm event: {str(e)}")
        return None

def get_service_deployment_info():
    """
    Retrieves current service deployment information
    """
    try:
        response = ecs_client.describe_services(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME]
        )
        
        if not response['services']:
            return None
        
        service = response['services'][0]
        deployments = service.get('deployments', [])
        
        # Get current and previous task definitions
        current_task_def = service['taskDefinition']
        
        # Get task definition history
        task_def_response = ecs_client.describe_task_definition(
            taskDefinition=current_task_def
        )
        
        current_revision = task_def_response['taskDefinition']['revision']
        task_def_family = task_def_response['taskDefinition']['family']
        
        previous_revision = max(1, current_revision - 1)
        previous_task_def = f"{task_def_family}:{previous_revision}"
        
        return {
            'current_task_def': current_task_def,
            'previous_task_def': previous_task_def,
            'deployments': deployments
        }
        
    except Exception as e:
        print(f"Error getting service info: {str(e)}")
        return None

def perform_rollback(service_info):
    """
    Performs the actual rollback by updating ECS service
    """
    try:
        previous_task_def = service_info['previous_task_def']
        
        print(f"Rolling back to task definition: {previous_task_def}")
        
        # Update ECS service with previous task definition
        response = ecs_client.update_service(
            cluster=CLUSTER_NAME,
            service=SERVICE_NAME,
            taskDefinition=previous_task_def,
            forceNewDeployment=True
        )
        
        return {
            'success': True,
            'previous_task_def': previous_task_def,
            'deployment_id': response['service']['deployments'][0]['id']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def send_notification(subject, message):
    """
    Sends SNS notification about rollback status
    """
    if not SNS_TOPIC_ARN:
        print("SNS Topic ARN not configured")
        return
    
    try:
        full_message = f"""
{subject}

{message}

Cluster: {CLUSTER_NAME}
Service: {SERVICE_NAME}
Timestamp: {datetime.utcnow().isoformat()}

This is an automated notification from the CI/CD pipeline rollback system.
"""
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=full_message
        )
        
        print(f"Notification sent: {subject}")
        
    except Exception as e:
        print(f"Failed to send SNS notification: {str(e)}")

def create_response(status_code, message):
    """
    Creates standardized Lambda response
    """
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
```

## lambdas/requirements.txt
```
boto3>=1.26.0
urllib3>=1.26.0
