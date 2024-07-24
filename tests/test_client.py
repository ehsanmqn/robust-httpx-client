import pytest
import httpx
import tenacity
from unittest import mock
from cluster_client.client import ClusterClient
from httpx import Response, RequestError, TimeoutException

from cluster_client.config import HOSTS


@pytest.fixture
def mock_async_client():
    return mock.AsyncMock(spec=httpx.AsyncClient)


@pytest.mark.asyncio
async def test_create_group_on_host_success():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 201

    with mock.patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
        result = await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is True


@pytest.mark.asyncio
async def test_create_group_on_host_400_status_code():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    with mock.patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
        result = await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is False


@pytest.mark.asyncio
async def test_create_group_on_host_500_status_code():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 500

    with mock.patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
        result = await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is False


@pytest.mark.asyncio
async def test_create_group_on_host_timeout():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'post', side_effect=TimeoutException('Request timed out')):
        with pytest.raises(tenacity.RetryError):
            await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_create_group_on_host_request_error():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'post', side_effect=RequestError('Request failed')):
        with pytest.raises(tenacity.RetryError):
            await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_delete_group_on_host_success():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 200

    with mock.patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
        result = await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is True


@pytest.mark.asyncio
async def test_delete_group_on_host_400_status_code():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    with mock.patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
        result = await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_on_host_500_status_code():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 500

    with mock.patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
        result = await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_on_host_timeout_error():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'request', side_effect=TimeoutException('Request timed out')):
        with pytest.raises(tenacity.RetryError):
            await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_delete_group_on_host_request_error():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'request', side_effect=RequestError('Request failed')):
        with pytest.raises(tenacity.RetryError):
            await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_verify_group_on_host_success():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 200

    with mock.patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
        result = await client._verify_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is True


@pytest.mark.asyncio
async def test_verify_group_on_host_not_found():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 404

    with mock.patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
        result = await client._verify_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is False


@pytest.mark.asyncio
async def test_verify_group_on_host_request_error():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'get', side_effect=RequestError('Request failed')):
        with pytest.raises(tenacity.RetryError):
            await client._verify_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_rollback_creation_success():
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_delete_group_on_host', return_value=True), \
            mock.patch.object(client, '_verify_group_on_host', return_value=False):
        undeleted_hosts = await client._rollback_creation(httpx.AsyncClient(), 'test_group', HOSTS)
        assert undeleted_hosts == []


@pytest.mark.asyncio
async def test_rollback_creation_failure():
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_delete_group_on_host', return_value=True), \
            mock.patch.object(client, '_verify_group_on_host', return_value=True):
        undeleted_hosts = await client._rollback_creation(httpx.AsyncClient(), 'test_group', HOSTS)
        assert undeleted_hosts == HOSTS


@pytest.mark.asyncio
async def test_create_group_success():
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_create_group_on_host', return_value=True), \
            mock.patch.object(client, '_verify_group_on_host', return_value=True):
        result = await client.create_group('test_group')
        assert result is True


@pytest.mark.asyncio
async def test_create_group_rollback():
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_create_group_on_host', side_effect=[True, True, False]), \
            mock.patch.object(client, '_verify_group_on_host', return_value=True), \
            mock.patch.object(client, '_rollback_creation', return_value=HOSTS[:2]):
        result = await client.create_group('test_group')
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_success():
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_delete_group_on_host', return_value=True):
        result = await client.delete_group('test_group')
        assert result == []


@pytest.mark.asyncio
async def test_delete_group_failure():
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_delete_group_on_host', side_effect=[True, False, True]):
        result = await client.delete_group('test_group')
        assert result == [HOSTS[1]]


@pytest.mark.asyncio
async def test_create_group_on_host_empty_group_id():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    with mock.patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
        result = await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], '')
        assert result is False


@pytest.mark.asyncio
async def test_create_group_on_host_unexpected_exception():
    client = ClusterClient()

    class UnexpectedException(Exception):
        pass

    with mock.patch.object(httpx.AsyncClient, 'post', side_effect=UnexpectedException('Unexpected error')):
        with pytest.raises(UnexpectedException):
            await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_delete_group_on_host_unexpected_exception():
    client = ClusterClient()

    class UnexpectedException(Exception):
        pass

    with mock.patch.object(httpx.AsyncClient, 'request', side_effect=UnexpectedException('Unexpected error')):
        with pytest.raises(UnexpectedException):
            await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_verify_group_on_host_unexpected_exception():
    client = ClusterClient()

    class UnexpectedException(Exception):
        pass

    with mock.patch.object(httpx.AsyncClient, 'get', side_effect=UnexpectedException('Unexpected error')):
        with pytest.raises(UnexpectedException):
            await client._verify_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')


@pytest.mark.asyncio
async def test_create_group_multiple_requests_with_one_failure():
    hosts = ["http://node1.example.com", "http://node2.example.com", "http://node3.example.com"]

    client = ClusterClient(hosts=hosts)
    group_id = "test-group"

    async def mock_post(url):
        if "node3.example.com" in url:
            raise httpx.RequestError("Connection error", request=None)
        return mock.AsyncMock(status_code=201)()

    async def mock_delete():
        return mock.AsyncMock(status_code=200)()

    async def mock_get(url):
        if "node3.example.com" in url:
            return mock.AsyncMock(status_code=404)()
        return mock.AsyncMock(status_code=200)()

    with mock.patch('httpx.AsyncClient.post', new=mock_post), \
            mock.patch('httpx.AsyncClient.request', new=mock_delete), \
            mock.patch('httpx.AsyncClient.get', new=mock_get):

        success = await client.create_group(group_id)
        assert not success


@pytest.mark.asyncio
async def test_create_group_success_but_verification_fails(caplog):
    hosts = ["http://node1.example.com", "http://node2.example.com", "http://node3.example.com"]

    client = ClusterClient(hosts=hosts)
    group_id = "test-group"

    async def mock_post(url, json=None, timeout=None):
        return mock.AsyncMock(status_code=201)()

    async def mock_delete(url, json=None, timeout=None):
        return mock.AsyncMock(status_code=200)()

    async def mock_get(url, timeout=None):
        return mock.AsyncMock(status_code=404)()

    with mock.patch('httpx.AsyncClient.post', new=mock_post), \
            mock.patch('httpx.AsyncClient.request', new=mock_delete), \
            mock.patch('httpx.AsyncClient.get', new=mock_get):
        success = await client.create_group(group_id)
        assert not success

    assert "Error during group creation. Detail:" in caplog.text
