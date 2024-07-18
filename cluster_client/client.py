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
