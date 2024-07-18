import asyncio
import logging
from cluster_client.client import ClusterClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    client = ClusterClient()
    group_id = 'example_group'

    # Create group
    if await client.create_group(group_id):
        logger.info('Group created successfully on all nodes.')
    else:
        logger.info('Group creation failed and rolled back.')

    # Delete group
    await client.delete_group(group_id)
    logger.info('Group deleted from all nodes.')


if __name__ == '__main__':
    asyncio.run(main())
