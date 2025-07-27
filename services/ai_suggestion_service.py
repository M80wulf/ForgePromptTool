#!/usr/bin/env python3
"""
AI-powered prompt suggestion service for the Prompt Organizer application.
Provides intelligent recommendations for improving prompts and suggesting new ones.
"""

import re
import json
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class PromptSuggestion:
    """Represents an AI-generated suggestion for a prompt"""
    suggestion_id: str
    prompt_id: Optional[int]
    suggestion_type: str  # 'improvement', 'alternative', 'template', 'completion'
    title: str
    content: str
    reasoning: str
    confidence: float  # 0.0 to 1.0
    category: str
    tags: List[str]
    created_at: datetime
    applied: bool = False
    user_rating: Optional[int] = None  # 1-5 stars


@dataclass
class PromptAnalysis:
    """Analysis results for a prompt"""
    prompt_id: int
    clarity_score: float
    specificity_score: float
    completeness_score: float
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[PromptSuggestion]
    analyzed_at: datetime


class AIPromptAnalyzer:
    """Analyzes prompts and provides AI-powered insights"""
    
    def __init__(self):
        self.improvement_patterns = self._load_improvement_patterns()
        self.quality_indicators = self._load_quality_indicators()
        self.suggestion_templates = self._load_suggestion_templates()
    
    def analyze_prompt(self, prompt_content: str, prompt_id: int = None) -> PromptAnalysis:
        """Analyze a prompt and provide comprehensive feedback"""
        
        # Calculate quality scores
        clarity_score = self._calculate_clarity_score(prompt_content)
        specificity_score = self._calculate_specificity_score(prompt_content)
        completeness_score = self._calculate_completeness_score(prompt_content)
        overall_score = (clarity_score + specificity_score + completeness_score) / 3
        
        # Identify strengths and weaknesses
        strengths = self._identify_strengths(prompt_content)
        weaknesses = self._identify_weaknesses(prompt_content)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(prompt_content, prompt_id, weaknesses)
        
        return PromptAnalysis(
            prompt_id=prompt_id,
            clarity_score=clarity_score,
            specificity_score=specificity_score,
            completeness_score=completeness_score,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            analyzed_at=datetime.now()
        )
    
    def _calculate_clarity_score(self, content: str) -> float:
        """Calculate clarity score based on various factors"""
        score = 0.5  # Base score
        
        # Check for clear structure
        if self._has_clear_structure(content):
            score += 0.2
        
        # Check for specific language
        if self._has_specific_language(content):
            score += 0.15
        
        # Check for ambiguous terms
        if not self._has_ambiguous_terms(content):
            score += 0.1
        
        # Check for proper grammar and spelling
        if self._has_good_grammar(content):
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_specificity_score(self, content: str) -> float:
        """Calculate specificity score"""
        score = 0.3  # Base score
        
        # Check for specific details
        if self._has_specific_details(content):
            score += 0.25
        
        # Check for examples
        if self._has_examples(content):
            score += 0.2
        
        # Check for constraints or requirements
        if self._has_constraints(content):
            score += 0.15
        
        # Check for context
        if self._has_context(content):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_completeness_score(self, content: str) -> float:
        """Calculate completeness score"""
        score = 0.4  # Base score
        
        # Check for clear objective
        if self._has_clear_objective(content):
            score += 0.2
        
        # Check for sufficient detail
        if self._has_sufficient_detail(content):
            score += 0.2
        
        # Check for output format specification
        if self._has_output_format(content):
            score += 0.1
        
        # Check for role definition
        if self._has_role_definition(content):
            score += 0.1
        
        return min(1.0, score)
    
    def _has_clear_structure(self, content: str) -> bool:
        """Check if prompt has clear structure"""
        # Look for headers, bullet points, numbered lists
        structure_patterns = [
            r'^\s*#',  # Headers
            r'^\s*\d+\.',  # Numbered lists
            r'^\s*[-*]',  # Bullet points
            r'^\s*[A-Z][a-z]+:',  # Section labels
        ]
        
        for pattern in structure_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False
    
    def _has_specific_language(self, content: str) -> bool:
        """Check for specific, concrete language"""
        vague_words = ['thing', 'stuff', 'something', 'anything', 'everything', 'some', 'any']
        specific_indicators = ['exactly', 'specifically', 'precisely', 'detailed', 'comprehensive']
        
        vague_count = sum(1 for word in vague_words if word in content.lower())
        specific_count = sum(1 for word in specific_indicators if word in content.lower())
        
        return specific_count > vague_count
    
    def _has_ambiguous_terms(self, content: str) -> bool:
        """Check for ambiguous terms"""
        ambiguous_terms = ['maybe', 'perhaps', 'might', 'could be', 'sort of', 'kind of']
        return any(term in content.lower() for term in ambiguous_terms)
    
    def _has_good_grammar(self, content: str) -> bool:
        """Basic grammar check"""
        # Simple heuristics for grammar quality
        sentences = re.split(r'[.!?]+', content)
        if not sentences:
            return False
        
        # Check for proper capitalization
        capitalized_sentences = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        return capitalized_sentences / len([s for s in sentences if s.strip()]) > 0.8
    
    def _has_specific_details(self, content: str) -> bool:
        """Check for specific details"""
        detail_indicators = [
            r'\d+',  # Numbers
            r'[A-Z][a-z]+ \d+',  # Dates
            r'\$\d+',  # Money
            r'\d+%',  # Percentages
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]
        
        return any(re.search(pattern, content) for pattern in detail_indicators)
    
    def _has_examples(self, content: str) -> bool:
        """Check for examples"""
        example_keywords = ['example', 'for instance', 'such as', 'like', 'including']
        return any(keyword in content.lower() for keyword in example_keywords)
    
    def _has_constraints(self, content: str) -> bool:
        """Check for constraints or requirements"""
        constraint_keywords = ['must', 'should', 'required', 'limit', 'maximum', 'minimum', 'only', 'exactly']
        return any(keyword in content.lower() for keyword in constraint_keywords)
    
    def _has_context(self, content: str) -> bool:
        """Check for context information"""
        context_indicators = ['background', 'context', 'situation', 'scenario', 'given that', 'assuming']
        return any(indicator in content.lower() for indicator in context_indicators)
    
    def _has_clear_objective(self, content: str) -> bool:
        """Check for clear objective"""
        objective_patterns = [
            r'(create|generate|write|analyze|explain|describe|list|provide)',
            r'(help me|assist with|I need|I want)',
            r'(the goal is|the objective is|the purpose is)'
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in objective_patterns)
    
    def _has_sufficient_detail(self, content: str) -> bool:
        """Check for sufficient detail"""
        word_count = len(content.split())
        return word_count >= 20  # Minimum threshold for detailed prompts
    
    def _has_output_format(self, content: str) -> bool:
        """Check for output format specification"""
        format_keywords = ['format', 'structure', 'layout', 'organize', 'bullet points', 'numbered list', 'table', 'json', 'markdown']
        return any(keyword in content.lower() for keyword in format_keywords)
    
    def _has_role_definition(self, content: str) -> bool:
        """Check for role definition"""
        role_patterns = [
            r'you are (a|an)',
            r'act as (a|an)',
            r'pretend to be',
            r'role.*of',
            r'expert in',
            r'specialist in'
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in role_patterns)
    
    def _identify_strengths(self, content: str) -> List[str]:
        """Identify strengths in the prompt"""
        strengths = []
        
        if self._has_clear_structure(content):
            strengths.append("Well-structured with clear organization")
        
        if self._has_specific_language(content):
            strengths.append("Uses specific and concrete language")
        
        if self._has_examples(content):
            strengths.append("Includes helpful examples")
        
        if self._has_constraints(content):
            strengths.append("Clearly defines constraints and requirements")
        
        if self._has_context(content):
            strengths.append("Provides good context and background")
        
        if self._has_role_definition(content):
            strengths.append("Clearly defines the AI's role")
        
        if self._has_output_format(content):
            strengths.append("Specifies desired output format")
        
        if len(content.split()) > 50:
            strengths.append("Comprehensive and detailed")
        
        return strengths
    
    def _identify_weaknesses(self, content: str) -> List[str]:
        """Identify weaknesses in the prompt"""
        weaknesses = []
        
        if not self._has_clear_objective(content):
            weaknesses.append("Unclear objective or goal")
        
        if self._has_ambiguous_terms(content):
            weaknesses.append("Contains ambiguous or vague language")
        
        if not self._has_specific_details(content):
            weaknesses.append("Lacks specific details")
        
        if not self._has_context(content):
            weaknesses.append("Missing context or background information")
        
        if not self._has_output_format(content):
            weaknesses.append("No specified output format")
        
        if len(content.split()) < 10:
            weaknesses.append("Too brief, needs more detail")
        
        if not self._has_constraints(content):
            weaknesses.append("No clear constraints or requirements")
        
        if not self._has_role_definition(content):
            weaknesses.append("AI role not clearly defined")
        
        return weaknesses
    
    def _generate_suggestions(self, content: str, prompt_id: int, weaknesses: List[str]) -> List[PromptSuggestion]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        # Generate improvement suggestions based on weaknesses
        for weakness in weaknesses:
            suggestion = self._create_improvement_suggestion(content, weakness, prompt_id)
            if suggestion:
                suggestions.append(suggestion)
        
        # Generate alternative versions
        alternative = self._create_alternative_suggestion(content, prompt_id)
        if alternative:
            suggestions.append(alternative)
        
        # Generate template suggestions
        template_suggestion = self._create_template_suggestion(content, prompt_id)
        if template_suggestion:
            suggestions.append(template_suggestion)
        
        return suggestions
    
    def _create_improvement_suggestion(self, content: str, weakness: str, prompt_id: int) -> Optional[PromptSuggestion]:
        """Create an improvement suggestion for a specific weakness"""
        improvement_map = {
            "Unclear objective or goal": {
                "title": "Add Clear Objective",
                "content": f"Consider starting your prompt with a clear statement like:\n\n\"Please help me [specific action] by [specific method] to achieve [specific goal].\"\n\nOriginal prompt:\n{content}",
                "reasoning": "Adding a clear objective helps the AI understand exactly what you want to accomplish."
            },
            "Contains ambiguous or vague language": {
                "title": "Use More Specific Language",
                "content": self._suggest_specific_language(content),
                "reasoning": "Specific language reduces ambiguity and improves response quality."
            },
            "Lacks specific details": {
                "title": "Add Specific Details",
                "content": self._suggest_specific_details(content),
                "reasoning": "Specific details help the AI provide more targeted and useful responses."
            },
            "Missing context or background information": {
                "title": "Provide Context",
                "content": self._suggest_context_addition(content),
                "reasoning": "Context helps the AI understand the situation and provide more relevant responses."
            },
            "No specified output format": {
                "title": "Specify Output Format",
                "content": self._suggest_output_format(content),
                "reasoning": "Specifying the desired format ensures you get responses in the structure you need."
            },
            "Too brief, needs more detail": {
                "title": "Expand with More Detail",
                "content": self._suggest_expansion(content),
                "reasoning": "More detailed prompts typically yield better, more comprehensive responses."
            },
            "No clear constraints or requirements": {
                "title": "Add Constraints",
                "content": self._suggest_constraints(content),
                "reasoning": "Clear constraints help focus the AI's response and ensure it meets your specific needs."
            },
            "AI role not clearly defined": {
                "title": "Define AI Role",
                "content": self._suggest_role_definition(content),
                "reasoning": "Defining the AI's role helps it respond from the appropriate perspective and expertise level."
            }
        }
        
        if weakness in improvement_map:
            suggestion_data = improvement_map[weakness]
            return PromptSuggestion(
                suggestion_id=self._generate_suggestion_id(content, weakness),
                prompt_id=prompt_id,
                suggestion_type="improvement",
                title=suggestion_data["title"],
                content=suggestion_data["content"],
                reasoning=suggestion_data["reasoning"],
                confidence=0.8,
                category="Improvement",
                tags=["improvement", "quality"],
                created_at=datetime.now()
            )
        
        return None
    
    def _suggest_specific_language(self, content: str) -> str:
        """Suggest more specific language"""
        suggestions = {
            "thing": "specific item/object/concept",
            "stuff": "specific materials/items",
            "something": "specific item/action",
            "some": "specific number/amount",
            "good": "effective/high-quality/excellent",
            "bad": "ineffective/poor-quality/problematic"
        }
        
        improved_content = content
        for vague, specific in suggestions.items():
            if vague in content.lower():
                improved_content = f"Consider replacing '{vague}' with more specific terms like '{specific}'.\n\n"
                break
        
        return f"{improved_content}Improved version:\n{content}"
    
    def _suggest_specific_details(self, content: str) -> str:
        """Suggest adding specific details"""
        return f"""Consider adding specific details such as:
- Exact numbers, dates, or quantities
- Specific names, brands, or models
- Precise measurements or specifications
- Concrete examples or use cases

Original prompt:
{content}

Enhanced version:
{content}
[Add specific details relevant to your use case]"""
    
    def _suggest_context_addition(self, content: str) -> str:
        """Suggest adding context"""
        return f"""Consider adding context such as:
- Background information about the situation
- Your current knowledge level on the topic
- The intended audience for the response
- Any relevant constraints or limitations

Original prompt:
{content}

Enhanced version:
Context: [Provide relevant background information]

{content}"""
    
    def _suggest_output_format(self, content: str) -> str:
        """Suggest specifying output format"""
        return f"""Consider specifying the desired output format:
- Bullet points for lists
- Numbered steps for procedures
- Table format for comparisons
- Paragraph form for explanations
- JSON/structured data for technical responses

Original prompt:
{content}

Enhanced version:
{content}

Please format your response as: [specify desired format]"""
    
    def _suggest_expansion(self, content: str) -> str:
        """Suggest expanding the prompt"""
        return f"""Consider expanding your prompt with:
- More detailed explanation of what you need
- Specific requirements or criteria
- Examples of what you're looking for
- Any constraints or limitations
- The intended use of the response

Original prompt:
{content}

Expanded version:
{content}

Additional details:
- [Add specific requirements]
- [Add examples or criteria]
- [Add context or constraints]"""
    
    def _suggest_constraints(self, content: str) -> str:
        """Suggest adding constraints"""
        return f"""Consider adding constraints such as:
- Length requirements (e.g., "in 200 words or less")
- Complexity level (e.g., "explain for beginners")
- Specific focus areas (e.g., "focus on practical applications")
- Exclusions (e.g., "avoid technical jargon")

Original prompt:
{content}

Enhanced version:
{content}

Requirements:
- [Add specific constraints]
- [Add length or complexity requirements]
- [Add focus areas or exclusions]"""
    
    def _suggest_role_definition(self, content: str) -> str:
        """Suggest defining AI role"""
        return f"""Consider defining the AI's role:
- "Act as a [specific expert/professional]"
- "You are a [role] with expertise in [area]"
- "Respond as if you were a [specific perspective]"

Original prompt:
{content}

Enhanced version:
You are a [define specific role/expertise].

{content}"""
    
    def _create_alternative_suggestion(self, content: str, prompt_id: int) -> Optional[PromptSuggestion]:
        """Create an alternative version of the prompt"""
        # Generate a restructured version
        alternative_content = self._restructure_prompt(content)
        
        return PromptSuggestion(
            suggestion_id=self._generate_suggestion_id(content, "alternative"),
            prompt_id=prompt_id,
            suggestion_type="alternative",
            title="Alternative Prompt Structure",
            content=alternative_content,
            reasoning="This alternative structure may improve clarity and response quality.",
            confidence=0.7,
            category="Alternative",
            tags=["alternative", "restructure"],
            created_at=datetime.now()
        )
    
    def _create_template_suggestion(self, content: str, prompt_id: int) -> Optional[PromptSuggestion]:
        """Suggest converting to a template"""
        if self._could_be_template(content):
            template_content = self._convert_to_template(content)
            
            return PromptSuggestion(
                suggestion_id=self._generate_suggestion_id(content, "template"),
                prompt_id=prompt_id,
                suggestion_type="template",
                title="Convert to Reusable Template",
                content=template_content,
                reasoning="This prompt could be converted to a reusable template for similar use cases.",
                confidence=0.6,
                category="Template",
                tags=["template", "reusable"],
                created_at=datetime.now()
            )
        
        return None
    
    def _restructure_prompt(self, content: str) -> str:
        """Restructure prompt for better clarity"""
        return f"""# Restructured Prompt

## Objective
[Clearly state what you want to achieve]

## Context
[Provide relevant background information]

## Requirements
{content}

## Output Format
[Specify how you want the response formatted]

## Additional Notes
[Any other relevant information]"""
    
    def _could_be_template(self, content: str) -> bool:
        """Check if prompt could benefit from being a template"""
        # Look for patterns that suggest reusability
        template_indicators = [
            r'\b(write|create|generate)\b.*\bfor\b',  # "write X for Y"
            r'\b(analyze|review|evaluate)\b',  # Analysis tasks
            r'\b(explain|describe)\b.*\bto\b',  # Explanation tasks
            r'\b(help|assist)\b.*\bwith\b',  # Help requests
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in template_indicators)
    
    def _convert_to_template(self, content: str) -> str:
        """Convert prompt to template format"""
        # Simple template conversion - replace specific terms with variables
        template_content = content
        
        # Common replacements
        replacements = [
            (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '{person_name}'),  # Names
            (r'\b\d{4}\b', '{year}'),  # Years
            (r'\b[A-Z][a-z]+\s+Company\b', '{company_name}'),  # Company names
            (r'\$\d+', '{amount}'),  # Money amounts
        ]
        
        for pattern, replacement in replacements:
            if re.search(pattern, template_content):
                template_content = re.sub(pattern, replacement, template_content, count=1)
                break
        
        return f"""Template Version:
{template_content}

Variables:
- {{person_name}}: Name of the person
- {{year}}: Relevant year
- {{company_name}}: Company name
- {{amount}}: Monetary amount

Original:
{content}"""
    
    def _generate_suggestion_id(self, content: str, suggestion_type: str) -> str:
        """Generate unique suggestion ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{suggestion_type}_{content_hash}_{int(datetime.now().timestamp())}"
    
    def _load_improvement_patterns(self) -> Dict[str, Any]:
        """Load improvement patterns (placeholder for future ML models)"""
        return {}
    
    def _load_quality_indicators(self) -> Dict[str, Any]:
        """Load quality indicators (placeholder for future ML models)"""
        return {}
    
    def _load_suggestion_templates(self) -> Dict[str, Any]:
        """Load suggestion templates (placeholder for future ML models)"""
        return {}


class AISuggestionService:
    """Service for managing AI-powered prompt suggestions"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.analyzer = AIPromptAnalyzer()
        self._init_database()
    
    def _init_database(self):
        """Initialize suggestion-related database tables"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_id TEXT UNIQUE NOT NULL,
                    prompt_id INTEGER,
                    suggestion_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    applied BOOLEAN DEFAULT FALSE,
                    user_rating INTEGER,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    clarity_score REAL NOT NULL,
                    specificity_score REAL NOT NULL,
                    completeness_score REAL NOT NULL,
                    overall_score REAL NOT NULL,
                    strengths TEXT NOT NULL,
                    weaknesses TEXT NOT NULL,
                    analyzed_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            """)
            
            conn.commit()
    
    def analyze_prompt(self, prompt_id: int, prompt_content: str) -> PromptAnalysis:
        """Analyze a prompt and store results"""
        analysis = self.analyzer.analyze_prompt(prompt_content, prompt_id)
        
        # Store analysis in database
        self._store_analysis(analysis)
        
        # Store suggestions
        for suggestion in analysis.suggestions:
            self._store_suggestion(suggestion)
        
        return analysis
    
    def get_suggestions_for_prompt(self, prompt_id: int) -> List[PromptSuggestion]:
        """Get all suggestions for a specific prompt"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT suggestion_id, prompt_id, suggestion_type, title, content,
                       reasoning, confidence, category, tags, created_at, applied, user_rating
                FROM prompt_suggestions
                WHERE prompt_id = ?
                ORDER BY confidence DESC, created_at DESC
            """, (prompt_id,))
            
            results = cursor.fetchall()
            suggestions = []
            
            for row in results:
                suggestions.append(PromptSuggestion(
                    suggestion_id=row[0],
                    prompt_id=row[1],
                    suggestion_type=row[2],
                    title=row[3],
                    content=row[4],
                    reasoning=row[5],
                    confidence=row[6],
                    category=row[7],
                    tags=json.loads(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    applied=bool(row[10]),
                    user_rating=row[11]
                ))
            
            return suggestions
    
    def apply_suggestion(self, suggestion_id: str) -> bool:
        """Mark a suggestion as applied"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE prompt_suggestions SET applied = 1 WHERE suggestion_id = ?", (suggestion_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def rate_suggestion(self, suggestion_id: str, rating: int) -> bool:
        """Rate a suggestion (1-5 stars)"""
        if not 1 <= rating <= 5:
            return False
        
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE prompt_suggestions SET user_rating = ? WHERE suggestion_id = ?", (rating, suggestion_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_prompt_analysis(self, prompt_id: int) -> Optional[PromptAnalysis]:
        """Get the latest analysis for a prompt"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prompt_id, clarity_score, specificity_score, completeness_score,
                       overall_score, strengths, weaknesses, analyzed_at
                FROM prompt_analyses
                WHERE prompt_id = ?
                ORDER BY analyzed_at DESC
                LIMIT 1
            """, (prompt_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Get suggestions for this prompt
            suggestions = self.get_suggestions_for_prompt(prompt_id)
            
            return PromptAnalysis(
                prompt_id=result[0],
                clarity_score=result[1],
                specificity_score=result[2],
                completeness_score=result[3],
                overall_score=result[4],
                strengths=json.loads(result[5]),
                weaknesses=json.loads(result[6]),
                suggestions=suggestions,
                analyzed_at=datetime.fromisoformat(result[7])
            )
    
    def get_suggestion_statistics(self) -> Dict[str, Any]:
        """Get statistics about suggestions"""
        import sqlite3
        
        stats = {}
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Total suggestions
            cursor.execute("SELECT COUNT(*) FROM prompt_suggestions")
            stats['total_suggestions'] = cursor.fetchone()[0]
            
            # Applied suggestions
            cursor.execute("SELECT COUNT(*) FROM prompt_suggestions WHERE applied = 1")
            stats['applied_suggestions'] = cursor.fetchone()[0]
            
            # Average rating
            cursor.execute("SELECT AVG(user_rating) FROM prompt_suggestions WHERE user_rating IS NOT NULL")
            avg_rating = cursor.fetchone()[0]
            stats['average_rating'] = round(avg_rating, 2) if avg_rating else None
            
            # Suggestions by type
            cursor.execute("""
                SELECT suggestion_type, COUNT(*)
                FROM prompt_suggestions
                GROUP BY suggestion_type
            """)
            stats['by_type'] = dict(cursor.fetchall())
            
            # Suggestions by category
            cursor.execute("""
                SELECT category, COUNT(*)
                FROM prompt_suggestions
                GROUP BY category
            """)
            stats['by_category'] = dict(cursor.fetchall())
        
        return stats
    
    def _store_analysis(self, analysis: PromptAnalysis):
        """Store prompt analysis in database"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prompt_analyses
                (prompt_id, clarity_score, specificity_score, completeness_score,
                 overall_score, strengths, weaknesses, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.prompt_id,
                analysis.clarity_score,
                analysis.specificity_score,
                analysis.completeness_score,
                analysis.overall_score,
                json.dumps(analysis.strengths),
                json.dumps(analysis.weaknesses),
                analysis.analyzed_at.isoformat()
            ))
            conn.commit()
    
    def generate_prompt_from_description(self, description: str, prompt_type: str = "General Purpose", length_preference: str = "Medium") -> str:
        """Generate a complete prompt from a short description"""
        try:
            # Create a comprehensive prompt based on the description and parameters
            generated_prompt = self._create_prompt_from_description(description, prompt_type, length_preference)
            return generated_prompt
        except Exception as e:
            print(f"Error generating prompt: {e}")
            return ""
    
    def _create_prompt_from_description(self, description: str, prompt_type: str, length_preference: str) -> str:
        """Create a detailed prompt from user description"""
        
        # Base prompt structure templates by type
        type_templates = {
            "General Purpose": {
                "intro": "Please help me with the following task:",
                "structure": "clear and comprehensive",
                "focus": "practical and actionable"
            },
            "Creative Writing": {
                "intro": "As a creative writing assistant, please help me:",
                "structure": "imaginative and engaging",
                "focus": "creativity and storytelling"
            },
            "Business Communication": {
                "intro": "As a professional business communication expert, please assist me with:",
                "structure": "professional and structured",
                "focus": "clarity and business effectiveness"
            },
            "Technical Documentation": {
                "intro": "As a technical documentation specialist, please help me:",
                "structure": "detailed and systematic",
                "focus": "accuracy and technical precision"
            },
            "Educational Content": {
                "intro": "As an educational content creator, please assist me in:",
                "structure": "pedagogical and progressive",
                "focus": "learning and comprehension"
            },
            "Data Analysis": {
                "intro": "As a data analysis expert, please help me:",
                "structure": "analytical and methodical",
                "focus": "insights and data-driven conclusions"
            },
            "Code Generation": {
                "intro": "As a programming expert, please assist me with:",
                "structure": "logical and well-documented",
                "focus": "functionality and best practices"
            },
            "Problem Solving": {
                "intro": "As a problem-solving specialist, please help me:",
                "structure": "systematic and solution-oriented",
                "focus": "practical solutions and implementation"
            }
        }
        
        # Length preferences
        length_specs = {
            "Short": {
                "detail_level": "concise",
                "word_target": "100-200 words",
                "complexity": "straightforward"
            },
            "Medium": {
                "detail_level": "comprehensive",
                "word_target": "200-500 words",
                "complexity": "detailed with examples"
            },
            "Detailed": {
                "detail_level": "thorough",
                "word_target": "500+ words",
                "complexity": "comprehensive with multiple examples and considerations"
            }
        }
        
        # Get template and specs
        template = type_templates.get(prompt_type, type_templates["General Purpose"])
        length_spec = length_specs.get(length_preference, length_specs["Medium"])
        
        # Analyze the description to extract key elements
        key_elements = self._extract_key_elements(description)
        
        # Build the comprehensive prompt
        prompt_parts = []
        
        # 1. Role and Introduction
        prompt_parts.append(f"{template['intro']}")
        prompt_parts.append("")
        
        # 2. Main Task Description
        prompt_parts.append("## Task Description")
        prompt_parts.append(description)
        prompt_parts.append("")
        
        # 3. Specific Requirements
        if key_elements['requirements']:
            prompt_parts.append("## Requirements")
            for req in key_elements['requirements']:
                prompt_parts.append(f"- {req}")
            prompt_parts.append("")
        
        # 4. Context and Background
        if key_elements['context']:
            prompt_parts.append("## Context")
            prompt_parts.append(key_elements['context'])
            prompt_parts.append("")
        
        # 5. Output Specifications
        prompt_parts.append("## Output Requirements")
        prompt_parts.append(f"- Style: {template['structure']}")
        prompt_parts.append(f"- Focus: {template['focus']}")
        prompt_parts.append(f"- Length: {length_spec['word_target']}")
        prompt_parts.append(f"- Detail level: {length_spec['detail_level']}")
        
        # Add format specifications based on type
        if prompt_type == "Business Communication":
            prompt_parts.append("- Format: Professional business format with clear sections")
            prompt_parts.append("- Tone: Professional and courteous")
        elif prompt_type == "Creative Writing":
            prompt_parts.append("- Format: Narrative or creative structure as appropriate")
            prompt_parts.append("- Tone: Engaging and imaginative")
        elif prompt_type == "Technical Documentation":
            prompt_parts.append("- Format: Structured documentation with clear headings")
            prompt_parts.append("- Tone: Technical but accessible")
        elif prompt_type == "Educational Content":
            prompt_parts.append("- Format: Learning-focused with clear progression")
            prompt_parts.append("- Tone: Educational and encouraging")
        elif prompt_type == "Data Analysis":
            prompt_parts.append("- Format: Analytical structure with data insights")
            prompt_parts.append("- Tone: Objective and data-driven")
        elif prompt_type == "Code Generation":
            prompt_parts.append("- Format: Well-commented code with explanations")
            prompt_parts.append("- Tone: Technical and instructional")
        elif prompt_type == "Problem Solving":
            prompt_parts.append("- Format: Problem-solution structure")
            prompt_parts.append("- Tone: Solution-oriented and practical")
        else:
            prompt_parts.append("- Format: Clear and well-organized")
            prompt_parts.append("- Tone: Helpful and informative")
        
        prompt_parts.append("")
        
        # 6. Additional Guidelines
        prompt_parts.append("## Additional Guidelines")
        if length_preference == "Detailed":
            prompt_parts.append("- Provide multiple examples and use cases")
            prompt_parts.append("- Include potential challenges and solutions")
            prompt_parts.append("- Consider different perspectives or approaches")
        elif length_preference == "Medium":
            prompt_parts.append("- Include relevant examples")
            prompt_parts.append("- Provide practical implementation details")
        else:  # Short
            prompt_parts.append("- Focus on the most essential information")
            prompt_parts.append("- Be direct and actionable")
        
        prompt_parts.append("- Ensure accuracy and relevance")
        prompt_parts.append("- Use clear, understandable language")
        
        # 7. Quality Assurance
        if key_elements['quality_notes']:
            prompt_parts.append("")
            prompt_parts.append("## Quality Considerations")
            for note in key_elements['quality_notes']:
                prompt_parts.append(f"- {note}")
        
        return "\n".join(prompt_parts)
    
    def _extract_key_elements(self, description: str) -> Dict[str, Any]:
        """Extract key elements from the user's description"""
        elements = {
            'requirements': [],
            'context': '',
            'quality_notes': []
        }
        
        # Look for requirement indicators
        requirement_patterns = [
            r'must\s+([^.!?]+)',
            r'should\s+([^.!?]+)',
            r'need\s+to\s+([^.!?]+)',
            r'require[sd]?\s+([^.!?]+)',
            r'important\s+to\s+([^.!?]+)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                elements['requirements'].append(match.strip())
        
        # Look for context indicators
        context_patterns = [
            r'for\s+([^.!?]+)',
            r'in\s+the\s+context\s+of\s+([^.!?]+)',
            r'when\s+([^.!?]+)',
            r'because\s+([^.!?]+)'
        ]
        
        for pattern in context_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                elements['context'] = match.group(1).strip()
                break
        
        # Look for quality indicators
        if 'professional' in description.lower():
            elements['quality_notes'].append('Maintain professional standards')
        if 'beginner' in description.lower() or 'simple' in description.lower():
            elements['quality_notes'].append('Keep language simple and accessible')
        if 'expert' in description.lower() or 'advanced' in description.lower():
            elements['quality_notes'].append('Include advanced concepts and terminology')
        if 'quick' in description.lower() or 'fast' in description.lower():
            elements['quality_notes'].append('Prioritize efficiency and speed')
        
        return elements
    
    def _store_suggestion(self, suggestion: PromptSuggestion):
        """Store suggestion in database"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO prompt_suggestions
                (suggestion_id, prompt_id, suggestion_type, title, content, reasoning,
                 confidence, category, tags, created_at, applied, user_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion.suggestion_id,
                suggestion.prompt_id,
                suggestion.suggestion_type,
                suggestion.title,
                suggestion.content,
                suggestion.reasoning,
                suggestion.confidence,
                suggestion.category,
                json.dumps(suggestion.tags),
                suggestion.created_at.isoformat(),
                suggestion.applied,
                suggestion.user_rating
            ))
            conn.commit()