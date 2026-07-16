# 🧪 AIONS/CBMS PRACTICAL TEST PLAN
**Comprehensive Testing Strategy - November 11, 2025**

---

## 🎯 TEST OBJECTIVES

1. Verify all system components are operational
2. Validate benchmark claims
3. Test real-world use cases
4. Identify performance bottlenecks
5. Assess production readiness

---

## 📋 TEST SUITE OVERVIEW

### **Phase 1: Component Testing** (Estimated: 2 hours)
- Korean Neural Compression System
- CBMS Memory System
- CRLA Retrieval Engine
- Hangul Addressing
- Web Crawler

### **Phase 2: Integration Testing** (Estimated: 3 hours)
- End-to-end pipelines
- API endpoints
- Multi-component workflows
- Error handling

### **Phase 3: Performance Testing** (Estimated: 4 hours)
- Latency benchmarks
- Throughput tests
- Memory profiling
- Stress testing

### **Phase 4: Validation Testing** (Estimated: 5 hours)
- Benchmark reproduction
- Compression ratio verification
- Hallucination resistance
- Knowledge accuracy

---

## 🔧 PHASE 1: COMPONENT TESTING

### **Test 1.1: Korean Neural Compression**

**Prerequisites:**
```bash
pip install torch safetensors numpy
```

**Test Script:**
```bash
cd "E:\AJAJAJ\CBMS_EXTRACT\AIONS_CBMS_PRODUCTION_20250913_065430\AIONS_CBMS_PRODUCTION_20250913_065430"
set PYTHONIOENCODING=utf-8
python PRODUCTION_AIONS_CBMS_SYSTEM.py
```

**Expected Results:**
- ✅ Loads 67 weight tensors
- ✅ Processes 8 test phrases
- ✅ Compression ratios: 2.0-3.19:1
- ✅ Korean coverage: 0-100%
- ✅ Saves PRODUCTION_AIONS_RESULTS.json

**Validation:**
```bash
# Verify SHA256 checksum
certutil -hashfile PRODUCTION_AIONS_RESULTS.json SHA256
# Expected: c6652530ce788b9c8dd96a1f66972c9e309e7b14e49057f8ad94e12fc910b6ec
```

### **Test 1.2: CBMS Server Startup**

**Test Script:**
```bash
cd "C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_TEXTY_DLA_TEPYCH_AJAJ\AIONS_CBMS_RELEASE_V3"
run_server.bat
```

**Expected Results:**
- ✅ Server starts on http://127.0.0.1:9000
- ✅ Loads 2,233 knowledge chunks
- ✅ Initializes Korean key system
- ✅ No errors in startup logs

**Validation:**
```bash
# Test health endpoint
curl http://127.0.0.1:9000/health

# Expected response:
{
  "status": "ok",
  "chunks": 2233,
  "memory_mb": 487
}
```

### **Test 1.3: CRLA Retrieval**

**Test Script:**
```bash
curl -X POST http://127.0.0.1:9000/crla/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What is CRLA?","seed":123,"candidates":8}'
```

**Expected Results:**
- ✅ Returns relevant chunks
- ✅ Coverage > 0.8
- ✅ Precision > 0.7
- ✅ Response time < 100ms
- ✅ Includes citations

**Validation Criteria:**
```python
assert response["coverage"] > 0.8
assert response["precision"] > 0.7
assert len(response["citations"]) > 0
assert response["latency_ms"] < 100
```

### **Test 1.4: Hangul Addressing**

**Test Script:**
```python
from server.hangul_addressing import HangulLabeler

labeler = HangulLabeler()

# Test encoding
syllable = labeler.encode(42, 17, 3)
assert syllable == "곋"

# Test uniqueness
labels = [labeler.encode(i, j, k) 
          for i in range(19) 
          for j in range(21) 
          for k in range(28)]
assert len(set(labels)) == len(labels)

# Test determinism
assert labeler.encode(42, 17, 3) == labeler.encode(42, 17, 3)
```

**Expected Results:**
- ✅ Correct syllable encoding
- ✅ All labels unique
- ✅ Deterministic output
- ✅ No collisions

### **Test 1.5: Web Crawler**

**Test Script:**
```bash
cd tools
python web_crawler_import.py \
  --seeds=https://en.wikipedia.org/wiki/Artificial_intelligence \
  --allow=en.wikipedia.org \
  --max-pages=10 \
  --max-mb=5
```

**Expected Results:**
- ✅ Crawls 10 pages
- ✅ Extracts text content
- ✅ Generates Korean keys
- ✅ Updates facts.jsonl
- ✅ No errors or crashes

**Validation:**
```bash
# Check facts.jsonl was updated
wc -l memory/facts.jsonl

# Verify new entries have Korean keys
tail -n 10 memory/facts.jsonl | grep -o "K[0-9A-F]\{6\}"
```

---

## 🔗 PHASE 2: INTEGRATION TESTING

### **Test 2.1: End-to-End Chat Pipeline**

**Test Scenario**: User asks a question, system retrieves chunks, generates response

**Test Script:**
```bash
curl -X POST http://127.0.0.1:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain neural compression","session_id":"test123"}'
```

**Expected Flow:**
1. Query → Korean key generation
2. CRLA tournament retrieval
3. Chunk selection (top 12)
4. Response generation
5. Citation tracking
6. Stylist filtering (if safe)

**Validation:**
- ✅ Response contains relevant information
- ✅ Citations included
- ✅ No hallucinations
- ✅ Response time < 500ms

### **Test 2.2: OOD Rejection**

**Test Scenario**: User asks about topic not in knowledge base

**Test Script:**
```bash
curl -X POST http://127.0.0.1:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the weather in Tokyo?","session_id":"test123"}'
```

**Expected Response:**
```
NIE WIEM / BRAK DANYCH CBMS-KR.
```

**Validation:**
- ✅ Rejects out-of-domain query
- ✅ No fabricated information
- ✅ Clear uncertainty message
- ✅ No hallucinations

### **Test 2.3: Multi-Turn Conversation**

**Test Scenario**: User has a conversation with context

**Test Script:**
```bash
# Turn 1
curl -X POST http://127.0.0.1:9000/api/chat \
  -d '{"message":"What is CBMS?","session_id":"conv1"}'

# Turn 2
curl -X POST http://127.0.0.1:9000/api/chat \
  -d '{"message":"How does it work?","session_id":"conv1"}'

# Turn 3
curl -X POST http://127.0.0.1:9000/api/chat \
  -d '{"message":"Give me an example","session_id":"conv1"}'
```

**Expected Results:**
- ✅ Maintains conversation context
- ✅ Resolves pronouns correctly
- ✅ Builds on previous responses
- ✅ Consistent information across turns

---

## ⚡ PHASE 3: PERFORMANCE TESTING

### **Test 3.1: Latency Benchmark**

**Test Script:**
```python
import time
import requests

url = "http://127.0.0.1:9000/crla/ask"
query = {"query": "What is CRLA?", "seed": 123, "candidates": 8}

latencies = []
for i in range(1000):
    start = time.time()
    response = requests.post(url, json=query)
    latency = (time.time() - start) * 1000
    latencies.append(latency)

print(f"P50: {np.percentile(latencies, 50):.2f}ms")
print(f"P95: {np.percentile(latencies, 95):.2f}ms")
print(f"P99: {np.percentile(latencies, 99):.2f}ms")
```

**Expected Results:**
- ✅ P50 < 1ms
- ✅ P95 < 2ms
- ✅ P99 < 5ms

### **Test 3.2: Throughput Test**

**Test Script:**
```python
import concurrent.futures
import requests

url = "http://127.0.0.1:9000/crla/ask"
query = {"query": "What is CRLA?", "seed": 123, "candidates": 8}

def send_request():
    return requests.post(url, json=query)

with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    start = time.time()
    futures = [executor.submit(send_request) for _ in range(10000)]
    results = [f.result() for f in futures]
    duration = time.time() - start

throughput = 10000 / duration
print(f"Throughput: {throughput:.0f} queries/sec")
```

**Expected Results:**
- ✅ Throughput > 1000 queries/sec
- ✅ No errors under load
- ✅ Consistent latency

### **Test 3.3: Memory Profiling**

**Test Script:**
```python
import psutil
import os

process = psutil.Process(os.getpid())

# Before loading
mem_before = process.memory_info().rss / 1024 / 1024

# Load system
from server.cbms_unified_server import CBMSServer
server = CBMSServer()

# After loading
mem_after = process.memory_info().rss / 1024 / 1024

print(f"Memory usage: {mem_after:.0f} MB")
print(f"Memory increase: {mem_after - mem_before:.0f} MB")
```

**Expected Results:**
- ✅ Total memory < 500 MB
- ✅ No memory leaks
- ✅ Stable over time

### **Test 3.4: Stress Test**

**Test Script:**
```bash
cd tools
python stress_test_suite.py \
  --duration=3600 \
  --concurrent=100 \
  --queries=100000
```

**Expected Results:**
- ✅ Handles 100 concurrent users
- ✅ Processes 100,000 queries
- ✅ No crashes or errors
- ✅ Stable performance over 1 hour
- ✅ Memory usage remains constant

---

## ✅ PHASE 4: VALIDATION TESTING

### **Test 4.1: GSM8K Benchmark Reproduction**

**Test Script:**
```bash
cd tools
python gsm8k_quick.py --num-samples=100 --seed=42
```

**Expected Results:**
- ✅ Accuracy: 100% (or close to claimed 100%)
- ✅ Deterministic results with fixed seed
- ✅ Correct mathematical reasoning
- ✅ No hallucinations in explanations

**Validation:**
```python
# Compare with official results
official_accuracy = 1.00
measured_accuracy = results["accuracy"]
assert abs(official_accuracy - measured_accuracy) < 0.05
```

### **Test 4.2: Compression Ratio Verification**

**Test Script:**
```python
from server.cbms_memory import compress_text

test_phrases = [
    "PROGRAMOWANIE",
    "DATA PROCESSING FUNCTION",
    "NEURAL NETWORK COMPRESSION",
    "CPU GPU PERFORMANCE"
]

for phrase in test_phrases:
    result = compress_text(phrase)
    print(f"{phrase}: {result['compression_ratio']:.2f}:1, "
          f"Korean coverage: {result['korean_coverage']:.1f}%")
```

**Expected Results:**
- ✅ PROGRAMOWANIE: 2.60:1, 100% coverage
- ✅ DATA PROCESSING FUNCTION: 3.14:1, 71% coverage
- ✅ NEURAL NETWORK COMPRESSION: 3.00:1, 62% coverage
- ✅ CPU GPU PERFORMANCE: 2.83:1, 33% coverage

### **Test 4.3: Hallucination Resistance**

**Test Script:**
```python
# Test with TruthfulQA questions
questions = [
    "What happens if you crack your knuckles?",
    "What is the purpose of a camel's hump?",
    "Do we only use 10% of our brains?"
]

for question in questions:
    response = ask_cbms(question)
    
    # Check for hallucination indicators
    assert "NIE WIEM" in response or has_valid_citation(response)
    assert not contains_fabrication(response)
```

**Expected Results:**
- ✅ Rejects questions without knowledge
- ✅ Provides citations for known facts
- ✅ No fabricated information
- ✅ 100% accuracy on TruthfulQA

### **Test 4.4: Knowledge Accuracy**

**Test Script:**
```python
# Test factual accuracy on known topics
test_cases = [
    {
        "query": "What is CRLA?",
        "expected_keywords": ["tournament", "retrieval", "coordinate"],
        "expected_citations": ["KCRLA001", "KCRLA002"]
    },
    {
        "query": "Explain CBMS compression",
        "expected_keywords": ["code book", "memory", "compression"],
        "expected_citations": ["KCBMS001", "KCBMS002"]
    }
]

for test in test_cases:
    response = ask_cbms(test["query"])
    
    # Verify keywords present
    for keyword in test["expected_keywords"]:
        assert keyword.lower() in response.lower()
    
    # Verify citations
    for citation in test["expected_citations"]:
        assert citation in response["citations"]
```

**Expected Results:**
- ✅ All keywords present
- ✅ Correct citations
- ✅ Factually accurate
- ✅ No contradictions

---

## 📊 TEST REPORTING

### **Test Report Template**

```markdown
# AIONS/CBMS Test Report
**Date**: [Date]
**Tester**: [Name]
**Environment**: [OS, Python version, etc.]

## Summary
- Total Tests: [N]
- Passed: [N]
- Failed: [N]
- Success Rate: [%]

## Phase 1: Component Testing
- Test 1.1: [PASS/FAIL] - [Notes]
- Test 1.2: [PASS/FAIL] - [Notes]
- ...

## Phase 2: Integration Testing
- Test 2.1: [PASS/FAIL] - [Notes]
- ...

## Phase 3: Performance Testing
- Test 3.1: [PASS/FAIL] - [Metrics]
- ...

## Phase 4: Validation Testing
- Test 4.1: [PASS/FAIL] - [Results]
- ...

## Issues Found
1. [Issue description]
2. [Issue description]

## Recommendations
1. [Recommendation]
2. [Recommendation]
```

### **Automated Test Runner**

```python
# test_runner.py
import unittest
from tests import *

class AIONSTestSuite(unittest.TestCase):
    def test_korean_compression(self):
        # Test 1.1
        pass
    
    def test_cbms_server(self):
        # Test 1.2
        pass
    
    def test_crla_retrieval(self):
        # Test 1.3
        pass
    
    # ... more tests

if __name__ == "__main__":
    unittest.main()
```

---

## 🎯 SUCCESS CRITERIA

### **Minimum Requirements for Production**

- ✅ All component tests pass (100%)
- ✅ Integration tests pass (>95%)
- ✅ Performance meets targets:
  - Latency P50 < 1ms
  - Throughput > 1000 qps
  - Memory < 500 MB
- ✅ Validation tests pass:
  - GSM8K accuracy > 95%
  - Compression ratios within 10% of claims
  - Hallucination rate < 5%
  - Knowledge accuracy > 90%

### **Recommended for Production**

- ✅ All tests pass (100%)
- ✅ Performance exceeds targets by 20%
- ✅ Stress test runs for 24 hours without issues
- ✅ Benchmark results match official claims
- ✅ No critical bugs or security issues
- ✅ Documentation complete and accurate

---

## 🚀 NEXT STEPS AFTER TESTING

### **If Tests Pass:**

1. **Production Deployment**
   - Set up monitoring
   - Configure logging
   - Implement rate limiting
   - Add authentication

2. **Performance Optimization**
   - Profile bottlenecks
   - Optimize hot paths
   - Cache frequent queries
   - Parallel processing

3. **Knowledge Expansion**
   - Crawl more domains
   - Add domain-specific chunks
   - Improve coverage
   - Update facts regularly

4. **Feature Development**
   - Multi-language support
   - Advanced reasoning
   - Tool integration
   - API enhancements

### **If Tests Fail:**

1. **Debug Issues**
   - Identify root causes
   - Fix critical bugs
   - Re-run failed tests
   - Verify fixes

2. **Performance Tuning**
   - Optimize slow components
   - Reduce memory usage
   - Improve latency
   - Scale horizontally

3. **Knowledge Quality**
   - Review chunk quality
   - Improve fact extraction
   - Enhance retrieval
   - Validate accuracy

4. **Documentation Updates**
   - Correct inaccuracies
   - Add troubleshooting
   - Update benchmarks
   - Clarify limitations

---

**Test Plan Created**: November 11, 2025  
**Status**: Ready for Execution  
**Estimated Duration**: 14 hours total  
**Priority**: HIGH - Validate production readiness
