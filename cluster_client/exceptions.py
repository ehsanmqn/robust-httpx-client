class GroupOperationException(Exception):
    """
    Custom exception for group operation failures.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ClusterOperationException(Exception):
    """
    Custom exception for timeout errors.
    """

    def __init__(self, host, status_code):
        message = f'Error occurred on {host}: {status_code}'
        self.message = message
        super().__init__(self.message)


class RequestErrorException(Exception):
    """
    Custom exception for request errors.
    """

    def __init__(self, host, message):
        self.message = f'Request error on {host}: {message}'
        super().__init__(self.message)
