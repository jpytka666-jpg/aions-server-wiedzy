#!/usr/bin/env python3
"""
Web RAG Integration for CBMS System
Integrates web crawling with CBMS memory system
"""

import json
import time
import hashlib
import urllib.parse as up
import urllib.request as ur
import ssl
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from html.parser import HTMLParser

try:
    from korean_keys import build_keys
    KR_AVAILABLE = True
except ImportError:
    KR_AVAILABLE = False
    print("Warning: korean_keys not available - using fallback")


class WebRAGTextExtractor(HTMLParser):
    """Extracts clean text from HTML"""
    
    def __init__(self):
        super().__init__()
        self.in_ignored = False
        self.buffer = []
    
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "nav", "footer", "header"):
            self.in_ignored = True
    
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "nav", "footer", "header"):
            self.in_ignored = False
        if tag in ("p", "br", "div", "li", "section", "article", "h1", "h2", "h3"):
            self.buffer.append("\n")
    
    def handle_data(self, data):
        if not self.in_ignored:
            self.buffer.append(data)
    
    def get_text(self) -> str:
        raw = "".join(self.buffer)
        raw = re.sub(r"\s+", " ", raw)
        return raw.strip()


class WebRAGCBMS:
    """Web RAG system integrated with CBMS"""
    
    def __init__(self, cbms_memory, max_pages: int = 5, max_mb: int = 10):
        self.cbms = cbms_memory
        self.max_pages = max_pages
        self.max_mb = max_mb
        
        # Trusted domains for crawling
        self.trusted_domains = {
            'wikipedia.org', 'pl.wikipedia.org', 'en.wikipedia.org',
            'stackoverflow.com', 'stackexchange.com',
            'github.com', 'docs.python.org', 'developer.mozilla.org',
            'w3schools.com', 'tutorialspoint.com'
        }
        
        # SSL context
        self.ssl_context = ssl.create_default_context()
        
        # Cache for recent searches
        self.search_cache = {}
        self.cache_max_age = 3600  # 1 hour
    
    def search_and_inject(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Main Web RAG function: PANIC → Web Search → Inject → Return chunks
        
        Args:
            query: User query that triggered PANIC
            max_results: Maximum number of facts to extract
            
        Returns:
            Dict with injected chunks and metadata
        """
        print(f"🔍 Web RAG triggered for query: {query}")
        
        # 1. Generate search URLs
        search_urls = self._generate_search_urls(query)
        
        # 2. Crawl and extract facts
        facts = self._crawl_and_extract(search_urls, query)
        
        # 3. Inject facts as temporary chunks
        injected_chunks = self._inject_facts_as_chunks(facts[:max_results])
        
        # 4. Return metadata for CRLA
        return {
            'injected_chunks': injected_chunks,
            'facts_count': len(facts),
            'sources': [f['url'] for f in facts[:max_results]],
            'query': query,
            'timestamp': time.time()
        }
    
    def _generate_search_urls(self, query: str) -> List[str]:
        """Generate search URLs for the query"""
        # URL encode query
        encoded_query = up.quote_plus(query)
        
        urls = []
        
        # Wikipedia search
        urls.append(f"https://en.wikipedia.org/wiki/{encoded_query}")
        urls.append(f"https://pl.wikipedia.org/wiki/{encoded_query}")
        
        # Stack Overflow search
        urls.append(f"https://stackoverflow.com/search?q={encoded_query}")
        
        # GitHub search
        urls.append(f"https://github.com/search?q={encoded_query}&type=repositories")
        
        # Documentation sites
        if 'python' in query.lower():
            urls.append(f"https://docs.python.org/3/search.html?q={encoded_query}")
        
        return urls[:self.max_pages]
    
    def _crawl_and_extract(self, urls: List[str], query: str) -> List[Dict[str, Any]]:
        """Crawl URLs and extract relevant facts"""
        facts = []
        seen_text = set()
        
        for url in urls:
            try:
                # Check if domain is trusted
                if not self._is_trusted_domain(url):
                    continue
                
                # Fetch page
                page_content = self._fetch_page(url)
                if not page_content:
                    continue
                
                # Extract text
                parser = WebRAGTextExtractor()
                parser.feed(page_content)
                text = parser.get_text()
                
                # Split into sentences and filter
                sentences = self._split_into_sentences(text)
                
                # Score and filter sentences
                for sentence in sentences:
                    if self._is_relevant_sentence(sentence, query):
                        sentence_hash = hashlib.md5(sentence.encode()).hexdigest()
                        if sentence_hash not in seen_text:
                            facts.append({
                                'text': sentence,
                                'url': url,
                                'score': self._score_relevance(sentence, query),
                                'domain': up.urlparse(url).netloc
                            })
                            seen_text.add(sentence_hash)
                
                time.sleep(0.5)  # Be respectful
                
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                continue
        
        # Sort by relevance score
        facts.sort(key=lambda x: x['score'], reverse=True)
        return facts
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content safely"""
        try:
            req = ur.Request(
                url, 
                headers={
                    'User-Agent': 'AIONS-CBMS-WebRAG/1.0 (Educational Research)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
            )
            
            with ur.urlopen(req, context=self.ssl_context, timeout=10) as resp:
                if resp.getcode() == 200:
                    content_type = resp.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        return resp.read().decode('utf-8', errors='ignore')
            
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        
        return None
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Filter sentences by length and content
        filtered = []
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 <= len(sentence) <= 300:  # Reasonable length
                if not re.match(r'^[0-9\s\-_]+$', sentence):  # Not just numbers/symbols
                    filtered.append(sentence)
        
        return filtered
    
    def _is_relevant_sentence(self, sentence: str, query: str) -> bool:
        """Check if sentence is relevant to query"""
        sentence_lower = sentence.lower()
        query_lower = query.lower()
        
        # Extract keywords from query
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        # Count keyword matches
        matches = sum(1 for word in query_words if word in sentence_lower)
        
        # Must have at least 1 keyword match
        return matches > 0
    
    def _score_relevance(self, sentence: str, query: str) -> float:
        """Score sentence relevance to query"""
        sentence_lower = sentence.lower()
        query_lower = query.lower()
        
        # Extract keywords
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        sentence_words = set(re.findall(r'\b\w+\b', sentence_lower))
        
        # Calculate overlap
        overlap = len(query_words.intersection(sentence_words))
        
        # Normalize by query length
        if len(query_words) == 0:
            return 0.0
        
        base_score = overlap / len(query_words)
        
        # Bonus for exact phrase match
        if query_lower in sentence_lower:
            base_score += 0.3
        
        # Bonus for domain-specific terms
        domain_terms = ['definition', 'explanation', 'example', 'tutorial', 'guide']
        if any(term in sentence_lower for term in domain_terms):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _is_trusted_domain(self, url: str) -> bool:
        """Check if URL domain is trusted"""
        try:
            domain = up.urlparse(url).netloc.lower()
            return any(domain.endswith(trusted) for trusted in self.trusted_domains)
        except:
            return False
    
    def _inject_facts_as_chunks(self, facts: List[Dict[str, Any]]) -> List[str]:
        """Inject facts as temporary CBMS chunks"""
        injected_chunks = []
        
        for fact in facts:
            try:
                # Create chunk content
                content = f"{fact['text']}\n\n[Źródło: {fact['url']}]"
                
                # Generate chunk ID
                chunk_id = f"WEB{hashlib.sha256(content.encode()).hexdigest()[:10].upper()}"
                
                # Create chunk metadata
                meta = {
                    'source': 'web_rag',
                    'url': fact['url'],
                    'domain': fact['domain'],
                    'relevance_score': fact['score'],
                    'temporary': True,
                    'created_at': time.time()
                }
                
                # Inject into CBMS
                actual_chunk_id = self.cbms.create_knowledge_chunk(
                    content=content,
                    concept='web_rag_fact',
                    references=[fact['url']],
                    meta=meta
                )
                
                injected_chunks.append(actual_chunk_id)
                print(f"✅ Injected Web RAG chunk: {actual_chunk_id}")
                
            except Exception as e:
                print(f"❌ Failed to inject fact: {e}")
                continue
        
        return injected_chunks
    
    def cleanup_temporary_chunks(self, max_age_hours: int = 24):
        """Clean up old temporary Web RAG chunks"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # This would need to be implemented in CBMS memory system
        # For now, just log the intention
        print(f"🧹 Would clean up Web RAG chunks older than {max_age_hours} hours")


def create_web_rag_instance(cbms_memory) -> WebRAGCBMS:
    """Factory function to create Web RAG instance"""
    return WebRAGCBMS(cbms_memory, max_pages=5, max_mb=10)


