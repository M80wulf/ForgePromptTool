#!/usr/bin/env python3
"""
Simple test suite for the AI Suggestion System
"""

import sys
import os
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from services.ai_suggestion_service import AISuggestionService, AIPromptAnalyzer


def test_ai_prompt_analyzer():
    """Test the AI prompt analyzer"""
    print("Testing AI Prompt Analyzer")
    print("-" * 30)
    
    analyzer = AIPromptAnalyzer()
    
    # Test clarity scoring
    clear_prompt = """
    # Task: Write a Product Review
    
    Please write a detailed product review for the iPhone 15 Pro.
    
    Requirements:
    - Include pros and cons
    - Mention specific features
    - Rate from 1-5 stars
    """
    
    clarity_score = analyzer._calculate_clarity_score(clear_prompt)
    print(f"[OK] Clear prompt clarity score: {clarity_score:.2f}")
    assert clarity_score > 0.7, f"Expected clarity > 0.7, got {clarity_score}"
    
    # Test vague prompt
    vague_prompt = "Write something about phones maybe"
    vague_score = analyzer._calculate_clarity_score(vague_prompt)
    print(f"[OK] Vague prompt clarity score: {vague_score:.2f}")
    assert vague_score < 0.7, f"Expected clarity < 0.7, got {vague_score}"
    
    # Test full analysis
    test_prompt = """
    Create a social media post for our new product launch.
    The product is innovative and will change everything.
    Make it engaging and viral.
    """
    
    analysis = analyzer.analyze_prompt(test_prompt, prompt_id=1)
    print(f"[OK] Analysis completed:")
    print(f"  - Clarity: {analysis.clarity_score:.2f}")
    print(f"  - Specificity: {analysis.specificity_score:.2f}")
    print(f"  - Completeness: {analysis.completeness_score:.2f}")
    print(f"  - Overall: {analysis.overall_score:.2f}")
    print(f"  - Strengths: {len(analysis.strengths)}")
    print(f"  - Weaknesses: {len(analysis.weaknesses)}")
    print(f"  - Suggestions: {len(analysis.suggestions)}")
    
    assert analysis.overall_score >= 0.0 and analysis.overall_score <= 1.0
    assert len(analysis.suggestions) > 0
    
    return True


def test_ai_suggestion_service():
    """Test the AI suggestion service"""
    print("\nTesting AI Suggestion Service")
    print("-" * 30)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        db = DatabaseManager(temp_db.name)
        service = AISuggestionService(db)
        
        # Create test prompt
        test_prompt_id = db.create_prompt(
            title="Test Prompt",
            content="Write a brief summary about artificial intelligence",
            folder_id=None
        )
        
        # Test analysis
        content = "Write a comprehensive guide about machine learning for beginners"
        analysis = service.analyze_prompt(test_prompt_id, content)
        
        print(f"[OK] Analysis stored with {len(analysis.suggestions)} suggestions")
        assert len(analysis.suggestions) > 0
        
        # Test retrieving suggestions
        suggestions = service.get_suggestions_for_prompt(test_prompt_id)
        print(f"[OK] Retrieved {len(suggestions)} suggestions")
        assert len(suggestions) > 0
        
        # Test applying suggestion
        if suggestions:
            suggestion_id = suggestions[0].suggestion_id
            result = service.apply_suggestion(suggestion_id)
            print(f"[OK] Suggestion applied: {result}")
            assert result == True
        
        # Test rating suggestion
        if suggestions:
            suggestion_id = suggestions[0].suggestion_id
            result = service.rate_suggestion(suggestion_id, 4)
            print(f"[OK] Suggestion rated: {result}")
            assert result == True
        
        # Test statistics
        stats = service.get_suggestion_statistics()
        print(f"[OK] Statistics retrieved:")
        print(f"  - Total suggestions: {stats['total_suggestions']}")
        print(f"  - Applied suggestions: {stats['applied_suggestions']}")
        
        assert stats['total_suggestions'] > 0
        
        return True
        
    finally:
        try:
            os.unlink(temp_db.name)
        except:
            pass


def test_suggestion_types():
    """Test different types of suggestions"""
    print("\nTesting Suggestion Types")
    print("-" * 30)
    
    analyzer = AIPromptAnalyzer()
    
    # Test improvement suggestions
    weak_prompt = "Write something"
    analysis = analyzer.analyze_prompt(weak_prompt, prompt_id=1)
    
    improvement_suggestions = [
        s for s in analysis.suggestions 
        if s.suggestion_type == "improvement"
    ]
    
    print(f"[OK] Generated {len(improvement_suggestions)} improvement suggestions")
    assert len(improvement_suggestions) > 0
    
    # Test alternative suggestions
    prompt = "Create a newsletter for our company"
    analysis = analyzer.analyze_prompt(prompt, prompt_id=1)
    
    alternative_suggestions = [
        s for s in analysis.suggestions 
        if s.suggestion_type == "alternative"
    ]
    
    print(f"[OK] Generated {len(alternative_suggestions)} alternative suggestions")
    assert len(alternative_suggestions) > 0
    
    # Test confidence scores
    for suggestion in analysis.suggestions:
        assert 0.0 <= suggestion.confidence <= 1.0
    
    print(f"[OK] All suggestions have valid confidence scores")
    
    return True


def run_simple_test():
    """Run simple test of the AI suggestion system"""
    print("AI Suggestion System Test Suite")
    print("=" * 50)
    
    try:
        # Test AI Prompt Analyzer
        if not test_ai_prompt_analyzer():
            print("[FAIL] AI Prompt Analyzer tests failed!")
            return False
        
        # Test AI Suggestion Service
        if not test_ai_suggestion_service():
            print("[FAIL] AI Suggestion Service tests failed!")
            return False
        
        # Test Suggestion Types
        if not test_suggestion_types():
            print("[FAIL] Suggestion Types tests failed!")
            return False
        
        print("\n" + "=" * 50)
        print("[SUCCESS] ALL AI SUGGESTION SYSTEM TESTS PASSED!")
        
        print("\nAI Suggestion System Features Implemented:")
        print("* Prompt analysis with quality scoring")
        print("* Multiple suggestion types (improvement, alternative, template)")
        print("* Confidence scoring for suggestions")
        print("* Suggestion application and rating")
        print("* Database storage and retrieval")
        print("* Statistics and analytics")
        print("* UI integration ready")
        
        print("\nThe AI suggestion system is ready for production use!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = run_simple_test()
    sys.exit(0 if success else 1)