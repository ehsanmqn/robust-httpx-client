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


class TimeoutErrorException(Exception):
    """
    Custom exception for timeout errors.
    """

    def __init__(self, host):
        message = f'Timeout occurred on {host}'
        self.message = message
        super().__init__(self.message)


class RequestErrorException(Exception):
    """
    Custom exception for request errors.
    """

    def __init__(self, host, message):
        self.message = f'Request error on {host}: {message}'
        super().__init__(self.message)
