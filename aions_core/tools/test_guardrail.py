import requests
import json
import sys

def test_guardrail():
    url = "http://127.0.0.1:8080/query"
    
    print("\n--- TEST 1: Nonsense Query (Should REFUSE) ---")
    payload_bad = {"query": "xyz123 blablabla unicorn"}
    try:
        r = requests.post(url, json=payload_bad)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- TEST 2: Valid Query (Should ACCEPT) ---")
    payload_good = {"query": "Opisz guardrail refusal policy CBMS"}
    try:
        r = requests.post(url, json=payload_good)
        print(f"Status: {r.status_code}")
        # Truncate answer for readability
        res = r.json()
        if 'answer' in res:
            res['answer'] = res['answer'][:200] + "..."
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_guardrail()
