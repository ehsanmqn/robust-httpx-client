import httpx
import logging
from .config import HOSTS

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