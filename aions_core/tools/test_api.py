import requests
import json
import sys

def test_api():
    url = "http://127.0.0.1:8080/query"
    payload = {"query": "Hello, who are you?"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
        try:
            print(response.text)
        except:
            pass

if __name__ == "__main__":
    test_api()
