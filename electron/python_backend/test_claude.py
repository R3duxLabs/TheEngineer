import os
import requests

# Check API key
api_key = os.environ.get("ANTHROPIC_API_KEY")
print(f"API key found: {'Yes' if api_key else 'No'}")

if not api_key:
    print("ERROR: No API key found. Please add ANTHROPIC_API_KEY to Secrets.")
    exit(1)

# Test API connection
print("Sending test request to Claude API...")
try:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Hello, are you working?"}]
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=data,
        timeout=10
    )
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Claude API is working.")
        response_data = response.json()
        print(f"Claude says: {response_data[\"content\"][0][\"text\"][:50]}...")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {str(e)}")

print("Test complete.")
