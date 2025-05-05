"""
A simplified version of the web interface for demonstration purposes.
"""

import http.server
import socketserver
import os

# Create the HTML content
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>The Engineer - Demo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f7;
            color: #333;
        }
        h1 {
            color: #4361ee;
            text-align: center;
            margin-bottom: 20px;
            font-size: 28px;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .chat-container {
            height: 400px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 20px;
            background-color: #fff;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 8px;
            max-width: 80%;
        }
        .user {
            background-color: #f1faee;
            margin-left: auto;
            border-left: 3px solid #4361ee;
        }
        .claude {
            background-color: #f0f7ff;
            border-left: 3px solid #4cc9f0;
        }
        .message strong {
            font-weight: 600;
            margin-bottom: 5px;
            display: block;
        }
        .input-container {
            display: flex;
            margin-bottom: 20px;
        }
        input {
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #dee2e6;
            border-radius: 8px 0 0 8px;
            font-size: 16px;
        }
        button {
            padding: 10px 20px;
            background-color: #4361ee;
            color: white;
            border: none;
            border-radius: 0 8px 8px 0;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
        }
        button:hover {
            background-color: #3a56d4;
        }
        .agent-switcher {
            margin-bottom: 20px;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .agent-switcher h3 {
            margin-top: 0;
            color: #4361ee;
        }
        .agent-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }
        .agent-button {
            padding: 8px 16px;
            background-color: #fff;
            color: #4361ee;
            border: 1px solid #4361ee;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .agent-button:hover {
            background-color: #4361ee;
            color: white;
        }
        .agent-button.active {
            background-color: #4361ee;
            color: white;
        }
        .theme-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            background: none;
            border: none;
            color: #4361ee;
            font-size: 24px;
            cursor: pointer;
        }
        .demo-note {
            margin-top: 30px;
            padding: 15px;
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <button class="theme-toggle" id="theme-toggle">🌙</button>
    <h1>The Engineer</h1>
    
    <div class="container">
        <div class="agent-switcher">
            <h3>Current Agent: <span id="current-agent">Claude</span></h3>
            <div class="agent-buttons">
                <button class="agent-button active" data-agent="claude">Claude</button>
                <button class="agent-button" data-agent="code_expert">Code Expert</button>
                <button class="agent-button" data-agent="data_scientist">Data Scientist</button>
                <button class="agent-button" data-agent="creative_writer">Creative Writer</button>
                <button class="agent-button" data-agent="security_expert">Security Expert</button>
            </div>
        </div>
        
        <div class="chat-container" id="chat">
            <div class="message claude">
                <strong>Claude:</strong> Hello! I'm Claude, your AI assistant. How can I help you today?
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="message" placeholder="Type your message here...">
            <button id="send-button">Send</button>
        </div>
        
        <div class="demo-note">
            <strong>Demo Mode:</strong> This is a demonstration of the desktop app interface. In a full app store version, this would connect to the Claude API and provide a complete AI assistant experience with all the features shown in the UI.
        </div>
    </div>
    
    <script>
        // Sample responses for demo mode
        const demoResponses = {
            "claude": [
                "I'm Claude, the default assistant. I can help with a wide range of tasks and questions.",
                "As a general-purpose assistant, I can help with research, writing, coding, and more. What would you like to work on?",
                "Hello! I'm here to assist with whatever you need. How can I help you today?"
            ],
            "code_expert": [
                "As a Code Expert, I specialize in software development and technical problem-solving. Here's a solution to your coding challenge...",
                "Looking at this code, I notice a few optimization opportunities. First, we could refactor this loop to improve performance by...",
                "From a software architecture perspective, I'd recommend structuring your project with these components to improve maintainability..."
            ],
            "data_scientist": [
                "As a Data Scientist assistant, I'd approach this analysis by first examining the distribution of your variables, then applying appropriate statistical tests.",
                "For this visualization, I recommend using a scatter plot with a regression line to show the correlation between these variables.",
                "Based on your dataset characteristics, a Random Forest model might work well because it can handle non-linear relationships and categorical variables."
            ],
            "creative_writer": [
                "Your story has a compelling main character with clear motivations. To strengthen the narrative arc, consider adding more conflict in the second act...",
                "Here's a draft based on your outline. I've focused on vivid sensory details and varied sentence structure to create an engaging reading experience.",
                "For this marketing copy, I've incorporated emotional triggers, clear benefits, and a strong call to action while maintaining your brand voice."
            ],
            "security_expert": [
                "I've identified several potential security vulnerabilities in this code. The most critical issue is the unvalidated user input that could lead to SQL injection.",
                "For your authentication system, I recommend implementing multi-factor authentication, rate limiting, and secure password storage using bcrypt.",
                "Your infrastructure could be strengthened by implementing a zero-trust architecture, regular security scanning, and automated secret management."
            ]
        };
        
        // Current agent
        let currentAgent = "claude";
        
        // Theme state
        let darkMode = false;
        
        // Handle sending messages
        document.getElementById('send-button').addEventListener('click', sendMessage);
        document.getElementById('message').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        function sendMessage() {
            const input = document.getElementById('message');
            const message = input.value.trim();
            
            if (message === '') return;
            
            // Add user message to chat
            const chat = document.getElementById('chat');
            chat.innerHTML += `<div class="message user"><strong>You:</strong> ${message}</div>`;
            
            // Clear input
            input.value = '';
            
            // Scroll to bottom
            chat.scrollTop = chat.scrollHeight;
            
            // Simulate typing delay
            setTimeout(() => {
                // Get random response for current agent
                const responses = demoResponses[currentAgent];
                const response = responses[Math.floor(Math.random() * responses.length)];
                
                // Add Claude's response
                const agentName = document.getElementById('current-agent').textContent;
                chat.innerHTML += `<div class="message claude"><strong>${agentName}:</strong> ${response}</div>`;
                
                // Scroll to bottom again
                chat.scrollTop = chat.scrollHeight;
            }, 1000);
        }
        
        // Handle agent switching
        document.querySelectorAll('.agent-button').forEach(button => {
            button.addEventListener('click', function() {
                // Update active button
                document.querySelectorAll('.agent-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
                
                // Update current agent
                currentAgent = this.dataset.agent;
                
                // Update agent name display
                const agentName = this.textContent;
                document.getElementById('current-agent').textContent = agentName;
                
                // Add system message about agent switch
                const chat = document.getElementById('chat');
                chat.innerHTML += `<div class="message claude"><strong>System:</strong> Switched to ${agentName} agent.</div>`;
                
                // Scroll to bottom
                chat.scrollTop = chat.scrollHeight;
            });
        });
        
        // Handle theme toggle
        document.getElementById('theme-toggle').addEventListener('click', function() {
            darkMode = !darkMode;
            
            if (darkMode) {
                document.body.style.backgroundColor = '#121212';
                document.body.style.color = '#e9ecef';
                this.textContent = '☀️';
                
                // Add dark mode styles
                const style = document.createElement('style');
                style.id = 'dark-mode-styles';
                style.textContent = `
                    .container { background-color: #1e1e1e; }
                    .chat-container { background-color: #1e1e1e; border-color: #4a5568; }
                    .message.user { background-color: #1e2a23; }
                    .message.claude { background-color: #1a1d2d; }
                    input { background-color: #2d3748; color: #e9ecef; border-color: #4a5568; }
                    .agent-switcher { background-color: #2d3748; border-color: #4a5568; }
                    .agent-button { background-color: #1e1e1e; border-color: #4cc9f0; color: #4cc9f0; }
                    .agent-button.active { background-color: #4cc9f0; color: #1e1e1e; }
                    .theme-toggle { color: #4cc9f0; }
                    .demo-note { background-color: #2d3748; border-color: #f59e0b; color: #e9ecef; }
                `;
                document.head.appendChild(style);
            } else {
                document.body.style.backgroundColor = '#f5f5f7';
                document.body.style.color = '#333';
                this.textContent = '🌙';
                
                // Remove dark mode styles
                const darkStyles = document.getElementById('dark-mode-styles');
                if (darkStyles) {
                    darkStyles.remove();
                }
            }
        });
    </script>
</body>
</html>
"""

class DemoHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML.encode())

def run_demo_server():
    port = 8080
    handler = DemoHandler
    
    try:
        httpd = socketserver.TCPServer(("", port), handler)
        print(f"Demo server running at http://localhost:{port}")
        print("Open the Preview tab to interact with the demo interface")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Demo server stopped")
    except Exception as e:
        print(f"Error starting demo server: {str(e)}")

if __name__ == "__main__":
    run_demo_server()