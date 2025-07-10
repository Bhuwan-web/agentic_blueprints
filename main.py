from __future__ import annotations as _annotations
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
import os
import json
import yaml
from logging import getLogger
logger = getLogger(__name__)

class Technology(BaseModel):
    language: str
    version: str
    package_manager: str



async def generate_run_sh(ctx:RunContext[Technology],run_file: str):
    directory = f"setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}"
    try:
        with open(f"{directory}/run.sh","w") as f:
            f.write(run_file)
    except FileNotFoundError as e:
        logger.error(f"Failed to create run.sh: {e}")
    return f"Created run.sh at {directory}/run.sh"

blueprint_agent = Agent("google-gla:gemini-2.5-flash",deps_type=Technology,output_type=[generate_run_sh])


@blueprint_agent.system_prompt
async def system_prompt():
    return "You are a fantastic Engineer, having expertise in Devops and System Engineering.You have metacognitive skills to think step by step and give Precise Correct and Concise answers.Your core job is to create a blueprint for a system based on the given technology stack.Imagine I am using alpine or debian as base image and I want to create a container for my application.Your job is to provide me with bash script, You can take help of tools to create file based on generated output. Below are the examples of run.sh for reference. Take in consideration all the difficulties and complexities of the technology stack for both alpine and debian."

@blueprint_agent.instructions
async def instructions():
    return """Here is step by step instructions to create a blueprint for a system based on the given technology stack.
    1. Create a directory for blueprint using tool `create_directory`.
    2. Create a blueprint.yml file using tool `generate_blueprint`.
    3. Create a run.sh file for the given technology in Technology deps using output type `generate_run_sh`.
    THE CORRECTNESS OF TECHNOLOGY, VERSION and PACKAGE MANAGER IS CRUCIAL.
    If the version is not correct, the blueprint will not work."""
    
@blueprint_agent.system_prompt
async def example_for_run_sh():
    """Here is an example of run.sh for python version 3.11"""
    with open("examples/run.sh","r") as f:
        return f.read()

@blueprint_agent.system_prompt
async def technology_stack(ctx:RunContext[Technology]):
    return f"""Generate run.sh for {ctx.deps.language} version {ctx.deps.version} and package manager {ctx.deps.package_manager}"""
    

@blueprint_agent.tool
async def create_directory(ctx:RunContext[Technology]):
    os.makedirs("setup", exist_ok=True)
    os.makedirs(f"setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}", exist_ok=True)
    logger.info(f" Created Directory setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}")
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
@blueprint_agent.tool
async def generate_blueprint(ctx:RunContext[Technology]):
    with open(f"setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}/blueprint.yml","w") as f:
        content_json={
            "name": f"{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}",
            "version": "1.0.0",
            "description": f"Installs {ctx.deps.language} {ctx.deps.version} if it is not already present in the runner environment.",
            "author": "Bhuwan"
        }
        content = await json_to_yaml(content_json)
        
        f.write(content)
    return f"Created blueprint at setup/{ctx.deps.language}-{ctx.deps.version}-{ctx.deps.package_manager}/blueprint.yml"
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
    result=asyncio.run(blueprint_agent.run("Create a setup for given technology stack that is applicable to both the alpine and debian using technology deps", deps=Technology(language=language, version=version, package_manager=package_manager)))
    logger.info(result.output)
    