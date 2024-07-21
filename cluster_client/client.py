import httpx
import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import HOSTS
from .exceptions import GroupOperationException, RequestErrorException

logger = logging.getLogger(__name__)


class ClusterClient:
    def __init__(self, hosts: List[str] = HOSTS):
        self.hosts = hosts

    @retry(
        retry=retry_if_exception_type(RequestErrorException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _create_group_on_host(self, client: httpx.AsyncClient, host: str, group_id: str) -> bool:
        """
        Create a group on a specific host.

        :param client: An instance of `httpx.AsyncClient` for making HTTP requests.
        :param host: The host URL where the group is to be created.
        :param group_id: The ID of the group to create.
        :return: `True` if the group is successfully created; `False` otherwise.
        """

        url = f'{host}/v1/group/'

        try:
            response = await client.post(url, json={'groupId': group_id}, timeout=10)
            if response.status_code == 201:
                logger.info(f'Group {group_id} created on {host}')
                return True

            logger.error(f'Failed to create group on {host}: {response.status_code}')
            return False

        except httpx.RequestError as exc:
            logger.error(f'Request error occurred while creating group on {host}: {exc}')
            raise RequestErrorException(host, str(exc))

    @retry(
        retry=retry_if_exception_type(RequestErrorException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _delete_group_on_host(self, client: httpx.AsyncClient, host: str, group_id: str) -> bool:
        """
        Delete a group from a specific host.

        :param client: An instance of `httpx.AsyncClient` for making HTTP requests.
        :param host: The host URL where the group is to be deleted.
        :param group_id: The ID of the group to delete.
        :return: `True` if the group is successfully deleted; `False` otherwise.
        """

        url = f'{host}/v1/group/'

        try:
            response = await client.request(method='DELETE', url=url, json={'groupId': group_id}, timeout=10)
            if response.status_code == 200:
                logger.info(f'Group {group_id} deleted from {host}')
                return True

            logger.error(f'Failed to delete group on {host}: {response.status_code}')
            return False

        except httpx.RequestError as exc:
            logger.error(f'Request error occurred while deleting group on {host}: {exc}')
            raise RequestErrorException(host, str(exc))

    @retry(
        retry=retry_if_exception_type(RequestErrorException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _verify_group_on_host(self, client: httpx.AsyncClient, host: str, group_id: str) -> bool:
        """
        Verify that a group exists on a specific host.

        :param client: An instance of `httpx.AsyncClient` for making HTTP requests.
        :param host: The host URL where the group is expected to be verified.
        :param group_id: The ID of the group to verify.
        :return: `True` if the group exists on the host; `False` otherwise.
        """

        url = f'{host}/v1/group/{group_id}/'

        try:
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                logger.info(f'Group {group_id} verified on {host}')
                return True
            elif response.status_code == 404:
                logger.warning(f'Group {group_id} not found on {host}')
                return False
            else:
                logger.error(f'Failed to verify group on {host}: {response.status_code}')
                return False

        except httpx.RequestError as exc:
            logger.error(f'Request error occurred while verifying group on {host}: {exc}')
            raise RequestErrorException(host, str(exc))

    async def _rollback_creation(self, client: httpx.AsyncClient, group_id: str, success_hosts: List[str]) -> List[str]:
        """
        Rollback group creation on hosts where it was successfully created.
        Verifies the rollback and returns any hosts where the group remains undeleted.

        :param client: An instance of `httpx.AsyncClient` for making HTTP requests.
        :param group_id: The ID of the group to delete.
        :param success_hosts: A list of hosts where the group was successfully created.
        :return: A list of hosts where the rollback failed, meaning the group still exists.
        """

        logger.info('Rolling back creation on successful hosts...')

        undeleted_hosts = []

        for host in success_hosts:
            try:
                if not await self._delete_group_on_host(client, host, group_id):
                    logger.error(f'Failed to rollback creation on {host}')
                    undeleted_hosts.append(host)
                else:
                    # Verify deletion
                    if await self._verify_group_on_host(client, host, group_id):
                        logger.error(f'Group {group_id} still exists on {host} after rollback attempt')
                        undeleted_hosts.append(host)

            except RequestErrorException as e:
                logger.error(f'Error during rollback on {host}: {e}')
                undeleted_hosts.append(host)

        if len(undeleted_hosts) == 0:
            logger.info('Roll back performed successfully.')

        return undeleted_hosts

    async def create_group(self, group_id: str) -> bool:
        """
        Create a group on all cluster nodes.
        Rolls back if any creation or verification fails.

        :param group_id: The ID of the group to create.
        :return: `True` if the group is successfully created and verified on all hosts; `False` otherwise.
        """

        async with httpx.AsyncClient() as client:
            success_hosts: List[str] = []
            try:
                for host in self.hosts:
                    if not await self._create_group_on_host(client, host, group_id):
                        raise GroupOperationException(f'Failed to create group on {host}, initiating rollback.')
                    success_hosts.append(host)

                # Verify creation
                for host in success_hosts:
                    if not await self._verify_group_on_host(client, host, group_id):
                        raise GroupOperationException(f'Failed to verify group on {host}, initiating rollback.')

            except Exception as e:
                logger.error(f'Error during group creation. Detail: {e}')

                if success_hosts:
                    undeleted_hosts = await self._rollback_creation(client, group_id, success_hosts)
                    if undeleted_hosts:
                        logger.error(f'Rollback failed on the following hosts: {undeleted_hosts}')

                return False

            return True

    async def delete_group(self, group_id: str) -> List[str]:
        """
        Delete a group from all cluster nodes.

        :param group_id: The ID of the group to delete.
        :return: A list of hosts where the deletion failed.
        """

        undeleted_hosts = self.hosts[:]

        async with httpx.AsyncClient() as client:
            for host in self.hosts:
                try:
                    if not await self._delete_group_on_host(client, host, group_id):
                        logger.warning(f'Deletion failed on host {host}')
                        continue
                    undeleted_hosts.remove(host)
                except Exception as e:
                    logger.error(f'Error during deletion on host {host}: {e}')
                    continue

        return undeleted_hosts
