"""Configuration settings for the application.

This module contains configuration settings for logging, models, and other application parameters.
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, Any

# Model configuration
DEFAULT_MODEL = "google-gla:gemini-2.5-flash"

# Docker configuration
DOCKER_CONFIG = {
    "image": "alpine:latest",
    "command": "sleep 300",  # Keep container alive for 5 minutes
    "detach": True,
    "remove": True,
    "mem_limit": "512m",
}

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

# File paths
EXAMPLES_DIR = "examples"
SETUP_DIR = "setup"


@dataclass
class BlueprintConfig:
    """Configuration for blueprint generation."""

    author: str = "Blueprint Generator"
    version: str = "1.0.0"

    def get_blueprint_path(self, language: str, version: str, package_manager: str) -> str:
        """Get the path to the blueprint file."""
        return os.path.join(SETUP_DIR, f"{language}-{version}-{package_manager}", "blueprint.yml")

    def get_run_sh_path(self, language: str, version: str, package_manager: str) -> str:
        """Get the path to the run.sh file."""
        return os.path.join(SETUP_DIR, f"{language}-{version}-{package_manager}", "run.sh")

    def get_tech_dir(self, language: str, version: str, package_manager: str) -> str:
        """Get the directory for the technology."""
        return os.path.join(SETUP_DIR, f"{language}-{version}-{package_manager}")
