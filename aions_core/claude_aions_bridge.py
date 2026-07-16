
import time
from smart_cbms import smart_cbms_response

class ClaudeAionsBridge:
    def __init__(self):
        pass

    def get_hybrid_response(self, query):
        """
        Get hybrid response using AIONS speed + Claude/LLM depth
        """
        start = time.time()
        try:
            # smart_cbms_response tries CBMS first, then fallback to LLM
            response_text = smart_cbms_response(query)
        except Exception as e:
            response_text = f"Error in hybrid bridge: {e}"
        
        duration_ms = (time.time() - start) * 1000

        # metrics extraction
        chunks_used = 0
        if "[Source: CBMS" in response_text:
            try:
                # E.g. "... [Source: CBMS 5 chunks]"
                part = response_text.split("[Source: CBMS")[1].strip()
                # "5 chunks]" -> "5"
                num_str = part.split()[0]
                chunks_used = int(num_str)
            except:
                pass
        
        return {
            "response": response_text,
            "source": "hybrid",
            "aions_time_ms": round(duration_ms, 2),
            "chunks_used": chunks_used,
            "performance": "EXCELLENT" if duration_ms < 100 else "GOOD"
        }
    
    def get_stats(self):
        return {
            "status": "active",
            "mode": "hybrid_reconstructed", 
            "backend": "smart_cbms"
        }

if __name__ == "__main__":
    bridge = ClaudeAionsBridge()
    print("Testing Hybrid Bridge...")
    try:
        res = bridge.get_hybrid_response("Test query")
        print(res)
    except Exception as e:
        print(f"Bridge test failed: {e}")
