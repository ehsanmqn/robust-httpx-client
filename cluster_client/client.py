import httpx
import logging
from .config import HOSTS
from .exceptions import GroupOperationException

logger = logging.getLogger(__name__)


class ClusterClient:
    def __init__(self, hosts=HOSTS):
        self.hosts = hosts

    async def _create_group_on_host(self, client: httpx.AsyncClient, host: str, group_id: str) -> bool:
        """
        Create a group on a specific host.
        """

        url = f'{host}/v1/group/'
        try:
            response = await client.post(url, json={'groupId': group_id})
            if response.status_code == 201:
                logger.info(f'Group {group_id} created on {host}')
                return True

            logger.error(f'Failed to create group on {host}: {response.status_code}')

        except httpx.RequestError as exc:
            logger.error(f'Request error occurred: {exc}')

        return False

    async def _delete_group_on_host(self, client: httpx.AsyncClient, host: str, group_id: str) -> bool:
        """
        Delete a group from a specific host.
        """

        url = f'{host}/v1/group/'
        try:
            # httpx allows sending json parameters only through the request method not the delete method since it's discouraged
            # Ref: https://github.com/encode/httpx/discussions/1587
            response = await client.request(method='DELETE', url=url, json={'groupId': group_id})
            if response.status_code == 200:
                logger.info(f'Group {group_id} deleted from {host}')
                return True

            logger.error(f'Failed to delete group on {host}: {response.status_code}')

        except httpx.RequestError as exc:
            logger.error(f'Request error occurred: {exc}')

        return False

    async def _rollback_creation(self, client: httpx.AsyncClient, group_id: str, success_hosts: list) -> None:
        """
        Rollback group creation on hosts where it was successfully created.
        """

        logger.info('Rolling back creation on successful hosts...')

        for host in success_hosts:
            await self._delete_group_on_host(client, host, group_id)

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
