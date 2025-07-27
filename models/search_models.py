"""
Advanced search models and query parsing for the Prompt Organizer
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import re


class SearchOperator(Enum):
    """Search operators for advanced queries"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class SearchField(Enum):
    """Searchable fields"""
    TITLE = "title"
    CONTENT = "content"
    TAGS = "tags"
    FOLDER = "folder"
    CREATED = "created"
    UPDATED = "updated"
    ALL = "all"


@dataclass
class SearchTerm:
    """Individual search term"""
    field: SearchField
    value: str
    operator: Optional[SearchOperator] = None
    is_regex: bool = False
    is_exact: bool = False
    is_negated: bool = False


@dataclass
class SearchQuery:
    """Complete search query with multiple terms"""
    terms: List[SearchTerm]
    global_operator: SearchOperator = SearchOperator.AND
    case_sensitive: bool = False
    
    def __post_init__(self):
        if not self.terms:
            self.terms = []


@dataclass
class SearchResult:
    """Search result with metadata"""
    id: int
    title: str
    content: str
    tags: str = ""
    folder_name: str = ""
    created_at: str = ""
    updated_at: str = ""
    score: Optional[float] = None
    highlights: List[str] = None
    
    def __post_init__(self):
        if self.highlights is None:
            self.highlights = []


class SearchQueryParser:
    """Parser for advanced search queries"""
    
    def __init__(self):
        # Regex patterns for parsing search queries
        self.field_pattern = re.compile(r'(\w+):')
        self.quoted_pattern = re.compile(r'"([^"]*)"')
        self.regex_pattern = re.compile(r'/([^/]+)/')
        self.operator_pattern = re.compile(r'\b(AND|OR|NOT)\b', re.IGNORECASE)
        self.negation_pattern = re.compile(r'^-(.+)')
    
    def parse(self, query_string: str) -> SearchQuery:
        """Parse a search query string into a SearchQuery object"""
        if not query_string.strip():
            return SearchQuery([])
        
        # Normalize the query
        query_string = query_string.strip()
        
        # Split by operators while preserving them
        parts = self._split_by_operators(query_string)
        
        terms = []
        current_operator = None
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check if this part is an operator
            if part.upper() in ['AND', 'OR', 'NOT']:
                current_operator = SearchOperator(part.upper())
                continue
            
            # Parse the search term
            term = self._parse_term(part)
            if term:
                term.operator = current_operator
                terms.append(term)
                current_operator = None
        
        return SearchQuery(terms)
    
    def _split_by_operators(self, query: str) -> List[str]:
        """Split query by operators while preserving quoted strings and regex"""
        # First, protect quoted strings and regex patterns
        protected_parts = {}
        counter = 0
        
        # Protect quoted strings
        def protect_quoted(match):
            nonlocal counter
            key = f"__QUOTED_{counter}__"
            protected_parts[key] = match.group(0)
            counter += 1
            return key
        
        query = self.quoted_pattern.sub(protect_quoted, query)
        
        # Protect regex patterns
        def protect_regex(match):
            nonlocal counter
            key = f"__REGEX_{counter}__"
            protected_parts[key] = match.group(0)
            counter += 1
            return key
        
        query = self.regex_pattern.sub(protect_regex, query)
        
        # Split by operators
        parts = self.operator_pattern.split(query)
        
        # Restore protected parts
        for i, part in enumerate(parts):
            for key, value in protected_parts.items():
                part = part.replace(key, value)
            parts[i] = part
        
        return parts
    
    def _parse_term(self, term_string: str) -> Optional[SearchTerm]:
        """Parse a single search term"""
        term_string = term_string.strip()
        if not term_string:
            return None
        
        # Check for negation
        is_negated = False
        negation_match = self.negation_pattern.match(term_string)
        if negation_match:
            is_negated = True
            term_string = negation_match.group(1)
        
        # Check for field specification
        field = SearchField.ALL
        field_match = self.field_pattern.match(term_string)
        if field_match:
            field_name = field_match.group(1).lower()
            try:
                field = SearchField(field_name)
                term_string = term_string[len(field_match.group(0)):].strip()
            except ValueError:
                # Invalid field name, treat as regular search
                pass
        
        # Check for regex pattern (including regex: prefix)
        is_regex = False
        if term_string.startswith('regex:'):
            is_regex = True
            term_string = term_string[6:].strip()
        else:
            regex_match = self.regex_pattern.match(term_string)
            if regex_match:
                is_regex = True
                term_string = regex_match.group(1)
        
        # Check for exact match (quoted)
        is_exact = False
        quoted_match = self.quoted_pattern.match(term_string)
        if quoted_match:
            is_exact = True
            term_string = quoted_match.group(1)
        
        return SearchTerm(
            field=field,
            value=term_string,
            is_regex=is_regex,
            is_exact=is_exact,
            is_negated=is_negated
        )


class AdvancedSearchEngine:
    """Advanced search engine for prompts"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.parser = SearchQueryParser()
    
    def search(self, query_string: str, folder_id: Optional[int] = None,
               tag_ids: Optional[List[int]] = None,
               is_favorite: Optional[bool] = None,
               is_template: Optional[bool] = None) -> List[SearchResult]:
        """Perform advanced search on prompts"""
        
        # Parse the query
        search_query = self.parser.parse(query_string)
        
        if not search_query.terms:
            # No search terms, return all prompts with filters
            prompts = self.db.get_prompts(
                folder_id=folder_id,
                tag_ids=tag_ids,
                is_favorite=is_favorite,
                is_template=is_template
            )
            return [self._prompt_to_search_result(prompt) for prompt in prompts]
        
        # Get all prompts first
        all_prompts = self.db.get_prompts(
            folder_id=folder_id,
            tag_ids=tag_ids,
            is_favorite=is_favorite,
            is_template=is_template
        )
        
        # Filter prompts based on search query
        matching_prompts = []
        
        for prompt in all_prompts:
            if self._matches_query(prompt, search_query):
                result = self._prompt_to_search_result(prompt)
                # Add highlights for matching terms
                result.highlights = self._get_highlights(prompt, search_query)
                matching_prompts.append(result)
        
        return matching_prompts
    
    def _matches_query(self, prompt: Dict[str, Any], query: SearchQuery) -> bool:
        """Check if a prompt matches the search query"""
        if not query.terms:
            return True
        
        # Evaluate each term
        term_results = []
        
        for term in query.terms:
            result = self._matches_term(prompt, term)
            term_results.append((term, result))
        
        # Apply operators
        return self._evaluate_terms(term_results, query.global_operator)
    
    def _matches_term(self, prompt: Dict[str, Any], term: SearchTerm) -> bool:
        """Check if a prompt matches a single search term"""
        # Get the text to search in based on the field
        search_text = self._get_search_text(prompt, term.field)
        
        if not search_text:
            return False
        
        # Apply case sensitivity
        if not term.is_regex:
            search_text = search_text.lower()
            search_value = term.value.lower()
        else:
            search_value = term.value
        
        # Perform the match
        try:
            if term.is_regex:
                # Regex search
                pattern = re.compile(search_value, re.IGNORECASE if not term.is_regex else 0)
                matches = bool(pattern.search(search_text))
            elif term.is_exact:
                # Exact match
                matches = search_value in search_text
            else:
                # Fuzzy match (contains)
                matches = search_value in search_text
        except re.error:
            # Invalid regex, fall back to literal search
            matches = term.value.lower() in search_text.lower()
        
        # Apply negation
        if term.is_negated:
            matches = not matches
        
        return matches
    
    def _get_search_text(self, prompt: Dict[str, Any], field: SearchField) -> str:
        """Get the text to search in for a specific field"""
        if field == SearchField.TITLE:
            return prompt.get('title', '')
        elif field == SearchField.CONTENT:
            return prompt.get('content', '')
        elif field == SearchField.TAGS:
            # Get tags for this prompt
            tags = self.db.get_prompt_tags(prompt['id'])
            return ' '.join(tag['name'] for tag in tags)
        elif field == SearchField.FOLDER:
            # Get folder name
            if prompt.get('folder_id'):
                folders = self.db.get_all_folders()
                folder = next((f for f in folders if f['id'] == prompt['folder_id']), None)
                return folder['name'] if folder else ''
            return ''
        elif field == SearchField.CREATED:
            return prompt.get('created_at', '')
        elif field == SearchField.UPDATED:
            return prompt.get('updated_at', '')
        elif field == SearchField.ALL:
            # Search in all text fields
            title = prompt.get('title', '')
            content = prompt.get('content', '')
            tags = self.db.get_prompt_tags(prompt['id'])
            tag_text = ' '.join(tag['name'] for tag in tags)
            return f"{title} {content} {tag_text}"
        
        return ''
    
    def _evaluate_terms(self, term_results: List[tuple], global_operator: SearchOperator) -> bool:
        """Evaluate term results with operators"""
        if not term_results:
            return True
        
        # Start with the first term
        result = term_results[0][1]
        
        # Apply operators
        for i in range(1, len(term_results)):
            term, term_result = term_results[i]
            
            # Use the term's operator if specified, otherwise use global operator
            operator = term.operator if term.operator else global_operator
            
            if operator == SearchOperator.AND:
                result = result and term_result
            elif operator == SearchOperator.OR:
                result = result or term_result
            elif operator == SearchOperator.NOT:
                result = result and not term_result
        
        return result
    
    def _prompt_to_search_result(self, prompt: Dict[str, Any]) -> SearchResult:
        """Convert a prompt dictionary to a SearchResult object"""
        # Get tags for this prompt
        tags = self.db.get_prompt_tags(prompt['id'])
        tag_text = ', '.join(tag['name'] for tag in tags)
        
        # Get folder name
        folder_name = ""
        if prompt.get('folder_id'):
            folders = self.db.get_all_folders()
            folder = next((f for f in folders if f['id'] == prompt['folder_id']), None)
            folder_name = folder['name'] if folder else ""
        
        return SearchResult(
            id=prompt['id'],
            title=prompt.get('title', ''),
            content=prompt.get('content', ''),
            tags=tag_text,
            folder_name=folder_name,
            created_at=prompt.get('created_at', ''),
            updated_at=prompt.get('updated_at', '')
        )
    
    def _get_highlights(self, prompt: Dict[str, Any], query: SearchQuery) -> List[str]:
        """Get highlight snippets for matching terms"""
        highlights = []
        
        for term in query.terms:
            if term.is_negated:
                continue  # Skip negated terms for highlights
            
            search_text = self._get_search_text(prompt, term.field)
            if not search_text:
                continue
            
            # Find matches and create highlights
            if term.is_regex:
                try:
                    pattern = re.compile(term.value, re.IGNORECASE)
                    matches = pattern.findall(search_text)
                    highlights.extend(matches[:3])  # Limit to 3 matches per term
                except re.error:
                    pass
            else:
                # Simple text search
                search_value = term.value.lower()
                search_lower = search_text.lower()
                
                if search_value in search_lower:
                    # Find the context around the match
                    start_idx = search_lower.find(search_value)
                    context_start = max(0, start_idx - 20)
                    context_end = min(len(search_text), start_idx + len(term.value) + 20)
                    
                    context = search_text[context_start:context_end]
                    if context_start > 0:
                        context = "..." + context
                    if context_end < len(search_text):
                        context = context + "..."
                    
                    highlights.append(context)
        
        return highlights[:5]  # Limit total highlights


# Search query examples and help text
SEARCH_EXAMPLES = [
    {
        "query": "machine learning",
        "description": "Simple text search - finds prompts containing 'machine learning'"
    },
    {
        "query": "title:\"API Documentation\"",
        "description": "Exact match in title field"
    },
    {
        "query": "content:/regex.*pattern/",
        "description": "Regex search in content field"
    },
    {
        "query": "tags:python AND content:tutorial",
        "description": "Boolean AND - prompts tagged 'python' AND containing 'tutorial'"
    },
    {
        "query": "title:guide OR tags:documentation",
        "description": "Boolean OR - prompts with 'guide' in title OR tagged 'documentation'"
    },
    {
        "query": "-tags:deprecated",
        "description": "Negation - exclude prompts tagged 'deprecated'"
    },
    {
        "query": "folder:\"AI Projects\" AND created:2024",
        "description": "Search in specific folder and date range"
    }
]

SEARCH_HELP_TEXT = """
Advanced Search Syntax:

BASIC SEARCH:
• Simple text: machine learning
• Quoted exact: "exact phrase"
• Regex pattern: /regex.*pattern/

FIELD SEARCH:
• title:keyword - Search in title only
• content:keyword - Search in content only
• tags:keyword - Search in tags only
• folder:keyword - Search in folder name
• created:keyword - Search in creation date
• updated:keyword - Search in update date

OPERATORS:
• AND - Both terms must match
• OR - Either term must match
• NOT - Term must not match
• -term - Negation (exclude term)

EXAMPLES:
• title:"API Guide" AND tags:python
• content:/function.*def/ OR tags:tutorial
• -tags:deprecated AND folder:active
• "machine learning" AND (tags:python OR tags:tensorflow)
"""