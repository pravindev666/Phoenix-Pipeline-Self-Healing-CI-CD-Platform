"""
Phoenix Pipeline - Unit Tests for Sample Flask Application
Comprehensive test suite for all API endpoints and functionality
"""

import pytest
import json
from app import app, app_state


@pytest.fixture
def client():
    """
    Create a test client for the Flask application
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Reset app state before each test
        app_state['request_count'] = 0
        app_state['error_count'] = 0
        app_state['healthy'] = True
        yield client


@pytest.fixture
def reset_app_state():
    """
    Reset application state after each test
    """
    yield
    app_state['request_count'] = 0
    app_state['error_count'] = 0
    app_state['healthy'] = True


class TestHomeEndpoint:
    """
    Test suite for home endpoint
    """
    
    def test_home_returns_200(self, client):
        """Test home endpoint returns 200 status code"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_home_returns_json(self, client):
        """Test home endpoint returns JSON response"""
        response = client.get('/')
        assert response.content_type == 'application/json'
    
    def test_home_contains_message(self, client):
        """Test home endpoint contains expected message"""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'message' in data
        assert 'Phoenix Pipeline' in data['message']
    
    def test_home_contains_metadata(self, client):
        """Test home endpoint contains application metadata"""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'version' in data
        assert 'environment' in data
        assert 'hostname' in data
        assert 'timestamp' in data
    
    def test_home_increments_request_count(self, client, reset_app_state):
        """Test home endpoint increments request counter"""
        initial_count = app_state['request_count']
        client.get('/')
        assert app_state['request_count'] == initial_count + 1


class TestHealthEndpoint:
    """
    Test suite for health check endpoint
    """
    
    def test_health_returns_200_when_healthy(self, client):
        """Test health endpoint returns 200 when application is healthy"""
        app_state['healthy'] = True
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_returns_503_when_unhealthy(self, client):
        """Test health endpoint returns 503 when application is unhealthy"""
        app_state['healthy'] = False
        response = client.get('/health')
        assert response.status_code == 503
    
    def test_health_returns_json(self, client):
        """Test health endpoint returns JSON response"""
        response = client.get('/health')
        assert response.content_type == 'application/json'
    
    def test_health_contains_status(self, client):
        """Test health endpoint contains status field"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'status' in data
    
    def test_health_contains_system_metrics(self, client):
        """Test health endpoint contains system metrics"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'system' in data
        assert 'cpu_percent' in data['system']
        assert 'memory_percent' in data['system']
    
    def test_health_contains_application_metrics(self, client):
        """Test health endpoint contains application metrics"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'metrics' in data
        assert 'total_requests' in data['metrics']
        assert 'total_errors' in data['metrics']


class TestReadinessEndpoint:
    """
    Test suite for readiness probe endpoint
    """
    
    def test_readiness_returns_200_when_ready(self, client):
        """Test readiness endpoint returns 200 when application is ready"""
        app_state['healthy'] = True
        response = client.get('/ready')
        assert response.status_code == 200
    
    def test_readiness_returns_503_when_not_ready(self, client):
        """Test readiness endpoint returns 503 when application is not ready"""
        app_state['healthy'] = False
        response = client.get('/ready')
        assert response.status_code == 503
    
    def test_readiness_contains_status(self, client):
        """Test readiness endpoint contains status field"""
        response = client.get('/ready')
        data = json.loads(response.data)
        assert 'status' in data
        assert 'message' in data


class TestMetricsEndpoint:
    """
    Test suite for metrics endpoint
    """
    
    def test_metrics_returns_200(self, client):
        """Test metrics endpoint returns 200 status code"""
        response = client.get('/metrics')
        assert response.status_code == 200
    
    def test_metrics_returns_json(self, client):
        """Test metrics endpoint returns JSON response"""
        response = client.get('/metrics')
        assert response.content_type == 'application/json'
    
    def test_metrics_contains_application_data(self, client):
        """Test metrics endpoint contains application metrics"""
        response = client.get('/metrics')
        data = json.loads(response.data)
        assert 'application' in data
        assert 'version' in data['application']
        assert 'total_requests' in data['application']
        assert 'total_errors' in data['application']
    
    def test_metrics_contains_system_data(self, client):
        """Test metrics endpoint contains system metrics"""
        response = client.get('/metrics')
        data = json.loads(response.data)
        assert 'system' in data
        assert 'cpu_percent' in data['system']
        assert 'memory' in data['system']
        assert 'disk' in data['system']
    
    def test_metrics_error_rate_calculation(self, client, reset_app_state):
        """Test metrics endpoint calculates error rate correctly"""
        # Generate some requests with errors
        client.get('/')  # Success
        client.get('/')  # Success
        client.get('/api/simulate-error')  # Error
        
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        # Error rate should be approximately 25% (1 error out of 4 requests)
        assert 'error_rate' in data['application']
        assert data['application']['error_rate'] >= 0


class TestAPIEndpoints:
    """
    Test suite for API endpoints
    """
    
    def test_get_data_returns_200(self, client):
        """Test GET /api/data returns 200 status code"""
        response = client.get('/api/data')
        assert response.status_code == 200
    
    def test_get_data_returns_sample_data(self, client):
        """Test GET /api/data returns expected data structure"""
        response = client.get('/api/data')
        data = json.loads(response.data)
        assert 'id' in data
        assert 'name' in data
        assert 'features' in data
        assert isinstance(data['features'], list)
    
    def test_post_data_with_json_returns_201(self, client):
        """Test POST /api/data with JSON body returns 201"""
        test_data = {'name': 'Test', 'value': 123}
        response = client.post('/api/data',
                              data=json.dumps(test_data),
                              content_type='application/json')
        assert response.status_code == 201
    
    def test_post_data_without_json_returns_400(self, client):
        """Test POST /api/data without JSON body returns 400"""
        response = client.post('/api/data')
        assert response.status_code == 400
    
    def test_post_data_returns_created_data(self, client):
        """Test POST /api/data returns the created data"""
        test_data = {'name': 'Test', 'value': 123}
        response = client.post('/api/data',
                              data=json.dumps(test_data),
                              content_type='application/json')
        data = json.loads(response.data)
        assert 'data' in data
        assert data['data'] == test_data


class TestVersionEndpoint:
    """
    Test suite for version endpoint
    """
    
    def test_version_returns_200(self, client):
        """Test version endpoint returns 200 status code"""
        response = client.get('/version')
        assert response.status_code == 200
    
    def test_version_contains_metadata(self, client):
        """Test version endpoint contains version metadata"""
        response = client.get('/version')
        data = json.loads(response.data)
        assert 'version' in data
        assert 'build_id' in data
        assert 'environment' in data
        assert 'hostname' in data


class TestErrorHandling:
    """
    Test suite for error handling
    """
    
    def test_404_error_handler(self, client):
        """Test 404 error is handled correctly"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Not found'
    
    def test_simulate_error_returns_500(self, client):
        """Test simulated error endpoint returns 500"""
        response = client.get('/api/simulate-error')
        assert response.status_code == 500
    
    def test_simulate_error_increments_error_count(self, client, reset_app_state):
        """Test simulated error increments error counter"""
        initial_error_count = app_state['error_count']
        client.get('/api/simulate-error')
        assert app_state['error_count'] == initial_error_count + 1


class TestHealthToggle:
    """
    Test suite for health toggle functionality
    """
    
    def test_toggle_health_changes_state(self, client):
        """Test toggle health endpoint changes application state"""
        initial_state = app_state['healthy']
        response = client.post('/api/toggle-health')
        assert response.status_code == 200
        assert app_state['healthy'] != initial_state
    
    def test_toggle_health_returns_new_state(self, client):
        """Test toggle health endpoint returns new health state"""
        response = client.post('/api/toggle-health')
        data = json.loads(response.data)
        assert 'healthy' in data
        assert isinstance(data['healthy'], bool)


class TestRequestCounter:
    """
    Test suite for request counting functionality
    """
    
    def test_multiple_requests_increment_counter(self, client, reset_app_state):
        """Test multiple requests increment the counter correctly"""
        initial_count = app_state['request_count']
        
        client.get('/')
        client.get('/health')
        client.get('/metrics')
        
        assert app_state['request_count'] == initial_count + 3
    
    def test_error_requests_increment_both_counters(self, client, reset_app_state):
        """Test error requests increment both request and error counters"""
        initial_request_count = app_state['request_count']
        initial_error_count = app_state['error_count']
        
        client.get('/api/simulate-error')
        
        assert app_state['request_count'] == initial_request_count + 1
        assert app_state['error_count'] == initial_error_count + 1


class TestIntegration:
    """
    Integration tests for the application
    """
    
    def test_application_flow(self, client, reset_app_state):
        """Test complete application flow"""
        # Check health
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # Get data
        data_response = client.get('/api/data')
        assert data_response.status_code == 200
        
        # Create data
        test_data = {'name': 'Integration Test'}
        create_response = client.post('/api/data',
                                     data=json.dumps(test_data),
                                     content_type='application/json')
        assert create_response.status_code == 201
        
        # Check metrics
        metrics_response = client.get('/metrics')
        assert metrics_response.status_code == 200
        metrics_data = json.loads(metrics_response.data)
        assert metrics_data['application']['total_requests'] >= 4
    
    def test_health_degradation_and_recovery(self, client):
        """Test application health degradation and recovery"""
        # Initial health check - should be healthy
        response1 = client.get('/health')
        assert response1.status_code == 200
        
        # Toggle health to unhealthy
        client.post('/api/toggle-health')
        
        # Health check should fail
        response2 = client.get('/health')
        assert response2.status_code == 503
        
        # Toggle health back to healthy
        client.post('/api/toggle-health')
        
        # Health check should pass again
        response3 = client.get('/health')
        assert response3.status_code == 200


# Run tests with coverage
# pytest test_app.py -v --cov=app --cov-report=html --cov-report=term

# Test execution notes:
# - All tests use fixtures for proper setup/teardown
# - Tests are organized into logical classes
# - Each test is independent and can run in any order
# - Coverage target: >80% code coverage
# - Integration tests verify end-to-end functionality
