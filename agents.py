"""AI agents for blueprint generation and validation.

This module defines agents for creating and validating run.sh files
based on technology specifications.
"""

from __future__ import annotations as _annotations

import atexit

from ddgs import DDGS
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

from config import DEFAULT_MODEL
from models import (
    AgentAction,
    RouterRequest,
    RouterResponse,
    SuccessfulBlueprint,
    Technology,
    BlueprintStatus,
)
from tools import (
    create_directory,
    example_for_run_sh,
    generate_blueprint,
    generate_run_sh,
    instructions,
    show_invalid_run_sh,
    system_prompt,
    technology_stack,
)
from utils import setup_logger

# Configure logging
logger = setup_logger(__name__)


def create_ddgs_client():
    """Create a DuckDuckGo search client with automatic cleanup.

    Returns:
        DDGS: A configured DuckDuckGo search client instance.
    """
    client = DDGS()
    # Register cleanup function
    atexit.register(lambda: client.close() if hasattr(client, "close") else None)
    return client


# Blueprint Agent - Responsible for generating run.sh scripts
blueprint_agent = Agent(
    DEFAULT_MODEL,
    deps_type=Technology,
    output_type=SuccessfulBlueprint,
    system_prompt=[system_prompt(), example_for_run_sh()],
    instructions=[instructions()],
    tools=[
        duckduckgo_search_tool(create_ddgs_client()),
        create_directory,
        generate_blueprint,
        technology_stack,
        generate_run_sh,
    ],
)


# Validator Agent - Responsible for validating and fixing run.sh scripts
validator_agent = Agent(
    DEFAULT_MODEL,
    deps_type=Technology,
    output_type=SuccessfulBlueprint,
    system_prompt=(
        "You are an expert DevOps engineer specializing in troubleshooting and fixing "
        "installation scripts. Your task is to analyze failed run.sh scripts, identify "
        "issues, and provide corrected versions that work reliably."
    ),
    instructions="""
    Follow these steps to fix a failed run.sh script:
    
    1. Check the technology stack using the `technology_stack` tool
    2. Examine the error logs to identify the root cause of the failure
    3. Review the invalid run.sh script using the `show_invalid_run_sh` tool
    4. Research solutions for the identified issues
    5. Create a corrected version of the script that:
       - Addresses all identified issues
       - Follows best practices for shell scripting
       - Works on both Alpine and Debian environments
    6. Use the `generate_run_sh` tool to save and validate your fixed script
    """,
    tools=[
        duckduckgo_search_tool(create_ddgs_client()),
        technology_stack,
        show_invalid_run_sh,
        generate_run_sh,
    ],
)


# Router Agent - Orchestrates the workflow between blueprint and validator agents
async def router_agent(request: RouterRequest) -> RouterResponse:
    """Router agent that orchestrates the workflow between blueprint and validator agents.

    Args:
        request: Router request containing action and technology details.

    Returns:
        Router response with results and next action.
    """
    logger.info(
        "Router agent processing %s action for %s %s with %s",
        request.action.value,
        request.technology.language,
        request.technology.version,
        request.technology.package_manager,
    )

    if request.action == AgentAction.GENERATE:
        # Generate blueprint using blueprint agent
        result = await blueprint_agent.run(
            "Create a setup for the given technology stack that works on both Alpine and Debian",
            deps=request.technology,
        )

        if not result.output.success:
            # If generation failed, set next action to fix
            return RouterResponse(
                status=BlueprintStatus.FAILURE,
                result=result.output,
                next_action=AgentAction.FIX,
            )

        # If generation succeeded, set next action to validate
        return RouterResponse(
            status=BlueprintStatus.SUCCESS,
            result=result.output,
            next_action=AgentAction.VALIDATE,
        )

    elif request.action == AgentAction.VALIDATE:
        tech = request.technology
        # Validate blueprint using validator agent
        result = await validator_agent.run(
            f"Validate the run.sh file for the given technology stack {tech.language} {tech.version} {tech.package_manager}",
            deps=request.technology,
        )

        if not result.output.success:
            # If validation failed, set next action to fix
            return RouterResponse(
                status=BlueprintStatus.FAILURE,
                result=result.output,
                next_action=AgentAction.FIX,
            )

        # If validation succeeded, we're done
        return RouterResponse(
            status=BlueprintStatus.SUCCESS,
            result=result.output,
        )

    elif request.action == AgentAction.FIX:
        # Fix blueprint using validator agent
        context = request.context or "Fix the run.sh file that failed validation"
        result = await validator_agent.run(
            f"{context}",
            deps=request.technology,
        )

        if not result.output.success:
            # If fixing failed, we're done (with failure)
            return RouterResponse(
                status=BlueprintStatus.FAILURE,
                result=result.output,
            )

        # If fixing succeeded, set next action to validate
        return RouterResponse(
            status=BlueprintStatus.SUCCESS,
            result=result.output,
            next_action=AgentAction.VALIDATE,
        )

    # Unsupported action
    return RouterResponse(
        status=BlueprintStatus.FAILURE,
        result=SuccessfulBlueprint(
            success=False,
            message=f"Unsupported action: {request.action}",
        ),
    )
