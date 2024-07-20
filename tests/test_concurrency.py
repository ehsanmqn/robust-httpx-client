import pytest
import asyncio
import httpx
import tenacity
from unittest import mock
from httpx import Response, RequestError

from cluster_client.client import ClusterClient
from cluster_client.config import HOSTS
from cluster_client.exceptions import RequestErrorException


@pytest.mark.asyncio
async def test_create_group_concurrent_requests_success():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 201

    with mock.patch.object(httpx.AsyncClient, 'post', return_value=mock_response) as mock_post:
        async def create_group():
            return await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')

        tasks = [create_group() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(result is True for result in results)
        assert mock_post.call_count == 5


@pytest.mark.asyncio
async def test_create_group_concurrent_requests_failure():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    with mock.patch.object(httpx.AsyncClient, 'post', return_value=mock_response) as mock_post:
        async def create_group():
            return await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')

        tasks = [create_group() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(result is False for result in results)
        assert mock_post.call_count == 5


@pytest.mark.asyncio
async def test_create_group_concurrent_requests_with_exceptions():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'post', side_effect=RequestError('Request failed')) as mock_post:
        async def create_group():
            try:
                await client._create_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
            except RequestErrorException:
                return False
            return True

        tasks = [create_group() for _ in range(5)]

        with pytest.raises(tenacity.RetryError):
            await asyncio.gather(*tasks)

        assert mock_post.call_count == 11


@pytest.mark.asyncio
async def test_delete_group_concurrent_requests_success():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 200

    with mock.patch.object(httpx.AsyncClient, 'request', return_value=mock_response) as mock_request:
        async def delete_group():
            return await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')

        tasks = [delete_group() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(result is True for result in results)
        assert mock_request.call_count == 5


@pytest.mark.asyncio
async def test_delete_group_concurrent_requests_failure():
    client = ClusterClient()

    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = 400

    with mock.patch.object(httpx.AsyncClient, 'request', return_value=mock_response) as mock_request:
        async def delete_group():
            return await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')

        tasks = [delete_group() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(result is False for result in results)
        assert mock_request.call_count == 5


@pytest.mark.asyncio
async def test_delete_group_concurrent_requests_with_exceptions():
    client = ClusterClient()

    with mock.patch.object(httpx.AsyncClient, 'request', side_effect=RequestError('Request failed')) as mock_request:
        async def delete_group():
            try:
                await client._delete_group_on_host(httpx.AsyncClient(), HOSTS[0], 'test_group')
            except RequestErrorException:
                return False
            return True

        tasks = [delete_group() for _ in range(5)]

        with pytest.raises(tenacity.RetryError):
            await asyncio.gather(*tasks)

        assert mock_request.call_count == 11
