class InvalidDivisionError(Exception):
    """A custom exception class."""
    def __init__(self, message="Invalid division."):
        self.message = message
        super().__init__(self.message)

class InvalidOperationError(Exception):
    """A custom exception class."""
    def __init__(self, message="Invalid operation."):
        self.message = message
        super().__init__(self.message)

class InvalidJSONError(Exception):
    """A custom exception class."""
    def __init__(self, message="Invalid JSON File."):
        self.message = message
        super().__init__(self.message)

class ArgumentError(Exception):
    """A custom exception class."""
    def __init__(self, message="Invalid argument."):
        self.message = message
        super().__init__(self.message)

class URLError(Exception):
    """A custom exception class."""
    def __init__(self, message="Invalid URL."):
        self.message = message
        super().__init__(self.message)