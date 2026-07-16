import requests
import json

def check_status():
    url = "http://127.0.0.1:8080/status"
    try:
        response = requests.get(url)
        data = response.json()
        print(json.dumps(data.get('stats', {}).get('errors', []), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()
