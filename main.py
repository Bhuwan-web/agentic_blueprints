#!/usr/bin/env python3
"""Main entry point for the blueprint generator application.

This module provides the command-line interface for generating and validating
technology blueprints.
"""

from __future__ import annotations as _annotations

import argparse
import asyncio
import sys
from typing import List, Optional

from pydantic_ai.exceptions import UnexpectedModelBehavior

from agents import router_agent
from models import AgentAction, RouterRequest, Technology
from utils import setup_logger

# Configure logging
logger = setup_logger(__name__)


async def run_blueprint_generation(
    language: str, version: str, package_manager: str, max_attempts: int = 3
) -> bool:
    """Run the blueprint generation process.

    Args:
        language: Programming language or technology name.
        version: Version of the technology.
        package_manager: Package manager for the technology.
        max_attempts: Maximum number of attempts to generate and validate the blueprint.

    Returns:
        True if the blueprint was successfully generated and validated, False otherwise.
    """
    technology = Technology(language=language, version=version, package_manager=package_manager)

    # Start with generation
    action = AgentAction.GENERATE
    context = None
    attempt = 1

    while attempt <= max_attempts:
        logger.info(
            "Attempt %d/%d: %s for %s %s with %s",
            attempt,
            max_attempts,
            action.value,
            language,
            version,
            package_manager,
        )

        try:
            # Create request for router agent
            request = RouterRequest(
                action=action,
                technology=technology,
                context=context,
            )

            # Process request
            response = await router_agent(request)

            # Log result
            if response.result.success:
                logger.info("Success: %s", response.result.message)
            else:
                logger.warning("Failure: %s", response.result.message)

            # If no next action, we're done
            if not response.next_action:
                return response.result.success

            # Otherwise, continue with next action
            action = response.next_action
            context = response.result.message

        except UnexpectedModelBehavior as e:
            logger.error("Model error: %s", str(e))
            return False

        attempt += 1

    logger.warning("Maximum attempts reached without success")
    return False


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments to parse. If None, sys.argv[1:] is used.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate and validate technology blueprints")
    parser.add_argument("language", help="Programming language or technology name")
    parser.add_argument("version", help="Version of the technology")
    parser.add_argument("package_manager", help="Package manager for the technology")
    parser.add_argument(
        "--max-attempts", type=int, default=3, help="Maximum number of attempts (default: 3)"
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point.

    Args:
        args: Command-line arguments. If None, sys.argv[1:] is used.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parsed_args = parse_args(args)

    logger.info(
        "Creating setup for %s %s with %s",
        parsed_args.language,
        parsed_args.version,
        parsed_args.package_manager,
    )

    success = asyncio.run(
        run_blueprint_generation(
            parsed_args.language,
            parsed_args.version,
            parsed_args.package_manager,
            parsed_args.max_attempts,
        )
    )

    if success:
        logger.info("Blueprint generation completed successfully")
        return 0
    else:
        logger.error("Blueprint generation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
