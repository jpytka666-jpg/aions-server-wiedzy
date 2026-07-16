import json, re, time
from urllib import request
API = 'http://127.0.0.1:9000/api/chat'
PATH = r"C:\Users\User\OneDrive - Global Banking School\Desktop\MAPA_LASU_SOLO_CBMS\AIONS_CBMS_RELEASE\tools\gsm8k_test.jsonl"
N = 20

num_re = re.compile(r"(-?\d+[\d,]*)")

def final_number(ans: str):
    if not ans: return None
    # Primary: look for #### pattern (GSM8K standard)
    m = re.findall(r"####\s*(-?\d+[\d,]*)", ans)
    if m: return int(m[-1].replace(",",""))
    
    # Secondary: look for "Odpowiedź to: X" pattern
    m = re.findall(r"Odpowiedź to:\s*(-?\d+[\d,]*)", ans)
    if m: return int(m[-1].replace(",",""))
    
    # Tertiary: look for "Answer: X" pattern
    m = re.findall(r"Answer:\s*(-?\d+[\d,]*)", ans)
    if m: return int(m[-1].replace(",",""))
    
    # Fallback: last number in text
    m = num_re.findall(ans)
    return int(m[-1].replace(",","")) if m else None

def post_chat(q: str):
    payload = json.dumps({"model":"local","messages":[{"role":"user","content":q}]}).encode('utf-8')
    req = request.Request(API, data=payload, headers={"Content-Type":"application/json"})
    t0 = time.time()
    with request.urlopen(req, timeout=10) as resp:
        dt = (time.time()-t0)*1000.0
        txt = resp.read().decode('utf-8','ignore')
        return dt, txt

correct=0; total=0; lats=[]; refused=0
with open(PATH,'r',encoding='utf-8') as fh:
    for i,line in enumerate(fh):
        if i>=N: break
        obj = json.loads(line)
        q=obj['question']; gt = final_number(obj['answer'])
        dt, txt = post_chat(q)
        lats.append(dt)
        if 'NIE WIEM' in txt: refused+=1
        pred = final_number(txt)
        if pred is not None and gt is not None and pred==gt:
            correct+=1
        total+=1

print(json.dumps({
    'total': total,
    'correct': correct,
    'accuracy': round(correct/total,3),
    'refused': refused,
    'p50_ms': round(sorted(lats)[int(0.5*(len(lats)-1))],2),
    'p95_ms': round(sorted(lats)[int(0.95*(len(lats)-1))],2),
}, ensure_ascii=False))
