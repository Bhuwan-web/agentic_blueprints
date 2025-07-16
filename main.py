from __future__ import annotations as _annotations
import logging
import sys
from logging import getLogger, StreamHandler, Formatter
from models import Technology
from agents import blueprint_agent, validator_agent

# Configure logging to show in console
logger = getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False  # Prevent duplicate logs

if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 2:
        print("Please provide the language, version and package manager as command line arguments")
        sys.exit(1)

    language = sys.argv[1]
    version = sys.argv[2]
    package_manager = sys.argv[3]
    logger.info(f"Creating setup for {language} {version} {package_manager}")
    result = asyncio.run(
        blueprint_agent.run(
            "Create a setup for given technology stack that is applicable to both the alpine and debian using technology deps",
            deps=Technology(language=language, version=version, package_manager=package_manager),
        )
    )
    logger.info(result.output)
    if not result.output.success:
        validator_result = asyncio.run(
            validator_agent.run(
                f"Fix this run.sh file to install given technology. Error Log: {result.output.message}",
                deps=Technology(
                    language=language, version=version, package_manager=package_manager
                ),
            )
        )
        logger.info(validator_result.output)
