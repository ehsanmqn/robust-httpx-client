class GroupOperationException(Exception):
    """
    Custom exception for group operation failures.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
