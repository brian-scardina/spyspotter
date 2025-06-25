import pytest
import responses
from pixeltracker.services.network import NetworkService

@pytest.mark.mock
def test_network_service_with_responses():
    """Test NetworkService using responses for HTTP mocking"""
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, 'http://example.com', json={'key': 'value'}, status=200)

        network_service = NetworkService()
        response = network_service.get('http://example.com')

        assert response.json() == {'key': 'value'}
        assert response.status_code == 200
