import os
import requests

api_key = os.environ.get("ANTHROPIC_API_KEY")
print(f"API key found: {'Yes' if api_key else 'No'}")

if api_key:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Try Claude 3.5 Sonnet instead
    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    print("Sending request to Anthropic...")
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=15
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {str(e)}")
else:
    print("No API key found")
