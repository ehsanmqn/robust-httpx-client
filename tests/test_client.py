import pytest
import httpx
from httpx import Response, RequestError
from cluster_client.client import ClusterClient
from unittest import mock


@pytest.mark.asyncio
async def test_create_group_on_host_success(mocker):
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 201

    mocker.patch.object(httpx.AsyncClient, 'post', return_value=mock_response)
    result = await client._create_group_on_host(httpx.AsyncClient(), 'http://node1.example.com', 'test_group')

    assert result is True


@pytest.mark.asyncio
async def test_create_group_on_host_failure_status_code(mocker):
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    mocker.patch.object(httpx.AsyncClient, 'post', return_value=mock_response)
    result = await client._create_group_on_host(httpx.AsyncClient(), 'http://node1.example.com', 'test_group')

    assert result is False


@pytest.mark.asyncio
async def test_create_group_on_host_request_error(mocker):
    client = ClusterClient()

    mocker.patch.object(httpx.AsyncClient, 'post', side_effect=RequestError('Request failed'))
    result = await client._create_group_on_host(httpx.AsyncClient(), 'http://node1.example.com', 'test_group')

    assert result is False
