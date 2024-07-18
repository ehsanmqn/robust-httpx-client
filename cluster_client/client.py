import httpx
import logging
from exceptions import GroupOperationException
from .config import HOSTS

logger = logging.getLogger(__name__)


class ClusterClient:
    def __init__(self, hosts=HOSTS):
        self.hosts = hosts
