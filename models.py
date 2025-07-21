"""Data models for the application.

This module defines the data models used throughout the application.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Technology(BaseModel):
    """Technology specification model.

    Attributes:
        language: Programming language or technology name.
        version: Version of the technology.
        package_manager: Package manager for the technology.
    """

    language: str
    version: str
    package_manager: str


class BlueprintStatus(str, Enum):
    """Status of a blueprint generation or validation process."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class SuccessfulBlueprint(BaseModel):
    """Result of a blueprint generation or validation process.

    Attributes:
        success: Whether the process was successful.
        message: Message describing the result.
        suggestions: Optional suggestions for improvement.
    """

    success: bool
    message: str
    suggestions: Optional[str] = None


class AgentAction(str, Enum):
    """Actions that can be performed by agents."""

    GENERATE = "generate"
    VALIDATE = "validate"
    FIX = "fix"


class RouterRequest(BaseModel):
    """Request to the router agent.

    Attributes:
        action: Action to perform.
        technology: Technology specification.
        context: Additional context for the action.
    """

    action: AgentAction
    technology: Technology
    context: Optional[str] = None


class RouterResponse(BaseModel):
    """Response from the router agent.

    Attributes:
        status: Status of the response.
        result: Result of the action.
        next_action: Optional next action to perform.
    """

    status: BlueprintStatus
    result: SuccessfulBlueprint
    next_action: Optional[AgentAction] = None
