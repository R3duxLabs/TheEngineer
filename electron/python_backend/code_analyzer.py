"""
Code analysis utilities for The Engineer application.
Provides language-specific analysis tools for different programming languages.
"""

import os
import re
import logging
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

# Language detection patterns
LANGUAGE_PATTERNS = {
    'python': [r'\.py$', r'\.pyi$', r'\.ipynb$'],
    'javascript': [r'\.js$', r'\.jsx$', r'\.mjs$'],
    'typescript': [r'\.ts$', r'\.tsx$', r'\.d\.ts$'],
    'html': [r'\.html$', r'\.htm$', r'\.xhtml$'],
    'css': [r'\.css$', r'\.scss$', r'\.sass$', r'\.less$'],
    'java': [r'\.java$', r'\.class$'],
    'c': [r'\.c$', r'\.h$'],
    'cpp': [r'\.cpp$', r'\.hpp$', r'\.cc$', r'\.cxx$'],
    'csharp': [r'\.cs$'],
    'go': [r'\.go$'],
    'rust': [r'\.rs$'],
    'php': [r'\.php$'],
    'ruby': [r'\.rb$'],
    'swift': [r'\.swift$'],
    'kotlin': [r'\.kt$', r'\.kts$'],
    'shell': [r'\.sh$', r'\.bash$', r'\.zsh$'],
    'sql': [r'\.sql$'],
    'markdown': [r'\.md$', r'\.markdown$'],
    'json': [r'\.json$'],
    'yaml': [r'\.yml$', r'\.yaml$'],
    'xml': [r'\.xml$', r'\.svg$'],
    'dockerfile': [r'Dockerfile$'],
    'makefile': [r'Makefile$', r'\.mk$'],
    'text': [r'\.txt$', r'\.log$'],
}

# Language-specific comment patterns
COMMENT_PATTERNS = {
    'python': [r'^\s*#.*$', r'""".*?"""', r"'''.*?'''"],
    'javascript': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'typescript': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'html': [r'<!--.*?-->'],
    'css': [r'\/\*.*?\*\/'],
    'java': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'c': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'cpp': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'csharp': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'go': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'rust': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'php': [r'^\s*\/\/.*$', r'\/\*.*?\*\/', r'^\s*#.*$'],
    'ruby': [r'^\s*#.*$', r'=begin.*?=end'],
    'swift': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'kotlin': [r'^\s*\/\/.*$', r'\/\*.*?\*\/'],
    'shell': [r'^\s*#.*$'],
    'sql': [r'^\s*--.*$', r'\/\*.*?\*\/'],
    'markdown': [],
    'json': [],
    'yaml': [r'^\s*#.*$'],
    'xml': [r'<!--.*?-->'],
    'dockerfile': [r'^\s*#.*$'],
    'makefile': [r'^\s*#.*$'],
    'text': [],
}

def detect_language(file_path):
    """Detect programming language from file extension"""
    file_path = file_path.lower()
    
    for language, patterns in LANGUAGE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, file_path):
                return language
    
    # Default to text if no pattern matches
    return 'text'

def get_language_metrics(content, language):
    """Get basic metrics about code in a specific language"""
    metrics = {
        'lines_total': 0,
        'lines_code': 0,
        'lines_comment': 0,
        'lines_blank': 0,
        'function_count': 0,
        'class_count': 0,
        'import_count': 0,
        'todo_count': 0,
    }
    
    # Count total lines
    lines = content.split('\n')
    metrics['lines_total'] = len(lines)
    
    # Count blank lines
    metrics['lines_blank'] = sum(1 for line in lines if not line.strip())
    
    # Count comment lines based on language
    if language in COMMENT_PATTERNS:
        comment_patterns = COMMENT_PATTERNS[language]
        for line in lines:
            for pattern in comment_patterns:
                if re.match(pattern, line):
                    metrics['lines_comment'] += 1
                    break
    
    # Calculate code lines
    metrics['lines_code'] = metrics['lines_total'] - metrics['lines_comment'] - metrics['lines_blank']
    
    # Language-specific metrics
    if language == 'python':
        # Count Python functions, classes, imports
        metrics['function_count'] = len(re.findall(r'^\s*def\s+\w+\s*\(', content, re.MULTILINE))
        metrics['class_count'] = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
        metrics['import_count'] = len(re.findall(r'^\s*import\s+|^\s*from\s+\w+\s+import', content, re.MULTILINE))
    
    elif language in ['javascript', 'typescript']:
        # Count JS/TS functions, classes, imports
        metrics['function_count'] = len(re.findall(r'function\s+\w+\s*\(|const\s+\w+\s*=\s*\([^)]*\)\s*=>|const\s+\w+\s*=\s*function', content, re.MULTILINE))
        metrics['class_count'] = len(re.findall(r'class\s+\w+', content, re.MULTILINE))
        metrics['import_count'] = len(re.findall(r'import\s+|require\(', content, re.MULTILINE))
    
    elif language in ['java', 'csharp']:
        # Count Java/C# functions, classes
        metrics['function_count'] = len(re.findall(r'(public|private|protected|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(\{?|[^;])', content, re.MULTILINE))
        metrics['class_count'] = len(re.findall(r'class\s+\w+', content, re.MULTILINE))
        metrics['import_count'] = len(re.findall(r'import\s+', content, re.MULTILINE))
    
    # Count TODOs in any language
    metrics['todo_count'] = len(re.findall(r'TODO|FIXME', content, re.IGNORECASE))
    
    return metrics

def analyze_complexity(content, language):
    """Analyze code complexity"""
    complexity_info = {
        'cyclomatic_complexity': 'low',
        'nesting_depth_max': 0,
        'long_functions': [],
        'complex_areas': []
    }
    
    # Count conditional statements and loops
    if language in ['python', 'javascript', 'typescript', 'java', 'csharp', 'cpp', 'c', 'go', 'php']:
        # Count conditionals and loops
        conditions = len(re.findall(r'\sif\s|\selse\s|\selif\s|\sswitch\s|\scase\s|\?|&&|\|\|', content))
        loops = len(re.findall(r'\sfor\s|\swhile\s|\sforeach\s|\sdo\s', content))
        
        # Simple complexity heuristic
        complexity = conditions + loops
        
        if complexity > 100:
            complexity_info['cyclomatic_complexity'] = 'very high'
        elif complexity > 50:
            complexity_info['cyclomatic_complexity'] = 'high'
        elif complexity > 20:
            complexity_info['cyclomatic_complexity'] = 'medium'
        
        # Estimate maximum nesting depth
        lines = content.split('\n')
        current_depth = 0
        max_depth = 0
        
        for line in lines:
            # Count opening braces/indentation increase
            if re.search(r'\{\s*$', line) or re.search(r':\s*$', line):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            # Count closing braces/indentation decrease
            if re.search(r'^\s*\}', line) or (language == 'python' and re.search(r'^\S', line) and current_depth > 0):
                current_depth = max(0, current_depth - 1)
        
        complexity_info['nesting_depth_max'] = max_depth
        
        # Identify long functions (over 50 lines)
        if language == 'python':
            function_pattern = r'def\s+(\w+)\s*\([^)]*\):(?:\s*"""[\s\S]*?""")?([\s\S]*?)(?=\n\S|$)'
            for match in re.finditer(function_pattern, content):
                func_name = match.group(1)
                func_body = match.group(2)
                if func_body.count('\n') > 50:
                    complexity_info['long_functions'].append(func_name)
        
        elif language in ['javascript', 'typescript']:
            function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{([\s\S]*?)(?=\n\}|$)'
            for match in re.finditer(function_pattern, content):
                func_name = match.group(1)
                func_body = match.group(2)
                if func_body.count('\n') > 50:
                    complexity_info['long_functions'].append(func_name)
    
    return complexity_info

def analyze_code(content, file_path):
    """Analyze code and return structured information"""
    language = detect_language(file_path)
    
    analysis = {
        'language': language,
        'file_name': os.path.basename(file_path),
        'metrics': get_language_metrics(content, language),
        'complexity': analyze_complexity(content, language),
        'patterns': detect_patterns(content, language)
    }
    
    return analysis

def detect_patterns(content, language):
    """Detect common patterns, anti-patterns and issues in code"""
    patterns = {
        'issues': [],
        'warnings': [],
        'good_practices': []
    }
    
    # Common issues across languages
    if len(content) > 100000:
        patterns['warnings'].append('File is very large (over 100KB), consider breaking it down')
    
    if re.search(r'TODO|FIXME', content, re.IGNORECASE):
        patterns['warnings'].append('Contains TODO or FIXME comments that need to be addressed')
    
    # Hard-coded credentials check
    if re.search(r'password\s*=|api[_\s]*key\s*=|secret\s*=|token\s*=', content, re.IGNORECASE):
        patterns['issues'].append('Potential hard-coded credentials or secrets found')
    
    # Language-specific checks
    if language == 'python':
        # Python-specific patterns
        if re.search(r'except\s*:', content):
            patterns['issues'].append('Bare except clause - should catch specific exceptions')
        
        if re.search(r'import\s*\*', content):
            patterns['warnings'].append('Wildcard imports should be avoided')
        
        if re.search(r'^\s*print\s*\(', content, re.MULTILINE):
            patterns['warnings'].append('Contains print statements which may need to be replaced with proper logging')
        
        if re.search(r'def\s+__init__\s*\(\s*self\s*\)', content):
            patterns['warnings'].append('Empty __init__ method that could be removed')
        
        # Good practices
        if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', content):
            patterns['good_practices'].append('Uses if __name__ == "__main__" idiom')
        
        if re.search(r'with\s+', content):
            patterns['good_practices'].append('Uses context managers (with statement)')
    
    elif language in ['javascript', 'typescript']:
        # JavaScript/TypeScript specific patterns
        if re.search(r'console\.log', content):
            patterns['warnings'].append('Contains console.log statements that may need to be removed or replaced')
        
        if re.search(r'var\s+', content):
            patterns['warnings'].append('Uses var instead of const/let')
        
        if re.search(r'==(?!=)', content):
            patterns['warnings'].append('Uses loose equality (==) instead of strict equality (===)')
        
        if re.search(r'eval\s*\(', content):
            patterns['issues'].append('Uses eval() which can be unsafe')
        
        # Good practices
        if language == 'typescript' or re.search(r'/\*\*[\s\S]*?\*/', content):
            patterns['good_practices'].append('Has JSDoc or TypeScript type annotations')
        
        if re.search(r'async\s+|await\s+', content):
            patterns['good_practices'].append('Uses async/await')
        
        if re.search(r'import\s+.*\s+from\s+', content):
            patterns['good_practices'].append('Uses ES modules')
    
    return patterns

def format_analysis_report(analysis, file_path):
    """Format code analysis into a readable report"""
    language = analysis['language']
    metrics = analysis['metrics']
    complexity = analysis['complexity']
    patterns = analysis['patterns']
    
    report = f"# Code Analysis Report: {os.path.basename(file_path)}\n\n"
    
    # Basic information
    report += f"**Language:** {language.capitalize()}\n"
    report += f"**Lines of code:** {metrics['lines_code']} (total: {metrics['lines_total']})\n"
    report += f"**Comments:** {metrics['lines_comment']} lines ({metrics['lines_comment']/max(1, metrics['lines_total'])*100:.1f}%)\n"
    
    # Code structure
    if language in ['python', 'javascript', 'typescript', 'java', 'csharp']:
        report += f"**Functions/Methods:** {metrics['function_count']}\n"
        report += f"**Classes:** {metrics['class_count']}\n"
        report += f"**Imports/Dependencies:** {metrics['import_count']}\n"
    
    # Complexity
    report += f"\n## Complexity\n"
    report += f"**Overall complexity:** {complexity['cyclomatic_complexity']}\n"
    report += f"**Maximum nesting depth:** {complexity['nesting_depth_max']}\n"
    
    if complexity['long_functions']:
        report += f"\n**Long functions** (may need refactoring):\n"
        for func in complexity['long_functions']:
            report += f"- `{func}`\n"
    
    # Issues and warnings
    if patterns['issues'] or patterns['warnings']:
        report += f"\n## Issues and Warnings\n"
        
        if patterns['issues']:
            report += "\n**Potential issues:**\n"
            for issue in patterns['issues']:
                report += f"- {issue}\n"
        
        if patterns['warnings']:
            report += "\n**Warnings:**\n"
            for warning in patterns['warnings']:
                report += f"- {warning}\n"
    
    # Good practices
    if patterns['good_practices']:
        report += f"\n## Good Practices\n"
        for practice in patterns['good_practices']:
            report += f"- {practice}\n"
    
    # Language-specific recommendations
    report += f"\n## Recommendations\n"
    
    if language == 'python':
        if metrics['lines_comment'] / max(1, metrics['lines_total']) < 0.1:
            report += "- Consider adding more documentation (current comment ratio is low)\n"
        if 'Bare except clause' in str(patterns['issues']):
            report += "- Replace bare `except:` clauses with specific exception types\n"
        if 'print statements' in str(patterns['warnings']):
            report += "- Use logging module instead of print statements\n"
    
    elif language in ['javascript', 'typescript']:
        if 'console.log' in str(patterns['warnings']):
            report += "- Replace console.log with proper logging\n"
        if 'loose equality' in str(patterns['warnings']):
            report += "- Use strict equality (===) instead of loose equality (==)\n"
    
    # General recommendations
    if complexity['cyclomatic_complexity'] in ['high', 'very high']:
        report += "- Consider refactoring complex areas of the code\n"
    
    if complexity['nesting_depth_max'] > 4:
        report += "- Reduce nesting depth to improve readability\n"
    
    if metrics['todo_count'] > 0:
        report += f"- Address {metrics['todo_count']} TODO/FIXME comments\n"
    
    return report

def analyze_directory(directory_path, file_patterns=None):
    """
    Analyze all code files in a directory and generate a summary report
    
    Args:
        directory_path: Path to the directory to analyze
        file_patterns: List of file patterns to include (e.g., ['*.py', '*.js'])
        
    Returns:
        A string containing the analysis report
    """
    if not os.path.exists(directory_path):
        return f"Directory not found: {directory_path}"
    
    if not os.path.isdir(directory_path):
        return f"Not a directory: {directory_path}"
    
    # Default to common code file types if not specified
    if not file_patterns:
        file_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.java', '*.c', '*.cpp', '*.cs']
    
    # Counters for summary
    language_counts = defaultdict(int)
    total_lines = 0
    total_code_lines = 0
    total_files = 0
    issues_count = 0
    warnings_count = 0
    
    # Analyze each file
    file_analyses = []
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            language = detect_language(file_path)
            
            # Skip if no pattern matches or language is 'text'
            if language == 'text' and not any(file.endswith(p.replace('*', '')) for p in file_patterns):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                analysis = analyze_code(content, file_path)
                file_analyses.append((file_path, analysis))
                
                # Update counters
                language_counts[language] += 1
                total_lines += analysis['metrics']['lines_total']
                total_code_lines += analysis['metrics']['lines_code']
                total_files += 1
                issues_count += len(analysis['patterns']['issues'])
                warnings_count += len(analysis['patterns']['warnings'])
                
            except Exception as e:
                logger.warning(f"Error analyzing file {file_path}: {str(e)}")
    
    # Generate summary report
    report = f"# Code Analysis Summary for {os.path.basename(directory_path)}\n\n"
    
    report += f"Analyzed {total_files} files, {total_code_lines} lines of code\n\n"
    
    report += "## Language Breakdown\n"
    for language, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"- {language.capitalize()}: {count} files\n"
    
    report += f"\n## Overall Health\n"
    report += f"- Issues found: {issues_count}\n"
    report += f"- Warnings found: {warnings_count}\n"
    
    # Add detailed file reports
    if file_analyses:
        report += "\n## File Analysis\n"
        
        # Sort files by issues count (most issues first)
        file_analyses.sort(key=lambda x: len(x[1]['patterns']['issues']) + len(x[1]['patterns']['warnings']), reverse=True)
        
        # Only include detailed reports for files with issues or warnings
        for file_path, analysis in file_analyses:
            if analysis['patterns']['issues'] or analysis['patterns']['warnings']:
                rel_path = os.path.relpath(file_path, directory_path)
                report += f"\n### {rel_path}\n"
                
                if analysis['patterns']['issues']:
                    report += "**Issues:**\n"
                    for issue in analysis['patterns']['issues']:
                        report += f"- {issue}\n"
                
                if analysis['patterns']['warnings']:
                    report += "**Warnings:**\n"
                    for warning in analysis['patterns']['warnings']:
                        report += f"- {warning}\n"
    
    return report