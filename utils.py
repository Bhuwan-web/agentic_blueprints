"""Utility functions for the application.

This module contains utility functions for logging, file operations, and other common tasks.
"""

import io
import json
import logging
import os
import sys
import tarfile
from logging import Formatter, StreamHandler, getLogger
from typing import Any, Dict, Optional, Union

import yaml

# Configure root logger
logger = getLogger(__name__)


def setup_logger(name: str = None) -> logging.Logger:
    """Set up and configure a logger.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    from config import LOG_FORMAT, LOG_LEVEL

    log = getLogger(name)
    log.setLevel(LOG_LEVEL)

    # Check if the logger already has handlers to avoid duplicates
    if not log.handlers:
        handler = StreamHandler(sys.stdout)
        handler.setLevel(LOG_LEVEL)
        formatter = Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.propagate = False  # Prevent duplicate logs

    return log


def json_to_yaml(json_data: Union[str, Dict[str, Any]]) -> str:
    """Convert JSON data to YAML string.

    Args:
        json_data: JSON data as string or dictionary.

    Returns:
        YAML formatted string.
    """
    if isinstance(json_data, str):
        # If input is a JSON string, parse it first
        data = json.loads(json_data)
    else:
        # If input is already a Python object (e.g., dict, list)
        data = json_data

    yaml_string = yaml.dump(data, default_flow_style=False, sort_keys=False)
    return yaml_string


def ensure_directory(directory_path: str) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to the directory to create.
    """
    os.makedirs(directory_path, exist_ok=True)


def create_tar_archive(file_path: str, archive_name: str = "run.sh") -> io.BytesIO:
    """Create a tar archive containing a file.

    Args:
        file_path: Path to the file to archive.
        archive_name: Name to use for the file in the archive.

    Returns:
        BytesIO object containing the tar archive.
    """
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        tar.add(file_path, arcname=archive_name)

    tar_buffer.seek(0)
    return tar_buffer


def read_file(file_path: str) -> str:
    """Read a file and return its contents.

    Args:
        file_path: Path to the file to read.

    Returns:
        Contents of the file as a string.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Write content to a file.

    Args:
        file_path: Path to the file to write.
        content: Content to write to the file.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def make_executable(file_path: str) -> None:
    """Make a file executable.

    Args:
        file_path: Path to the file to make executable.
    """
    os.chmod(file_path, 0o755)
