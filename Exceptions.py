"""All custom exceptions used"""

class InvalidCharException(Exception):
    """Raised when an invalid character is input in string mode"""
    default_message = "An invalid character was input"

    def __init__(self, message = None):
        super().__init__(message or self.default_message)

class ExitTextBoxException(Exception):
    """Raised when the user inputs h to exit string_mode"""

    def __init__(self, *args):
        super().__init__(*args)

# Future Exceptions to go here