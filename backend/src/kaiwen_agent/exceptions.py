class AgentError(Exception):
    """Base error for predictable runtime failures."""


class DuplicateToolError(AgentError):
    """Raised when two tools share the same public name."""


class PermissionDeniedError(AgentError):
    """Raised before a tool executes without all required permissions."""


class ToolNotFoundError(AgentError):
    """Raised when a model requests an unregistered tool."""


class ToolValidationError(AgentError):
    """Raised when tool arguments fail schema validation."""


class ApprovalRequiredError(AgentError):
    """Raised when an approval-protected tool has no approval gate."""


class ApprovalDeniedError(AgentError):
    """Raised when a tool execution request is rejected."""


class ToolTimeoutError(AgentError):
    """Raised when a tool exceeds its declared timeout."""


class ToolExecutionError(AgentError):
    """Raised when a tool handler fails after its retry policy is exhausted."""
