import json
import boto3
import urllib3
import os
from datetime import datetime

# Initialize AWS clients
ecs_client = boto3.client('ecs')
cloudwatch = boto3.client('cloudwatch')
http = urllib3.PoolManager()

# Environment variables
CLUSTER_NAME = os.environ.get('CLUSTER_NAME', 'sample-app-cluster')
SERVICE_NAME = os.environ.get('SERVICE_NAME', 'sample-app-service')
HEALTH_ENDPOINT = os.environ.get('HEALTH_ENDPOINT', '/health')

def lambda_handler(event, context):
    """
    Performs health checks on ECS service and publishes metrics to CloudWatch
    """
    try:
        # Get ECS service details
        service_response = ecs_client.describe_services(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME]
        )
        
        if not service_response['services']:
            return create_response(500, 'Service not found')
        
        service = service_response['services'][0]
        
        # Get task ARNs for the service
        tasks_response = ecs_client.list_tasks(
            cluster=CLUSTER_NAME,
            serviceName=SERVICE_NAME,
            desiredStatus='RUNNING'
        )
        
        if not tasks_response['taskArns']:
            publish_metric('HealthCheckStatus', 0)
            return create_response(500, 'No running tasks found')
        
        # Describe tasks to get network details
        tasks_detail = ecs_client.describe_tasks(
            cluster=CLUSTER_NAME,
            tasks=tasks_response['taskArns']
        )
        
        health_status = check_task_health(tasks_detail['tasks'])
        
        # Publish metrics to CloudWatch
        publish_metric('HealthCheckStatus', 1 if health_status['healthy'] else 0)
        publish_metric('ResponseTime', health_status['avg_response_time'])
        publish_metric('HealthyTasks', health_status['healthy_count'])
        publish_metric('TotalTasks', health_status['total_count'])
        
        return create_response(
            200 if health_status['healthy'] else 500,
            f"Health check completed: {health_status['healthy_count']}/{health_status['total_count']} tasks healthy"
        )
        
    except Exception as e:
        print(f"Error during health check: {str(e)}")
        publish_metric('HealthCheckStatus', 0)
        return create_response(500, f"Health check failed: {str(e)}")

def check_task_health(tasks):
    """
    Checks health of all running tasks
    """
    healthy_count = 0
    total_count = len(tasks)
    response_times = []
    
    for task in tasks:
        # Get task IP address
        for attachment in task.get('attachments', []):
            if attachment['type'] == 'ElasticNetworkInterface':
                for detail in attachment['details']:
                    if detail['name'] == 'privateIPv4Address':
                        ip_address = detail['value']
                        
                        # Perform health check
                        try:
                            health_url = f"http://{ip_address}:5000{HEALTH_ENDPOINT}"
                            response = http.request('GET', health_url, timeout=3.0)
                            
                            if response.status == 200:
                                healthy_count += 1
                                response_times.append(response.duration if hasattr(response, 'duration') else 0)
                        except Exception as e:
                            print(f"Health check failed for {ip_address}: {str(e)}")
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    return {
        'healthy': healthy_count == total_count and total_count > 0,
        'healthy_count': healthy_count,
        'total_count': total_count,
        'avg_response_time': avg_response_time
    }

def publish_metric(metric_name, value):
    """
    Publishes custom metric to CloudWatch
    """
    try:
        cloudwatch.put_metric_data(
            Namespace='CustomApp/Health',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    except Exception as e:
        print(f"Failed to publish metric {metric_name}: {str(e)}")

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
