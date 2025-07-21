"""Tools for blueprint generation and validation.

This module defines tools used by agents for blueprint generation and validation.
"""

from __future__ import annotations as _annotations

import os
from typing import Dict, Any, Optional

import docker
from pydantic_ai import RunContext

from config import DOCKER_CONFIG, BlueprintConfig
from models import SuccessfulBlueprint, Technology
from utils import (
    create_tar_archive,
    ensure_directory,
    json_to_yaml,
    make_executable,
    read_file,
    setup_logger,
    write_file,
)

# Configure logging
logger = setup_logger(__name__)
blueprint_config = BlueprintConfig()


def system_prompt() -> str:
    """Return the system prompt for the blueprint agent."""
    return (
        "You are a DevOps engineer specializing in containerization and system configuration. "
        "Your task is to create blueprints for installing various technologies in container "
        "environments. Focus on creating reliable, efficient installation scripts that work "
        "on both Alpine and Debian-based images. Provide clear, well-commented bash scripts "
        "that handle edge cases and follow best practices."
    )


def instructions() -> str:
    """Return the instructions for the blueprint agent."""
    return """Follow these steps to create a blueprint for the specified technology:

1. Check the technology stack using the `technology_stack` tool
2. Create a directory for the blueprint using the `create_directory` tool
3. Research the installation process for the specified technology and version
4. Create a run.sh script that:
   - Handles both Alpine and Debian environments
   - Downloads from official sources (avoid package managers when possible)
   - Includes proper error handling
   - Verifies successful installation
5. Use the `generate_run_sh` tool to save and validate your script

The correctness of technology name, version, and package manager is crucial for success."""


def example_for_run_sh() -> str:
    """Return an example run.sh script for reference."""
    try:
        return read_file("examples/run.sh")
    except FileNotFoundError:
        # Provide a fallback example if the file doesn't exist
        return """#!/bin/bash
set -e

# Example installation script for Python 3.11
echo "Installing Python 3.11..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
else
    OS=$(uname -s)
fi

# Install based on OS
if [[ "$OS" == *"Alpine"* ]]; then
    # Alpine installation
    apk add --no-cache wget tar
    wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz
    tar -xzf Python-3.11.0.tgz
    cd Python-3.11.0
    ./configure --enable-optimizations
    make -j$(nproc)
    make install
elif [[ "$OS" == *"Debian"* || "$OS" == *"Ubuntu"* ]]; then
    # Debian/Ubuntu installation
    apt-get update
    apt-get install -y wget build-essential
    wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz
    tar -xzf Python-3.11.0.tgz
    cd Python-3.11.0
    ./configure --enable-optimizations
    make -j$(nproc)
    make install
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Verify installation
python3.11 --version

echo "Python 3.11 installed successfully"
"""


async def technology_stack(ctx: RunContext[Technology]) -> str:
    """Get information about the requested technology stack.

    Args:
        ctx: Run context containing technology details.

    Returns:
        String describing the technology stack.
    """
    logger.info(
        "Checking technology stack: %s version %s with %s",
        ctx.deps.language,
        ctx.deps.version,
        ctx.deps.package_manager,
    )
    return (
        f"Generate run.sh for {ctx.deps.language} version {ctx.deps.version} "
        f"and package manager {ctx.deps.package_manager}"
    )


async def create_directory(ctx: RunContext[Technology]) -> str:
    """Create a directory for the blueprint.

    Args:
        ctx: Run context containing technology details.

    Returns:
        Message indicating directory creation status.
    """
    tech_dir = blueprint_config.get_tech_dir(
        ctx.deps.language, ctx.deps.version, ctx.deps.package_manager
    )
    ensure_directory("setup")
    ensure_directory(tech_dir)

    logger.info(
        "Created directory: %s",
        tech_dir,
    )
    return f"Directory created: {tech_dir}"


async def generate_blueprint(ctx: RunContext[Technology]) -> str:
    """Generate a blueprint.yml file.

    Args:
        ctx: Run context containing technology details.

    Returns:
        Message indicating blueprint creation status.
    """
    tech_dir = blueprint_config.get_tech_dir(
        ctx.deps.language, ctx.deps.version, ctx.deps.package_manager
    )
    blueprint_path = os.path.join(tech_dir, "blueprint.yml")

    content_json = {
        "name": f"{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}",
        "version": blueprint_config.version,
        "description": (
            f"Installs {ctx.deps.language} {ctx.deps.version} if it is not already "
            "present in the runner environment."
        ),
        "author": blueprint_config.author,
    }

    content = await json_to_yaml(content_json)
    write_file(blueprint_path, content)

    return f"Created blueprint at {blueprint_path}"


async def generate_run_sh(ctx: RunContext[Technology], run_file: str) -> SuccessfulBlueprint:
    """Generate and validate a run.sh file.

    Args:
        ctx: Run context containing technology details.
        run_file: Content of the run.sh file.

    Returns:
        SuccessfulBlueprint indicating success or failure.
    """
    tech_dir = blueprint_config.get_tech_dir(
        ctx.deps.language, ctx.deps.version, ctx.deps.package_manager
    )
    run_file_path = os.path.join(tech_dir, "run.sh")

    # Create directory if it doesn't exist
    ensure_directory(tech_dir)

    try:
        # Write the run.sh file
        write_file(run_file_path, run_file)

        # Make the script executable
        make_executable(run_file_path)

        # Validate the script
        validation_result = await validate_run_sh(run_file_path)

        return SuccessfulBlueprint(success=True, message=validation_result)
    except (OSError, ValueError) as e:
        return SuccessfulBlueprint(success=False, message=str(e))


async def validate_run_sh(run_file_path: str) -> str:
    """Validate a run.sh file by executing it in a Docker container.

    Args:
        run_file_path: Path to the run.sh file.

    Returns:
        Validation result message.
    """
    try:
        client = docker.from_env()
        script_path = os.path.abspath(run_file_path)

        if not os.path.exists(script_path):
            return f"Run script not found at: {script_path}"

        logger.info("Creating Alpine container for validation...")

        # Create and start container
        container = client.containers.run(**DOCKER_CONFIG)

        try:
            # Copy the run.sh file to container
            logger.info("Copying run.sh to container...")
            tar_buffer = create_tar_archive(script_path)
            container.put_archive("/tmp/", tar_buffer.getvalue())

            # Make script executable
            container.exec_run(["chmod", "+x", "/tmp/run.sh"])

            # Install bash
            logger.info("Installing bash...")
            install_result = container.exec_run(["apk", "add", "--no-cache", "bash"])
            if install_result.exit_code != 0:
                error_output = install_result.output.decode("utf-8")
                raise ValueError(
                    f"Failed to install bash. Exit code: {install_result.exit_code}, "
                    f"Output: {error_output}"
                )

            # Execute the script
            logger.info("Executing run.sh script with live logs...")
            exec_id = container.client.api.exec_create(
                container.id,
                cmd=["/bin/bash", "/tmp/run.sh"],
                stdout=True,
                stderr=True,
            )["Id"]

            # Stream output in real-time
            stream = container.client.api.exec_start(exec_id, stream=True)
            logs = []
            for chunk in stream:
                decoded_line = chunk.decode("utf-8").strip()
                logger.info(decoded_line)
                logs.append(decoded_line)

            # Get exit code after streaming completes
            exit_code = container.client.api.exec_inspect(exec_id)["ExitCode"]
            logger.info("Script exited with code: %s", exit_code)

            # Keep only last 500 characters for error reporting
            last_logs = "\n".join(logs)[-500:]

            if exit_code == 0:
                return f"Validation successful. Exit code: {exit_code}"

            error_msg = (
                "Validation failed. The script exited with code %s. "
                "Check the logs for details. Last logs: %s"
            )
            raise ValueError(error_msg % (exit_code, last_logs))

        finally:
            container.stop()
    except Exception as e:
        raise ValueError(f"Validation failed: {str(e)}") from e


async def show_invalid_run_sh(ctx: RunContext[Technology]) -> str:
    """Show the invalid run.sh file that needs to be reconfigured.

    Args:
        ctx: Run context containing technology details.

    Returns:
        Content of the run.sh file.
    """
    run_file_path = blueprint_config.get_run_sh_path(
        ctx.deps.language, ctx.deps.version, ctx.deps.package_manager
    )

    try:
        return read_file(run_file_path)
    except FileNotFoundError:
        return "Run.sh file not found. It may not have been generated yet."
