"""
Data models for the Prompt Organizer application
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Folder:
    """Represents a folder in the prompt organizer"""
    id: int
    name: str
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: List['Folder'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class Tag:
    """Represents a tag for categorizing prompts"""
    id: int
    name: str
    color: str = '#007bff'
    created_at: Optional[datetime] = None


@dataclass
class Prompt:
    """Represents a prompt in the organizer"""
    id: int
    title: str
    content: str
    folder_id: Optional[int] = None
    is_favorite: bool = False
    is_template: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[Tag] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class PromptVersion:
    """Represents a version of a prompt for history tracking"""
    id: int
    prompt_id: int
    content: str
    created_at: Optional[datetime] = None


@dataclass
class SearchFilter:
    """Represents search and filter criteria"""
    search_term: str = ""
    folder_id: Optional[int] = None
    tag_ids: List[int] = None
    is_favorite: Optional[bool] = None
    is_template: Optional[bool] = None
    
    def __post_init__(self):
        if self.tag_ids is None:
            self.tag_ids = []


@dataclass
class AppSettings:
    """Application settings"""
    window_geometry: Optional[str] = None
    splitter_state: Optional[str] = None
    font_family: str = "Consolas"
    font_size: int = 11
    theme: str = "light"
    auto_save: bool = True
    backup_enabled: bool = True
    backup_interval: int = 24  # hours
    recent_files: List[str] = None
    
    def __post_init__(self):
        if self.recent_files is None:
            self.recent_files = []