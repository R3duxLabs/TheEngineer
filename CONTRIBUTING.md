# Contributing to The Engineer

Thank you for your interest in contributing to The Engineer! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/TheEngineer.git`
3. Set up your development environment
4. Run the setup script: `bash setup.sh`

## Development Environment Setup

1. Make sure you have Python 3.11+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your Anthropic API key as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

## Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests to ensure your changes don't break existing functionality:
   ```bash
   python -m unittest discover -s . -p "test_*.py"
   ```
4. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "Add feature: your feature description"
   ```

## Pull Request Process

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Go to the original repository and create a new pull request
3. Describe your changes and why they should be included
4. Wait for a maintainer to review your pull request

## Adding New Features

When adding new features:
- Make sure to update documentation
- Add appropriate tests
- Follow the existing code style
- Update the README if necessary

## Reporting Issues

If you find a bug or have a suggestion:
1. Check if the issue already exists in the issues section
2. If not, create a new issue with a descriptive title and detailed description
3. Include steps to reproduce the issue if it's a bug

## Code Style

Please follow these guidelines for code style:
- Use 4 spaces for indentation
- Follow PEP 8 guidelines for Python code
- Include docstrings for functions and classes
- Use meaningful variable and function names

Thank you for contributing!