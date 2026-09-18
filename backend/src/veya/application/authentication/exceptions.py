class AuthenticationError(ValueError):
    pass


class EmailAlreadyRegisteredError(AuthenticationError):
    pass


class InvalidCredentialsError(AuthenticationError):
    pass


class InvalidRefreshTokenError(AuthenticationError):
    pass


class InactiveUserError(AuthenticationError):
    pass
