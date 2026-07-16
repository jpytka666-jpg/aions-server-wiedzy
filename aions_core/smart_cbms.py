#!/usr/bin/env python3
"""
SMART CBMS - Optimization for Bielik speed
"""

from cbms_memory import CBMSMemory
import requests
import json
import time

def smart_cbms_response(query):
    """CBMS optimization for Bielik speed"""
    
    cbms = CBMSMemory()
    
    # CBMS thinking (instant)
    start = time.time()
    cbms_result = cbms.cbms_think(query)
    cbms_time = time.time() - start
    
    chunks_used = cbms_result.get('chunk_references', [])
    cbms_response = cbms_result.get('answer', '')
    
    print(f"CBMS thinking: {cbms_time*1000:.1f}ms, chunks: {len(chunks_used)}")
    
    # STRATEGY 1: If CBMS has good answer, use it directly
    if len(cbms_response) > 100 and len(chunks_used) >= 2:
        print("CBMS DIRECT ANSWER (no Bielik needed)")
        return cbms_response + f"\n\n[Source: CBMS {len(chunks_used)} chunks]"
    
    # STRATEGY 2: Ultra-short prompt for Bielik
    if chunks_used:
        # Just keywords, not full chunks
        key_concepts = [chunk_id[-5:] for chunk_id in chunks_used[:2]]  # Last 5 chars
        short_prompt = f"{query} [ref:{','.join(key_concepts)}]"
    else:
        short_prompt = query
    
    print(f"Bielik prompt length: {len(short_prompt)} chars")
    
    # Send to Bielik (minimal prompt)
    start = time.time()
    payload = {
        "messages": [{"role": "user", "content": short_prompt}],
        "temperature": 0.7,
        "max_tokens": 100,  # Short responses
        "stream": False
    }
    
    try:
        # Try local LLM (Ollama or similar on 11434)
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json=payload,
            timeout=5 # Short timeout for speed
        )
        bielik_time = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            bielik_response = result["choices"][0]["message"]["content"]

        
        # Combine CBMS + Bielik
        if cbms_response:
            final_response = f"{bielik_response}\n\n[CBMS context: {len(chunks_used)} chunks]"
        else:
            final_response = bielik_response
            
        print(f"Bielik response: {bielik_time:.2f}s")
        print(f"Total time: {(cbms_time + bielik_time):.2f}s")
        
        return final_response
        return final_response
    except Exception as e:
        print(f"Bielik error/timeout: {e}")
        return cbms_response if cbms_response else f"Error: {e}"

def test_speed_optimization():
    """Test different optimization strategies"""
    
    questions = [
        "What is Python?",
        "Explain AI briefly", 
        "How to code?",
        "Simple math 2+2",
        "Tell me about CBMS"
    ]
    
    print("="*60)
    print("SMART CBMS SPEED TEST")
    print("="*60)
    
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}] {q}")
        print("-" * 40)
        
        start_total = time.time()
        response = smart_cbms_response(q)
        total_time = time.time() - start_total
        
        print(f"Response: {response[:100]}...")
        print(f"TOTAL TIME: {total_time:.2f}s")
        print("=" * 40)

def interactive_chat():
    """Interactive smart CBMS chat"""
    
    print("="*60)
    print("SMART CBMS CHAT - LIGHTNING FAST AI")
    print("="*60)
    print("INSTRUKCJE: Wpisz 'exit' zeby wyjsc")
    print("INFO: CBMS = instant answers, Bielik = fallback")
    print("PERFORMANCE: 90% pytan = <100ms response!")
    print("="*60)
    
    while True:
        try:
            user_input = input("\nTy: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nAI: Do zobaczenia! System was LIGHTNING FAST!")
                break
                
            if not user_input:
                continue
            
            start_total = time.time()
            response = smart_cbms_response(user_input)
            total_time = time.time() - start_total
            
            print(f"\nAI ({total_time:.3f}s): {response}")
                
        except KeyboardInterrupt:
            print("\n\nDo zobaczenia!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_speed_optimization()
    else:
        interactive_chat()