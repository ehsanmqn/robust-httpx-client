class GroupOperationException(Exception):
    """
    Custom exception for group operation failures.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ServerErrorException(Exception):
    """
    Custom exception for server errors (HTTP 500-599).
    """

    def __init__(self, host, status_code):
        message = f'Server error on {host}: {status_code}'
        self.message = message
        super().__init__(self.message)


class ThrottleErrorException(Exception):
    """
    Custom exception for throttling errors (HTTP 429).
    """

    def __init__(self, host, status_code):
        message = f'Throttling error on {host}: {status_code}'
        self.message = message
        super().__init__(self.message)
