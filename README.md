# Blueprint Generator

A tool for generating and validating technology installation blueprints.

## Overview

Blueprint Generator is a multi-agent system that creates, validates, and fixes installation scripts for various technologies. It uses AI agents to:

1. Generate installation scripts (`run.sh`) for specified technologies
2. Validate the scripts by running them in Docker containers
3. Fix any issues that arise during validation

## Architecture

The system uses a multi-agent architecture with three main components:

1. **Blueprint Agent**: Generates initial installation scripts
2. **Validator Agent**: Validates and fixes installation scripts
3. **Router Agent**: Orchestrates the workflow between agents

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/blueprint-generator.git
cd blueprint-generator

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Generate a blueprint for Python 3.11 with PyPI
python main.py python 3.11 pypi

# Generate a blueprint for Node.js 18 with NPM
python main.py node 18 npm

# Generate a blueprint for Java 21 with Maven
python main.py java 21 maven
```

## Project Structure

```
.
├── agents.py         # Agent definitions
├── config.py         # Configuration settings
├── examples/         # Example scripts
├── main.py           # Command-line interface
├── models.py         # Data models
├── setup/            # Generated blueprints
├── tools.py          # Agent tools
└── utils.py          # Utility functions
```

## How It Works

1. The user specifies a technology, version, and package manager
2. The router agent initiates the blueprint generation process
3. The blueprint agent creates an installation script
4. The script is validated in a Docker container
5. If validation fails, the validator agent attempts to fix the script
6. The process repeats until success or the maximum number of attempts is reached

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.