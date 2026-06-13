class ThreadNotFoundError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


class RequestAlreadyProcessingError(Exception):
    pass


class RequestPreviouslyFailedError(Exception):
    pass


class ChatProcessingError(Exception):
    pass