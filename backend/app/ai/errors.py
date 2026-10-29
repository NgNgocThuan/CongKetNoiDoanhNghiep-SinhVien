"""Safe AI diagnostics; messages must not contain documents or credentials."""


class LLMError(RuntimeError):
    """An AI request, configuration or extraction failure."""
