"""
Phoenix Pipeline - Sample Python Flask Application
A simple REST API demonstrating health checks, metrics, and deployment readiness
"""

from flask import Flask, jsonify, request
from datetime import datetime
import os
import logging
import socket
import psutil

# Initialize Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application metadata
APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
BUILD_ID = os.environ.get('BUILD_ID', 'local')
HOSTNAME = socket.gethostname()

# Application state
app_state = {
    'start_time': datetime.utcnow().isoformat(),
    'request_count': 0,
    'error_count': 0,
    'healthy': True
}


@app.route('/')
def home():
    """
    Home endpoint - Returns application information
    """
    app_state['request_count'] += 1
    
    return jsonify({
        'message': 'Phoenix Pipeline - Self-Healing CI/CD Platform',
        'status': 'running',
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'build_id': BUILD_ID,
        'hostname': HOSTNAME,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/health')
def health():
    """
    Health check endpoint - Used by ALB and Lambda health checks
    Returns 200 if healthy, 503 if unhealthy
    """
    app_state['request_count'] += 1
    
    if not app_state['healthy']:
        logger.warning("Health check failed - application marked as unhealthy")
        return jsonify({
            'status': 'unhealthy',
            'message': 'Application is not ready to serve traffic'
        }), 503
    
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': get_uptime(),
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'hostname': HOSTNAME,
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available // (1024 * 1024)
        },
        'metrics': {
            'total_requests': app_state['request_count'],
            'total_errors': app_state['error_count']
        }
    }
    
    logger.info(f"Health check passed - CPU: {cpu_percent}%, Memory: {memory.percent}%")
    return jsonify(health_data), 200


@app.route('/ready')
def readiness():
    """
    Readiness probe endpoint - Indicates if app is ready to receive traffic
    """
    app_state['request_count'] += 1
    
    # Check if application dependencies are available
    # In production, check database connections, cache availability, etc.
    
    if app_state['healthy']:
        return jsonify({
            'status': 'ready',
            'message': 'Application is ready to serve traffic',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'message': 'Application is starting up',
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@app.route('/metrics')
def metrics():
    """
    Metrics endpoint - Returns application metrics for monitoring
    """
    app_state['request_count'] += 1
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics_data = {
        'application': {
            'version': APP_VERSION,
            'environment': ENVIRONMENT,
            'uptime_seconds': get_uptime_seconds(),
            'total_requests': app_state['request_count'],
            'total_errors': app_state['error_count'],
            'error_rate': calculate_error_rate()
        },
        'system': {
            'hostname': HOSTNAME,
            'cpu_percent': cpu_percent,
            'cpu_count': psutil.cpu_count(),
            'memory': {
                'total_mb': memory.total // (1024 * 1024),
                'available_mb': memory.available // (1024 * 1024),
                'used_mb': memory.used // (1024 * 1024),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total // (1024 * 1024 * 1024),
                'used_gb': disk.used // (1024 * 1024 * 1024),
                'free_gb': disk.free // (1024 * 1024 * 1024),
                'percent': disk.percent
            }
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(metrics_data), 200


@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Sample API endpoint - Returns sample data
    """
    app_state['request_count'] += 1
    
    sample_data = {
        'id': 1,
        'name': 'Phoenix Pipeline',
        'description': 'Self-healing CI/CD platform with automated rollback',
        'features': [
            'Blue-green deployment',
            'Automated health checks',
            'Intelligent rollback',
            'Zero-downtime deployments',
            'Real-time monitoring'
        ],
        'status': 'active',
        'created_at': app_state['start_time'],
        'updated_at': datetime.utcnow().isoformat()
    }
    
    return jsonify(sample_data), 200


@app.route('/api/data', methods=['POST'])
def create_data():
    """
    Sample API endpoint - Creates new data
    """
    app_state['request_count'] += 1
    
    if not request.json:
        app_state['error_count'] += 1
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request body must be JSON'
        }), 400
    
    data = request.json
    
    response = {
        'message': 'Data created successfully',
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(response), 201


@app.route('/api/simulate-error')
def simulate_error():
    """
    Test endpoint - Simulates an error for testing rollback
    Useful for testing automated rollback functionality
    """
    app_state['request_count'] += 1
    app_state['error_count'] += 1
    
    logger.error("Simulated error triggered")
    
    return jsonify({
        'error': 'Simulated error',
        'message': 'This error is intentionally triggered for testing',
        'timestamp': datetime.utcnow().isoformat()
    }), 500


@app.route('/api/toggle-health', methods=['POST'])
def toggle_health():
    """
    Test endpoint - Toggles application health status
    Useful for testing health check and rollback mechanisms
    """
    app_state['request_count'] += 1
    app_state['healthy'] = not app_state['healthy']
    
    logger.warning(f"Application health toggled to: {app_state['healthy']}")
    
    return jsonify({
        'message': 'Health status toggled',
        'healthy': app_state['healthy'],
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/version')
def version():
    """
    Version endpoint - Returns application version information
    """
    app_state['request_count'] += 1
    
    version_info = {
        'version': APP_VERSION,
        'build_id': BUILD_ID,
        'environment': ENVIRONMENT,
        'hostname': HOSTNAME,
        'deployed_at': app_state['start_time'],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(version_info), 200


@app.errorhandler(404)
def not_found(error):
    """
    404 error handler
    """
    app_state['request_count'] += 1
    app_state['error_count'] += 1
    
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    500 error handler
    """
    app_state['error_count'] += 1
    
    logger.error(f"Internal server error: {str(error)}")
    
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.utcnow().isoformat()
    }), 500


# Helper functions
def get_uptime():
    """
    Calculate application uptime in human-readable format
    """
    start = datetime.fromisoformat(app_state['start_time'])
    uptime_delta = datetime.utcnow() - start
    
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{days}d {hours}h {minutes}m {seconds}s"


def get_uptime_seconds():
    """
    Calculate application uptime in seconds
    """
    start = datetime.fromisoformat(app_state['start_time'])
    uptime_delta = datetime.utcnow() - start
    return int(uptime_delta.total_seconds())


def calculate_error_rate():
    """
    Calculate error rate percentage
    """
    if app_state['request_count'] == 0:
        return 0.0
    
    return round((app_state['error_count'] / app_state['request_count']) * 100, 2)


# Application startup
if __name__ == '__main__':
    logger.info(f"Starting Phoenix Pipeline application")
    logger.info(f"Version: {APP_VERSION}")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Hostname: {HOSTNAME}")
    logger.info(f"Build ID: {BUILD_ID}")
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run Flask application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(ENVIRONMENT == 'development')
    )
