from __future__ import annotations as _annotations

import json
import logging
import os
import sys
from logging import Formatter, StreamHandler, getLogger

import docker
import yaml
from pydantic_ai import RunContext

from models import SuccessfulBlueprint, Technology

# Configure logging to show in console
logger = getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False  # Prevent duplicate logs


def system_prompt():
    return "You are a fantastic Engineer, having expertise in Devops and System Engineering.You have meta-cognitive skills to think step by step and give Precise Correct and Concise answers.Your core job is to create a blueprint for a system based on the given technology stack.Imagine I am using alpine or debian as base image and I want to create a container for my application.Your job is to provide me with bash script, You can take help of tools to create file based on generated output. Below are the examples of run.sh for reference. Take in consideration all the difficulties and complexities of the technology stack for both alpine and debian."


def instructions():
    return """Here is step by step instructions to create a blueprint for a system based on the given technology stack.
    CHECK TECH STACK USING TOOL `technology_stack`
    1. Create a directory for blueprint using tool `create_directory`.
    2. Create a blueprint.yml file using tool `generate_blueprint`.
    3. Search for setup configurations for the given technology in Technology deps using tool `duckduckgo_search_tool` on their respective official sources on how to setup for given image or ecosystem. DO NOT OVER COMPLICATE IT MORE THAN REQUIRED.
    4. Create a run.sh file for the given technology in Technology deps using output type `generate_run_sh`.
    THE CORRECTNESS OF TECHNOLOGY, VERSION and PACKAGE MANAGER IS CRUCIAL"""


def example_for_run_sh():
    """Here is an example of run.sh for python version 3.11"""
    with open("examples/run.sh", "r", encoding="utf-8") as f:
        return f.read()


async def technology_stack(ctx: RunContext[Technology]):
    logger.info(
        "Checking technology stack for %s version %s and package manager %s",
        ctx.deps.language,
        ctx.deps.version,
        ctx.deps.package_manager,
    )
    return f"""Generate run.sh for {ctx.deps.language} version {ctx.deps.version} and package manager {ctx.deps.package_manager}"""


async def create_directory(ctx: RunContext[Technology]):
    os.makedirs("setup", exist_ok=True)
    os.makedirs(
        f"setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}", exist_ok=True
    )
    logger.info(
        " Created Directory setup/%s-%s-%s",
        ctx.deps.language,
        ctx.deps.version,
        ctx.deps.package_manager,
    )
    return "Directory created"


async def json_to_yaml(json_data):
    """
    Converts JSON data (string or Python object) to a YAML string.
    """
    if isinstance(json_data, str):
        # If input is a JSON string, parse it first
        data = json.loads(json_data)
    else:
        # If input is already a Python object (e.g., dict, list)
        data = json_data

    yaml_string = yaml.dump(data, default_flow_style=False, sort_keys=False)
    return yaml_string


async def generate_blueprint(ctx: RunContext[Technology]):
    with open(
        f"setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}/blueprint.yml",
        "w",
        encoding="utf-8",
    ) as f:
        content_json = {
            "name": f"{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}",
            "version": "1.0.0",
            "description": f"Installs {ctx.deps.language} {ctx.deps.version} if it is not already present in the runner environment.",
            "author": "Bhuwan",
        }
        content = await json_to_yaml(content_json)

        f.write(content)
    return f"Created blueprint at setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}/blueprint.yml"


async def generate_run_sh(ctx: RunContext[Technology], run_file: str):
    directory = f"setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}"
    run_file_path = f"{directory}/run.sh"

    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    try:
        with open(run_file_path, "w", encoding="utf-8") as f:
            f.write(run_file)

        # Make the script executable
        os.chmod(run_file_path, 0o755)

        # Call validation function
        validation_result = await validate_run_sh_with_cp(run_file_path)

        return SuccessfulBlueprint(success=True, message=validation_result)
    except (OSError, ValueError) as e:
        return SuccessfulBlueprint(success=False, message=f"Failed to generate run.sh: {str(e)}")


# Alternative method using docker cp command
async def validate_run_sh_with_cp(run_file_path: str):
    """
    Alternative validation method using docker cp command
    """
    try:
        client = docker.from_env()
        script_path = os.path.abspath(run_file_path)

        if not os.path.exists(script_path):
            return f"Run script not found at: {script_path}"

        logger.info("Creating Alpine container...")

        # Create and start container
        container = client.containers.run(
            image="alpine:latest",
            command="sleep 3000",  # Keep container alive for 50 minutes
            detach=True,
            remove=True,
            mem_limit="512m",
        )

        try:
            # Copy the run.sh file to container
            logger.info("Copying run.sh to container...")

            # Create tar archive of the script
            import io
            import tarfile

            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                tar.add(script_path, arcname="run.sh")

            tar_buffer.seek(0)

            # Copy to container
            container.put_archive("/tmp/", tar_buffer.getvalue())

            # Make script executable
            container.exec_run(["chmod", "+x", "/tmp/run.sh"])

            # Install bash
            logger.info("Installing bash...")
            install_result = container.exec_run(["apk", "add", "--no-cache", "bash"])
            if install_result.exit_code != 0:
                error_output = install_result.output.decode("utf-8")
                raise ValueError(
                    f"Failed to install bash. Exit code: {install_result.exit_code}, Output: {error_output}"
                )

            # Execute the script
            logger.info("Executing run.sh script...")
            exec_id = container.client.api.exec_create(
                container.id,
                cmd=["/bin/bash", "/tmp/run.sh"],
                stdout=True,
                stderr=True,
            )["Id"]

            # Stream output in real-time
            stream = container.client.api.exec_start(exec_id, stream=True)
            store_last_logs = ""
            for chunk in stream:
                decoded_line = chunk.decode("utf-8").strip()
                logger.info(decoded_line)
                store_last_logs += decoded_line + "\n"

            # Get exit code after streaming completes
            exit_code = container.client.api.exec_inspect(exec_id)["ExitCode"]
            logger.info(f"Script exited with code: {exit_code}")

            # Keep only last 500 characters for error reporting
            store_last_logs = store_last_logs[-500:]

            if exit_code == 0:
                return f"Validation successful. Exit code: {exit_code}"

            error_msg = (
                "Validation failed. Try to Generate run.sh again. Go through the error and "
                "try to fix it and again call generate_run_sh tool. Check the logs above for "
                "details. Last logs: %s"
            )
            raise ValueError(error_msg % store_last_logs)

        finally:
            container.stop()
    except Exception as e:
        raise ValueError(f"Validation failed: {str(e)}") from e


async def show_invalid_run_sh(ctx: RunContext[Technology]):
    """Show the invalid run.sh file that needs to be reconfigured"""
    with open(
        f"setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}/run.sh",
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()
