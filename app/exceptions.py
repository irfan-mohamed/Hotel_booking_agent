class EmailNotVerifiedError(Exception):
    """Exception raised when a guest email has not been verified."""

    def __init__(self, message: str = "Guest email not verified"):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message