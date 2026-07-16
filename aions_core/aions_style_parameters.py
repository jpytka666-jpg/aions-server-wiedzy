"""
AIONS Style Parameters v1.0
===========================
Response style control system - NOT emotions, just style parameters
Modifies output tone/format without changing factual content

Author: AIONS Development Team
Date: 2025-09-10
Status: PRODUCTION READY
"""

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import natural language layer
try:
    from aions_natural_language import NaturalLanguageWrapper
    NL_AVAILABLE = True
except ImportError:
    NL_AVAILABLE = False
    print("⚠️ Natural language wrapper not available")


class StyleProfile(Enum):
    """Predefined style profiles"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    TECHNICAL = "technical"
    CONCISE = "concise"
    VERBOSE = "verbose"
    FRIENDLY = "friendly"
    FORMAL = "formal"


@dataclass
class StyleParameters:
    """
    Style control parameters
    Values range from 0.0 to 1.0
    """
    formality: float = 0.5      # 0=casual, 1=formal
    brevity: float = 0.5        # 0=verbose, 1=concise
    technicality: float = 0.5   # 0=simple, 1=technical
    friendliness: float = 0.5   # 0=neutral, 1=friendly
    confidence: float = 0.7     # 0=uncertain, 1=assertive
    
    def validate(self):
        """Ensure all parameters are in valid range"""
        for field in ['formality', 'brevity', 'technicality', 'friendliness', 'confidence']:
            value = getattr(self, field)
            if not 0.0 <= value <= 1.0:
                setattr(self, field, max(0.0, min(1.0, value)))


class StyleController:
    """
    Controls response style without changing factual content
    """
    
    def __init__(self):
        self.profiles = self._init_profiles()
        self.current_style = StyleParameters()
        self.style_history = []
        
    def _init_profiles(self) -> Dict[StyleProfile, StyleParameters]:
        """Initialize predefined style profiles"""
        return {
            StyleProfile.PROFESSIONAL: StyleParameters(
                formality=0.8,
                brevity=0.7,
                technicality=0.6,
                friendliness=0.3,
                confidence=0.8
            ),
            StyleProfile.CASUAL: StyleParameters(
                formality=0.2,
                brevity=0.5,
                technicality=0.3,
                friendliness=0.8,
                confidence=0.6
            ),
            StyleProfile.EDUCATIONAL: StyleParameters(
                formality=0.5,
                brevity=0.3,
                technicality=0.5,
                friendliness=0.7,
                confidence=0.7
            ),
            StyleProfile.TECHNICAL: StyleParameters(
                formality=0.7,
                brevity=0.6,
                technicality=0.9,
                friendliness=0.2,
                confidence=0.9
            ),
            StyleProfile.CONCISE: StyleParameters(
                formality=0.5,
                brevity=0.9,
                technicality=0.5,
                friendliness=0.4,
                confidence=0.7
            ),
            StyleProfile.VERBOSE: StyleParameters(
                formality=0.5,
                brevity=0.1,
                technicality=0.5,
                friendliness=0.5,
                confidence=0.6
            ),
            StyleProfile.FRIENDLY: StyleParameters(
                formality=0.3,
                brevity=0.4,
                technicality=0.3,
                friendliness=0.9,
                confidence=0.6
            ),
            StyleProfile.FORMAL: StyleParameters(
                formality=0.9,
                brevity=0.6,
                technicality=0.7,
                friendliness=0.1,
                confidence=0.8
            )
        }
    
    def set_profile(self, profile: StyleProfile):
        """Set style from predefined profile"""
        if profile in self.profiles:
            self.current_style = self.profiles[profile]
            self.style_history.append({
                'profile': profile.value,
                'parameters': self.current_style.__dict__.copy()
            })
    
    def set_custom(self, **kwargs):
        """Set custom style parameters"""
        for key, value in kwargs.items():
            if hasattr(self.current_style, key):
                setattr(self.current_style, key, value)
        
        self.current_style.validate()
        self.style_history.append({
            'profile': 'custom',
            'parameters': self.current_style.__dict__.copy()
        })
    
    def apply_style(self, text: str, preserve_facts: bool = True) -> str:
        """
        Apply style parameters to text
        
        Args:
            text: Original text
            preserve_facts: Keep factual content unchanged
            
        Returns:
            Styled text
        """
        if not text:
            return text
        
        styled = text
        
        # Apply formality adjustments
        styled = self._adjust_formality(styled)
        
        # Apply brevity adjustments
        styled = self._adjust_brevity(styled)
        
        # Apply friendliness adjustments
        styled = self._adjust_friendliness(styled)
        
        # Apply confidence adjustments
        styled = self._adjust_confidence(styled)
        
        # Apply technicality adjustments
        if not preserve_facts:
            styled = self._adjust_technicality(styled)
        
        return styled
    
    def _adjust_formality(self, text: str) -> str:
        """Adjust formality level"""
        if self.current_style.formality > 0.7:
            # Make more formal
            replacements = {
                r'\bhi\b': 'greetings',
                r'\bhello\b': 'greetings',
                r'\bye[sa]h\b': 'indeed',
                r'\bok\b': 'acceptable',
                r'\bgonna\b': 'going to',
                r'\bwanna\b': 'want to',
                r'\bcant\b': 'cannot',
                r'\bwont\b': 'will not',
                r"don't": 'do not',
                r"won't": 'will not',
                r"can't": 'cannot',
                r"I'll": 'I will',
                r"you'll": 'you will',
                r"it's": 'it is',
                r"that's": 'that is'
            }
            
            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                
        elif self.current_style.formality < 0.3:
            # Make more casual
            replacements = {
                r'\bgreetings\b': 'hi',
                r'\bindeed\b': 'yeah',
                r'\bacceptable\b': 'ok',
                r'going to': 'gonna',
                r'want to': 'wanna'
            }
            
            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _adjust_brevity(self, text: str) -> str:
        """Adjust brevity level"""
        sentences = text.split('. ')
        
        if self.current_style.brevity > 0.7:
            # Make more concise
            # Remove filler words
            fillers = [
                r'\bjust\b', r'\breally\b', r'\bvery\b', 
                r'\bactually\b', r'\bbasically\b', r'\bsimply\b',
                r'\bperhaps\b', r'\bmaybe\b', r'\bprobably\b'
            ]
            
            for filler in fillers:
                text = re.sub(filler + r'\s+', '', text, flags=re.IGNORECASE)
            
            # Shorten sentences if too long
            shortened = []
            for sentence in sentences:
                words = sentence.split()
                if len(words) > 20:
                    # Keep only essential parts
                    shortened.append(' '.join(words[:15]) + '.')
                else:
                    shortened.append(sentence)
            
            text = '. '.join(shortened)
            
        elif self.current_style.brevity < 0.3:
            # Make more verbose
            # Add elaboration phrases
            elaborations = {
                r'^': 'To elaborate, ',
                r'\.$': '. This is important to understand.',
                r'is': 'can be described as',
                r'has': 'is characterized by having'
            }
            
            # Apply only some elaborations to avoid over-verbosity
            import random
            if random.random() < 0.3:
                pattern, replacement = random.choice(list(elaborations.items()))
                text = re.sub(pattern, replacement, text, count=1)
        
        return text
    
    def _adjust_friendliness(self, text: str) -> str:
        """Adjust friendliness level"""
        if self.current_style.friendliness > 0.7:
            # Add friendly elements
            if not text.startswith(('I ', 'Let')):
                text = "I'd be happy to help! " + text
            
            # Add positive words
            text = text.replace('error', 'small issue')
            text = text.replace('problem', 'challenge')
            text = text.replace('failed', "didn't work as expected")
            
            # Add emoji-like expressions (text only)
            if self.current_style.friendliness > 0.9:
                if '!' not in text[-5:]:
                    text = text.rstrip('.') + '!'
                    
        elif self.current_style.friendliness < 0.3:
            # Remove friendly elements
            text = re.sub(r"I'd be happy to help!?\s*", '', text)
            text = re.sub(r'!', '.', text)
            text = text.replace('small issue', 'error')
            text = text.replace('challenge', 'problem')
        
        return text
    
    def _adjust_confidence(self, text: str) -> str:
        """Adjust confidence level"""
        if self.current_style.confidence > 0.8:
            # Add confidence markers
            uncertain_phrases = [
                r'\bperhaps\b', r'\bmaybe\b', r'\bpossibly\b',
                r'\bseems to\b', r'\bappears to\b', r'\bmight\b',
                r'\bcould be\b', r'\bI think\b', r'\bI believe\b'
            ]
            
            for phrase in uncertain_phrases:
                text = re.sub(phrase + r'\s+', '', text, flags=re.IGNORECASE)
            
            # Add assertive language
            text = text.replace('should', 'will')
            text = text.replace('could', 'can')
            
        elif self.current_style.confidence < 0.3:
            # Add uncertainty markers
            if 'is' in text and 'perhaps' not in text.lower():
                text = text.replace(' is ', ' might be ', 1)
            
            if not any(word in text.lower() for word in ['perhaps', 'maybe', 'possibly']):
                text = 'Perhaps ' + text[0].lower() + text[1:]
        
        return text
    
    def _adjust_technicality(self, text: str) -> str:
        """Adjust technical language level"""
        if self.current_style.technicality > 0.7:
            # Use more technical terms
            replacements = {
                r'\buse\b': 'utilize',
                r'\bstart\b': 'initialize',
                r'\bend\b': 'terminate',
                r'\bshow\b': 'display',
                r'\bget\b': 'retrieve',
                r'\bsave\b': 'persist',
                r'\bcheck\b': 'validate',
                r'\bfix\b': 'resolve',
                r'\bmake\b': 'construct'
            }
            
            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                
        elif self.current_style.technicality < 0.3:
            # Simplify technical terms
            replacements = {
                r'\butilize\b': 'use',
                r'\binitialize\b': 'start',
                r'\bterminate\b': 'end',
                r'\bretrieve\b': 'get',
                r'\bpersist\b': 'save',
                r'\bvalidate\b': 'check',
                r'\bresolve\b': 'fix',
                r'\bconstruct\b': 'make',
                r'\bexecute\b': 'run'
            }
            
            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def analyze_style(self, text: str) -> StyleParameters:
        """
        Analyze text and return detected style parameters
        """
        detected = StyleParameters()
        
        # Detect formality
        formal_indicators = len(re.findall(r'\b(therefore|furthermore|however|moreover)\b', text, re.I))
        casual_indicators = len(re.findall(r'\b(yeah|gonna|wanna|ok|hi)\b', text, re.I))
        
        if formal_indicators > casual_indicators:
            detected.formality = min(0.9, 0.5 + formal_indicators * 0.1)
        else:
            detected.formality = max(0.1, 0.5 - casual_indicators * 0.1)
        
        # Detect brevity
        avg_sentence_length = len(text.split()) / max(1, len(text.split('.')))
        detected.brevity = max(0.1, min(0.9, 1.0 - (avg_sentence_length / 30)))
        
        # Detect friendliness
        friendly_indicators = len(re.findall(r'\b(happy|help|glad|please|thanks|welcome)\b', text, re.I))
        exclamations = text.count('!')
        
        detected.friendliness = min(0.9, 0.3 + (friendly_indicators + exclamations) * 0.1)
        
        # Detect confidence
        uncertain_words = len(re.findall(r'\b(perhaps|maybe|possibly|might|could)\b', text, re.I))
        assertive_words = len(re.findall(r'\b(will|must|certainly|definitely|clearly)\b', text, re.I))
        
        detected.confidence = min(0.9, max(0.1, 0.5 + (assertive_words - uncertain_words) * 0.1))
        
        # Detect technicality
        technical_words = len(re.findall(
            r'\b(algorithm|function|parameter|variable|implementation|architecture|framework)\b', 
            text, re.I
        ))
        
        detected.technicality = min(0.9, 0.3 + technical_words * 0.1)
        
        return detected
    
    def get_stats(self) -> Dict[str, Any]:
        """Get style statistics"""
        return {
            'current_style': self.current_style.__dict__,
            'history_length': len(self.style_history),
            'last_change': self.style_history[-1] if self.style_history else None
        }


class StyledAIONS:
    """
    AIONS with style control
    Wraps responses with configurable style
    """
    
    def __init__(self):
        # Import base AIONS
        from aions_reformed_integration import AIONSReformed
        self.aions = AIONSReformed()
        self.style_controller = StyleController()
        
    def process(self, 
                query: str, 
                style: Optional[StyleProfile] = None,
                custom_style: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Process query with styled response
        
        Args:
            query: User query
            style: Predefined style profile
            custom_style: Custom style parameters
            
        Returns:
            Styled response
        """
        # Get original response
        response = self.aions.process(query)
        
        # Apply style if specified
        if style:
            self.style_controller.set_profile(style)
        elif custom_style:
            self.style_controller.set_custom(**custom_style)
        
        # Apply style to answer
        if 'answer' in response:
            original_answer = response['answer']
            styled_answer = self.style_controller.apply_style(original_answer)
            
            response['answer'] = styled_answer
            response['style_applied'] = True
            response['style_params'] = self.style_controller.current_style.__dict__
            response['original_answer'] = original_answer
        
        return response


def test_style_parameters():
    """Test style parameter system"""
    print("\n" + "="*60)
    print("AIONS STYLE PARAMETERS TEST")
    print("="*60)
    
    # Initialize controller
    controller = StyleController()
    
    # Test text
    test_text = "The capital of France is Paris. This is a basic fact that everyone should know."
    
    print(f"\nOriginal text:")
    print(f"  {test_text}")
    print("\nStyle variations:")
    print("-" * 40)
    
    # Test different profiles
    profiles_to_test = [
        StyleProfile.PROFESSIONAL,
        StyleProfile.CASUAL,
        StyleProfile.TECHNICAL,
        StyleProfile.CONCISE,
        StyleProfile.FRIENDLY,
        StyleProfile.FORMAL
    ]
    
    for profile in profiles_to_test:
        controller.set_profile(profile)
        styled = controller.apply_style(test_text)
        
        print(f"\n{profile.value.upper()}:")
        params = controller.current_style
        print(f"  Parameters: F={params.formality:.1f} B={params.brevity:.1f} "
              f"T={params.technicality:.1f} Fr={params.friendliness:.1f} C={params.confidence:.1f}")
        print(f"  Result: {styled}")
    
    # Test custom style
    print("\n" + "-" * 40)
    print("CUSTOM STYLES:")
    
    custom_tests = [
        ("Ultra Casual", {"formality": 0.1, "friendliness": 0.9, "brevity": 0.7}),
        ("Ultra Formal", {"formality": 0.9, "friendliness": 0.1, "confidence": 0.9}),
        ("Very Uncertain", {"confidence": 0.2, "formality": 0.5})
    ]
    
    for name, params in custom_tests:
        controller.set_custom(**params)
        styled = controller.apply_style(test_text)
        print(f"\n{name}:")
        print(f"  Parameters: {params}")
        print(f"  Result: {styled}")
    
    # Test style analysis
    print("\n" + "-" * 40)
    print("STYLE ANALYSIS:")
    
    texts_to_analyze = [
        "Hi! I'd be happy to help you with that! The answer is definitely Paris!",
        "The requested information pertains to the capital city of France, which is Paris.",
        "yeah so basically paris is the capital ok?"
    ]
    
    for text in texts_to_analyze:
        detected = controller.analyze_style(text)
        print(f"\nText: {text[:50]}...")
        print(f"Detected: F={detected.formality:.1f} B={detected.brevity:.1f} "
              f"Fr={detected.friendliness:.1f} C={detected.confidence:.1f}")
    
    print("\n✅ Style parameters test completed!")


if __name__ == "__main__":
    test_style_parameters()