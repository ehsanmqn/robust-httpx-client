import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import HOSTS
from .exceptions import (
    GroupOperationException,
    HandleableErrorException,
    RequestErrorException
)

logger = logging.getLogger(__name__)


class ClusterClient:
    def __init__(self, hosts=HOSTS):
        self.hosts = hosts

    @retry(
        retry=retry_if_exception_type(HandleableErrorException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _create_group_on_host(self, client: httpx.AsyncClient, host: str, group_id: str) -> bool:
        """
        Create a group on a specific host.
        """

        url = f'{host}/v1/group/'

        try:
            response = await client.post(url, json={'groupId': group_id}, timeout=10.0)
            if response.status_code == 201:
                logger.info(f'Group {group_id} created on {host}')
                return True
            elif response.status_code == 429 or 500 <= response.status_code < 600:
                logger.warning(f'Error {response.status_code} while creating group on {host}')
                raise HandleableErrorException(host, response.status_code)
            else:
                logger.error(f'Failed to create group on {host}: {response.status_code}')
                return False

        except httpx.RequestError as exc:
            logger.error(f'Request error occurred while creating group on {host}: {exc}')
            raise RequestErrorException(host, str(exc))

    @retry(
        retry=retry_if_exception_type(HandleableErrorException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _delete_group_on_host(self, client: httpx.AsyncClient, host: str, group_id: str) -> bool:
        """
        Delete a group from a specific host.
        """

        url = f'{host}/v1/group/'

        try:
            response = await client.request(method='DELETE', url=url, json={'groupId': group_id}, timeout=10.0)
            if response.status_code == 200:
                logger.info(f'Group {group_id} deleted from {host}')
                return True
            elif response.status_code == 429 or 500 <= response.status_code < 600:
                logger.warning(f'Error {response.status_code} while deleting group on {host}')
                raise HandleableErrorException(host, response.status_code)
            else:
                logger.error(f'Failed to delete group on {host}: {response.status_code}')
                return False

        except httpx.RequestError as exc:
            logger.error(f'Request error occurred while deleting group on {host}: {exc}')
            raise RequestErrorException(host, str(exc))

    async def _rollback_creation(self, client: httpx.AsyncClient, group_id: str, success_hosts: list) -> None:
        """
        Rollback group creation on hosts where it was successfully created.
        """

        logger.info('Rolling back creation on successful hosts...')

        for host in success_hosts:
            if not await self._delete_group_on_host(client, host, group_id):
                logger.error(f'Failed to rollback creation on {host}')

    async def create_group(self, group_id: str) -> bool:
        """
        Create a group on all cluster nodes. Rolls back if any creation fails.
        """

        async with httpx.AsyncClient() as client:
            success_hosts = []
            try:
                for host in self.hosts:
                    if not await self._create_group_on_host(client, host, group_id):
                        raise GroupOperationException(f'Failed to create group on {host}, initiating rollback.')
                    success_hosts.append(host)
            except GroupOperationException as e:
                logger.error(f'Error during creation: {e}')
                await self._rollback_creation(client, group_id, success_hosts)
                return False

            return True

    async def delete_group(self, group_id: str) -> bool:
        """
        Delete a group from all cluster nodes.
        """

        async with httpx.AsyncClient() as client:
            for host in self.hosts:
                await self._delete_group_on_host(client, host, group_id)
            return True
