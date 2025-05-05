import requests
try:
    response = requests.get("https://httpbin.org/get", timeout=5)
    print(f"HTTP request successful: {response.status_code == 200}")
except Exception as e:
    print(f"HTTP request failed: {str(e)}")
