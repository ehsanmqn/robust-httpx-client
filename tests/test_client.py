import pytest
import httpx
import tenacity
from httpx import Response, RequestError
from cluster_client.client import ClusterClient
from unittest import mock
from cluster_client.config import HOSTS
from cluster_client.exceptions import RequestErrorException, GroupOperationException, ClusterOperationException


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
async def test_create_group_on_host_failure_status_code():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    with mock.patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
        result = await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is False


@pytest.mark.asyncio
async def test_create_group_on_host_request_error():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'post', side_effect=RequestError('Request failed')):
        with pytest.raises(RequestErrorException):
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
async def test_delete_group_on_host_failure_status_code():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    with mock.patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
        result = await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_on_host_request_error():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'request', side_effect=RequestError('Request failed')):
        with pytest.raises(RequestErrorException):
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
async def test_rollback_creation_success(mock_async_client):
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_delete_group_on_host', return_value=True), \
         mock.patch.object(client, '_verify_group_on_host', return_value=False):
        undeleted_hosts = await client._rollback_creation(mock_async_client, 'test_group', HOSTS)
        assert undeleted_hosts == []


@pytest.mark.asyncio
async def test_rollback_creation_failure(mock_async_client):
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_delete_group_on_host', return_value=True), \
         mock.patch.object(client, '_verify_group_on_host', return_value=True):
        undeleted_hosts = await client._rollback_creation(mock_async_client, 'test_group', HOSTS)
        assert undeleted_hosts == HOSTS


@pytest.mark.asyncio
async def test_create_group_success(mock_async_client):
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_create_group_on_host', return_value=True), \
         mock.patch.object(client, '_verify_group_on_host', return_value=True):
        result = await client.create_group('test_group')
        assert result is True


@pytest.mark.asyncio
async def test_create_group_rollback(mock_async_client):
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_create_group_on_host', side_effect=[True, True, False]), \
         mock.patch.object(client, '_verify_group_on_host', return_value=True), \
         mock.patch.object(client, '_rollback_creation', return_value=HOSTS[:2]):
        result = await client.create_group('test_group')
        assert result is False


@pytest.mark.asyncio
async def test_delete_group(mock_async_client):
    client = ClusterClient(hosts=HOSTS)

    with mock.patch.object(client, '_delete_group_on_host', return_value=True):
        result = await client.delete_group('test_group')
        assert result is True
