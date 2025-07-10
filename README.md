# Technology Setup Blueprint Generator

## 🌟 Introduction
Welcome to the Technology Setup Blueprint Generator! This tool helps you generate Docker setup blueprints for various technology stacks. It creates the necessary configuration files and setup scripts to containerize your applications with the specified technology stack, version, and package manager.

## 🎯 Project Scope
This project provides automated generation of Docker setup configurations for different technology stacks, including:

- Language version management
- Package manager setup
- Base image optimization (supports both Alpine and Debian)
- Dependency management

## 🛠️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/agentic_blueprints.git
   cd agentic_blueprints
   ```

2. Set up your environment using UV (recommended):
   ```bash
   uv pip install -r requirements.txt
   ```

## 🚀 Usage

Generate a new technology setup by running:

```bash
python main.py <technology> <version> <package-manager>
```

### Examples:

1. For Python 3.13 with PyPI:
   ```bash
   python main.py python 3.13 pypi
   ```

2. For Node.js 18 with npm:
   ```bash
   python main.py node 18 npm
   ```

## 📂 Output Structure
For each technology setup, the generator creates:
- `run.sh`: Main setup script for the specified technology
- `blueprint.yml`: Configuration file with metadata about the setup

## 🔧 Customization
You can find the generated files in the `setup/` directory, organized by technology, version, and package manager. Feel free to modify these files to suit your specific needs.

## 💡 Purpose
This tool aims to:
- Streamline the process of setting up development environments
- Ensure consistent configurations across different projects
- Support multiple technology versions and package managers
- Provide a solid foundation for containerized applications

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit issues and enhancement requests.

## ✨ Getting Help
If you encounter any issues or have questions, please open an issue in the repository.