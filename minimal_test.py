import os
import requests

api_key = os.environ.get("ANTHROPIC_API_KEY")
print(f"API key available: {api_key is not None}")

if api_key:
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Say hello"}]
        }
        
        print("Sending request to Anthropic...")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=15
        )
        
        print(f"Response code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {str(e)}")
else:
    print("No API key found in environment variables")
