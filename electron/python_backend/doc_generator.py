"""
Documentation generator for The Engineer application.
Generates markdown documentation for the application.
"""

import os
import re
import inspect
import importlib
import markdown
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Modules to document
MODULES_TO_DOCUMENT = [
    'main',
    'search',
    'prompts',
    'settings',
    'code_analyzer',
    'export_import',
    'test_framework'
]

# Directory for documentation
DOCS_DIR = 'docs'

def ensure_docs_directory():
    """Ensure the docs directory exists"""
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR, exist_ok=True)
        logger.info(f"Created documentation directory: {DOCS_DIR}")
    
    # Create sections directories
    sections = ['modules', 'guides', 'api']
    for section in sections:
        section_dir = os.path.join(DOCS_DIR, section)
        if not os.path.exists(section_dir):
            os.makedirs(section_dir, exist_ok=True)
            logger.info(f"Created documentation section directory: {section_dir}")

def parse_docstring(docstring):
    """Parse a docstring into a description and parameter info"""
    if not docstring:
        return {'description': '', 'params': {}, 'returns': '', 'examples': []}
    
    # Clean up docstring
    docstring = inspect.cleandoc(docstring)
    
    # Extract description (everything up to the first parameter or empty line)
    lines = docstring.split('\n')
    description_lines = []
    for line in lines:
        if line.strip() == '' or line.strip().startswith(('Args:', 'Parameters:', 'Returns:', 'Example:')):
            break
        description_lines.append(line)
    
    description = '\n'.join(description_lines).strip()
    
    # Extract parameters
    params = {}
    param_pattern = re.compile(r'^\s*([\w_]+):\s*(.+)$')
    in_params_section = False
    current_param = None
    
    for line in lines:
        if line.strip() in ('Args:', 'Parameters:'):
            in_params_section = True
            continue
        elif line.strip() in ('Returns:', 'Raises:', 'Example:', 'Examples:'):
            in_params_section = False
            continue
        
        if in_params_section:
            if line.strip() == '':
                current_param = None
                continue
                
            # Check if this line defines a new parameter
            match = param_pattern.match(line)
            if match:
                param_name = match.group(1)
                param_desc = match.group(2)
                current_param = param_name
                params[param_name] = param_desc
            elif current_param and line.strip():
                # Continuation of previous parameter description
                params[current_param] += ' ' + line.strip()
    
    # Extract return info
    returns = ''
    in_returns_section = False
    for line in lines:
        if line.strip() == 'Returns:':
            in_returns_section = True
            continue
        elif line.strip() in ('Raises:', 'Example:', 'Examples:'):
            in_returns_section = False
            continue
        
        if in_returns_section and line.strip():
            returns += ' ' + line.strip()
    
    # Extract examples
    examples = []
    in_example_section = False
    current_example = []
    
    for line in lines:
        if line.strip() in ('Example:', 'Examples:'):
            in_example_section = True
            continue
        elif in_example_section and line.strip() == '' and current_example:
            examples.append('\n'.join(current_example))
            current_example = []
            continue
        
        if in_example_section and line.strip():
            current_example.append(line)
    
    if current_example:
        examples.append('\n'.join(current_example))
    
    return {
        'description': description,
        'params': params,
        'returns': returns.strip(),
        'examples': examples
    }

def generate_module_documentation(module_name):
    """Generate documentation for a module"""
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Get module docstring
        module_doc = inspect.getdoc(module) or "No module documentation available."
        
        # Documentation content
        content = f"# {module_name}\n\n{module_doc}\n\n"
        
        # Get all functions and classes
        functions = []
        classes = []
        
        for name, obj in inspect.getmembers(module):
            # Skip private members and imported objects
            if name.startswith('_') or inspect.getmodule(obj) != module:
                continue
            
            if inspect.isfunction(obj):
                functions.append((name, obj))
            elif inspect.isclass(obj):
                classes.append((name, obj))
        
        # Document functions
        if functions:
            content += "## Functions\n\n"
            
            for name, func in sorted(functions):
                # Get function signature
                try:
                    signature = str(inspect.signature(func))
                except ValueError:
                    signature = '(...)'
                
                content += f"### `{name}{signature}`\n\n"
                
                # Parse docstring
                docstring_info = parse_docstring(inspect.getdoc(func))
                
                # Add description
                if docstring_info['description']:
                    content += f"{docstring_info['description']}\n\n"
                else:
                    content += "No description available.\n\n"
                
                # Add parameters
                if docstring_info['params']:
                    content += "**Parameters:**\n\n"
                    for param_name, param_desc in docstring_info['params'].items():
                        content += f"- `{param_name}`: {param_desc}\n"
                    content += "\n"
                
                # Add return info
                if docstring_info['returns']:
                    content += f"**Returns:** {docstring_info['returns']}\n\n"
                
                # Add examples
                if docstring_info['examples']:
                    content += "**Examples:**\n\n"
                    for example in docstring_info['examples']:
                        content += f"```python\n{example}\n```\n\n"
                
                content += "---\n\n"
        
        # Document classes
        if classes:
            content += "## Classes\n\n"
            
            for name, cls in sorted(classes):
                content += f"### `{name}`\n\n"
                
                # Parse class docstring
                class_doc = parse_docstring(inspect.getdoc(cls))
                
                # Add description
                if class_doc['description']:
                    content += f"{class_doc['description']}\n\n"
                else:
                    content += "No description available.\n\n"
                
                # Get methods
                methods = inspect.getmembers(cls, predicate=inspect.isfunction)
                
                if methods:
                    content += "#### Methods\n\n"
                    
                    for method_name, method in sorted(methods):
                        # Skip private methods
                        if method_name.startswith('_'):
                            continue
                        
                        # Get method signature
                        try:
                            signature = str(inspect.signature(method))
                        except ValueError:
                            signature = '(...)'
                        
                        content += f"##### `{method_name}{signature}`\n\n"
                        
                        # Parse docstring
                        method_doc = parse_docstring(inspect.getdoc(method))
                        
                        # Add description
                        if method_doc['description']:
                            content += f"{method_doc['description']}\n\n"
                        else:
                            content += "No description available.\n\n"
                        
                        # Add parameters
                        if method_doc['params']:
                            content += "**Parameters:**\n\n"
                            for param_name, param_desc in method_doc['params'].items():
                                content += f"- `{param_name}`: {param_desc}\n"
                            content += "\n"
                        
                        # Add return info
                        if method_doc['returns']:
                            content += f"**Returns:** {method_doc['returns']}\n\n"
                        
                        # Add examples
                        if method_doc['examples']:
                            content += "**Examples:**\n\n"
                            for example in method_doc['examples']:
                                content += f"```python\n{example}\n```\n\n"
                        
                        content += "---\n\n"
                
                content += "---\n\n"
        
        # Save documentation to file
        ensure_docs_directory()
        filepath = os.path.join(DOCS_DIR, 'modules', f"{module_name}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Generated documentation for module: {module_name}")
        return filepath
    
    except ImportError:
        logger.error(f"Could not import module: {module_name}")
        return None
    except Exception as e:
        logger.error(f"Error generating documentation for {module_name}: {str(e)}")
        return None

def generate_index_page():
    """Generate the documentation index page"""
    content = f"""# The Engineer Documentation

**Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

The Engineer is a specialized Claude assistant interface designed to help you work with your code and projects. This powerful tool connects to the Claude AI system to provide code analysis, suggestions, and improvements.

## Features

- Interactive chat with Claude using the Anthropic API
- File browsing and viewing across your projects
- Code analysis and enhancement recommendations with language-specific tools
- Conversation history management with search capabilities
- Multiple domain-specific system prompts for different tasks
- Persistent settings storage
- Export/import conversation functionality in multiple formats
- Web and console interfaces

## Modules

"""
    
    # Add links to module documentation
    for module in MODULES_TO_DOCUMENT:
        content += f"- [{module}](modules/{module}.md): "
        
        # Try to get the module description
        try:
            mod = importlib.import_module(module)
            doc = inspect.getdoc(mod)
            if doc:
                # Get the first line of the docstring
                first_line = doc.split('\n')[0].strip()
                content += first_line
        except:
            pass
        
        content += "\n"
    
    content += """
## Usage Guides

- [Getting Started](guides/getting_started.md)
- [Web Interface](guides/web_interface.md)
- [Console Interface](guides/console_interface.md)
- [Code Analysis](guides/code_analysis.md)
- [Using Domains](guides/using_domains.md)
- [Exporting Conversations](guides/exporting.md)
"""
    
    # Save the index page
    ensure_docs_directory()
    filepath = os.path.join(DOCS_DIR, 'index.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Generated documentation index page")
    return filepath

def generate_usage_guides():
    """Generate usage guide documentation"""
    guides = {
        'getting_started': {
            'title': 'Getting Started',
            'content': """# Getting Started with The Engineer

The Engineer is a specialized Claude assistant interface that helps you with software development tasks. This guide will help you get started with the application.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your Anthropic API key**:
   - Get an API key from [Anthropic](https://www.anthropic.com/)
   - Set it as an environment variable: `export ANTHROPIC_API_KEY=your_key_here`

3. **Run the application**:
   ```bash
   python main.py
   ```
   This will start the application and prompt you to choose between the console or web interface.

## Choose an Interface

The Engineer offers two different interfaces:

1. **Console Interface**: A terminal-based interface that's great for command-line users
2. **Web Interface**: A browser-based UI that's better for visual interaction

To start directly in web interface mode:
```bash
python main.py --web
```

## Basic Commands

Here are some basic commands to get you started:

- `/help` - Show available commands
- `/save` - Save the current conversation
- `/list` - List saved conversations
- `/domains` - List available domain-specific prompts
- `/projects` - List all your projects
- `/files` - List files in the current project
- `/analyze` - Analyze code in the current project

## Next Steps

- Check out the [Web Interface Guide](web_interface.md) or [Console Interface Guide](console_interface.md)
- Learn about [Code Analysis](code_analysis.md) capabilities
- Explore [Domain-Specific Prompts](using_domains.md) for different tasks
"""
        },
        'web_interface': {
            'title': 'Web Interface Guide',
            'content': """# Web Interface Guide

The Engineer's web interface provides a browser-based experience for interacting with Claude and your code.

## Starting the Web Interface

To start the web interface:

```bash
python main.py --web
```

This will start a local web server on port 8080. Open your browser and navigate to:

```
http://localhost:8080
```

## Interface Overview

The web interface consists of:

1. **Chat Area**: Shows your conversation with Claude
2. **Input Box**: Type your messages or commands here
3. **Command Reference**: Quick reference for available commands

## Available Commands

### Conversation Commands

- `/save` - Save the conversation
- `/list` - List saved conversations
- `/search <query>` - Search current conversation
- `/search saved <query>` - Search saved conversations
- `/export [format]` - Export conversation (json, txt, md, html, csv, all)
- `/import <filepath>` - Import conversation from file
- `/clear` - Clear current conversation

### Domain Commands

- `/domains` - List available domains
- `/domain <name>` - Switch to domain
- `/domain default` - Use default system prompt
- `/create_domain <name> <prompt>` - Create a new domain

### Settings Commands

- `/settings` - View all settings
- `/setting <key> <value>` - Update a setting
- `/reset_settings` - Reset to defaults

### Project Commands

- `/projects` - List all your projects
- `/files [project]` - List files in a project
- `/read [project] [file]` - View file contents
- `/analyze [project] [pattern]` - Analyze files

## Tips for the Web Interface

- The web interface formats code blocks automatically with syntax highlighting
- Use the Enter key to send messages
- The chat history is preserved during your session
- For long-running operations, wait for the "thinking" indicator to disappear
"""
        },
        'console_interface': {
            'title': 'Console Interface Guide',
            'content': """# Console Interface Guide

The Engineer's console interface provides a terminal-based experience for interacting with Claude and your code.

## Starting the Console Interface

To start the console interface (default):

```bash
python main.py
```

## Available Commands

### Conversation Management

- `save [filename]` - Save conversation (optional custom filename)
- `list` - List saved conversations
- `load <number>` - Load conversation by number
- `history` - Show conversation history
- `clear` - Clear current conversation
- `exit` - Exit the application

### Search Commands

- `search <query>` - Search current conversation
- `search saved <query>` - Search all saved conversations

### Domain Commands

- `domains` - List available domain prompts
- `domain <name>` - Switch to a specific domain
- `domain default` - Reset to default domain

### Settings Commands

- `settings` - View all current settings
- `setting <key> <value>` - Update a specific setting
- `reset_settings` - Reset all settings to defaults

### Export/Import Commands

- `export [format]` - Export conversation (json, txt, md, html, csv, all)
- `import <filepath>` - Import conversation from file

### Project Commands

- `projects` - List all your projects
- `files [project]` - List files in a project
- `read [project] [file]` - View file contents
- `analyze [project] [pattern]` - Analyze files
- `web` - Switch to web interface mode

## Tips for the Console Interface

- Use the Up/Down arrow keys to navigate through command history
- You can use Tab completion for commands in many terminals
- Prefix special commands with their name (e.g., `search`, `domain`)
- Regular text without a command prefix will be sent to Claude as a message
"""
        },
        'code_analysis': {
            'title': 'Code Analysis Guide',
            'content': """# Code Analysis Guide

The Engineer includes powerful code analysis capabilities that can help you understand, improve, and maintain your codebase.

## Basic Analysis

To analyze code in your current project:

```
/analyze . *.py
```

This will:
1. Find all Python files in the current project
2. Analyze each file for metrics, complexity, and patterns
3. Generate an automated analysis report
4. Send the files and report to Claude for additional insights

## Language Support

The analyzer supports multiple languages with language-specific checks:

- Python
- JavaScript/TypeScript
- Java/C#
- C/C++
- Go
- Rust
- PHP
- Ruby
- HTML/CSS
- And more...

## Analysis Report

The analysis report includes:

1. **Code Metrics**:
   - Lines of code (total, code, comments, blank)
   - Function/method count
   - Class count
   - Import/dependency count

2. **Complexity Analysis**:
   - Cyclomatic complexity estimation
   - Maximum nesting depth
   - Long functions that may need refactoring

3. **Pattern Detection**:
   - Potential issues (e.g., hard-coded credentials, bare except clauses)
   - Warnings (e.g., print statements, console.log)
   - Good practices (e.g., context managers, async/await)

4. **Recommendations**:
   - Language-specific improvement suggestions
   - General code quality recommendations

## Using the Analysis Results

After getting the analysis:

1. Review the automated metrics and patterns
2. Read Claude's additional insights
3. Prioritize issues based on severity
4. Make incremental improvements to address the findings

## Advanced Analysis

You can target specific file patterns:

- Analyze JavaScript files: `/analyze . *.js`
- Analyze a specific directory: `/analyze . src/*.py`
- Analyze multiple file types: `/analyze . *.{js,ts}`

The Engineer will provide language-appropriate analysis for each file type.
"""
        },
        'using_domains': {
            'title': 'Using Domain-Specific Prompts',
            'content': """# Using Domain-Specific Prompts

The Engineer supports domain-specific system prompts that can tailor Claude's behavior for different types of tasks.

## Available Domains

To see all available domains:

```
/domains
```

The default domains include:

- **development**: Focused on software development, debugging, and code improvement
- **data_science**: Specialized for data analysis, machine learning, and visualization
- **devops**: Tailored for infrastructure, deployment, and operations
- **security**: Focused on security best practices and vulnerability detection

## Switching Domains

To switch to a specific domain:

```
/domain development
```

To return to the default prompt:

```
/domain default
```

## Creating Custom Domains

You can create your own custom domain prompts:

```
/create_domain my_domain "Your custom system prompt here..."
```

The custom prompt should provide instructions for Claude about how to behave in this domain.

## Domain Persistence

Your selected domain persists between sessions through the settings system. When you restart the application, it will use the last domain you selected.

## Tips for Using Domains

- Use the **development** domain for general coding tasks
- Switch to **data_science** when working with data analysis or ML code
- Use **devops** when dealing with infrastructure or deployment
- Switch to **security** when focused on code security review
- Create custom domains for specialized workflows or projects

## Example Domain Uses

**Development domain**:
```
/domain development
What's wrong with this code?
def calculate_average(nums):
    return sum(nums) / len(nums)
```

**Data Science domain**:
```
/domain data_science
How would I visualize this data?
import pandas as pd
df = pd.read_csv('data.csv')
```

**Security domain**:
```
/domain security
Review this login function for security issues:
def login(username, password):
    user = db.query("SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'")
    return user
```
"""
        },
        'exporting': {
            'title': 'Exporting and Importing Conversations',
            'content': """# Exporting and Importing Conversations

The Engineer allows you to export conversations in various formats and import them later.

## Exporting Conversations

To export the current conversation:

```
/export [format]
```

Available formats:

- **json**: JSON format with full message data (default)
- **txt**: Plain text format
- **md**: Markdown format
- **html**: HTML format with styling
- **csv**: CSV format for spreadsheet applications
- **all**: Export in all formats as a ZIP file

Examples:

```
/export json
/export md
/export all
```

All exports are saved to the `exports` directory.

## Importing Conversations

To import a previously exported conversation:

```
/import [filepath]
```

Example:

```
/import exports/conversation_20240501_123045.json
```

The current conversation will be replaced with the imported one.

## Export Features

Exported conversations include:

- **JSON**: Full conversation data with metadata
- **Markdown**: Formatted with headers and code blocks
- **HTML**: Styled HTML with syntax highlighting
- **Text**: Simple text format for readability
- **CSV**: Tabular format for analysis

## Using Exported Data

Exported conversations can be used for:

1. **Backup**: Save important conversations
2. **Sharing**: Send conversations to colleagues
3. **Documentation**: Include in project documentation
4. **Analysis**: Analyze conversation patterns
5. **Reporting**: Generate reports from conversations

## Tips for Exporting

- Use **JSON** format for complete data preservation
- Use **Markdown** for documentation purposes
- Use **HTML** for sharing with non-technical users
- Use **all** to get all formats at once in a ZIP file
"""
        }
    }
    
    # Generate guide files
    ensure_docs_directory()
    
    for guide_id, guide_info in guides.items():
        filepath = os.path.join(DOCS_DIR, 'guides', f"{guide_id}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(guide_info['content'])
        
        logger.info(f"Generated guide: {guide_id}")

def generate_html_docs():
    """Generate HTML documentation from markdown files"""
    # Ensure the HTML output directory exists
    html_dir = os.path.join(DOCS_DIR, 'html')
    if not os.path.exists(html_dir):
        os.makedirs(html_dir, exist_ok=True)
    
    # CSS for HTML docs
    css = """
    body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    pre {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
    }
    code {
        font-family: monospace;
        background-color: #f5f5f5;
        padding: 2px 4px;
        border-radius: 3px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
    }
    a {
        color: #3498db;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .content {
        margin-top: 20px;
    }
    .sidebar {
        position: fixed;
        top: 0;
        left: 0;
        width: 250px;
        height: 100%;
        overflow-y: auto;
        background-color: #f5f5f5;
        padding: 20px;
    }
    .main {
        margin-left: 270px;
    }
    """
    
    # Create CSS file
    css_path = os.path.join(html_dir, 'style.css')
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
    
    # Convert all markdown files to HTML
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                
                # Determine output path
                rel_path = os.path.relpath(md_path, DOCS_DIR)
                html_path = os.path.join(html_dir, rel_path.replace('.md', '.html'))
                
                # Create output directory if needed
                os.makedirs(os.path.dirname(html_path), exist_ok=True)
                
                # Read markdown content
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # Convert to HTML
                html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
                
                # Create HTML file with template
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Engineer - {os.path.splitext(file)[0]}</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div class="content">
        {html_content}
    </div>
</body>
</html>
""")
    
    logger.info("Generated HTML documentation")

def generate_documentation():
    """Generate full documentation for The Engineer"""
    ensure_docs_directory()
    
    # Generate module documentation
    for module in MODULES_TO_DOCUMENT:
        generate_module_documentation(module)
    
    # Generate usage guides
    generate_usage_guides()
    
    # Generate index page
    index_page = generate_index_page()
    
    # Generate HTML documentation
    generate_html_docs()
    
    logger.info(f"Documentation generation complete. Index page: {index_page}")
    return index_page

if __name__ == '__main__':
    # Generate documentation
    generate_documentation()