#!/usr/bin/env python3
"""
Community service for the Prompt Organizer application.
Handles prompt library sharing, discovery, and community features.
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class PromptVisibility(Enum):
    """Prompt visibility levels"""
    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"  # Public but not in discovery
    COMMUNITY = "community"  # Featured in community


class PromptCategory(Enum):
    """Community prompt categories"""
    WRITING = "writing"
    CODING = "coding"
    BUSINESS = "business"
    EDUCATION = "education"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    MARKETING = "marketing"
    RESEARCH = "research"
    PRODUCTIVITY = "productivity"
    OTHER = "other"


class PromptRating(Enum):
    """Prompt rating levels"""
    POOR = 1
    FAIR = 2
    GOOD = 3
    VERY_GOOD = 4
    EXCELLENT = 5


@dataclass
class CommunityPrompt:
    """Represents a prompt in the community library"""
    id: str
    title: str
    content: str
    description: str
    category: PromptCategory
    tags: List[str]
    author_id: str
    author_name: str
    visibility: PromptVisibility
    created_at: datetime
    updated_at: datetime
    download_count: int = 0
    rating_average: float = 0.0
    rating_count: int = 0
    is_featured: bool = False
    is_verified: bool = False
    version: str = "1.0"
    license: str = "CC BY 4.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['category'] = self.category.value
        data['visibility'] = self.visibility.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunityPrompt':
        """Create from dictionary"""
        data['category'] = PromptCategory(data['category'])
        data['visibility'] = PromptVisibility(data['visibility'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class PromptReview:
    """Represents a user review of a community prompt"""
    id: str
    prompt_id: str
    user_id: str
    user_name: str
    rating: PromptRating
    comment: str
    created_at: datetime
    helpful_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['rating'] = self.rating.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class UserProfile:
    """Represents a community user profile"""
    id: str
    username: str
    display_name: str
    email: str
    bio: str
    avatar_url: str
    created_at: datetime
    last_active: datetime
    prompts_shared: int = 0
    total_downloads: int = 0
    average_rating: float = 0.0
    is_verified: bool = False
    is_moderator: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_active'] = self.last_active.isoformat()
        return data


@dataclass
class SearchFilters:
    """Search and filter options for community prompts"""
    query: str = ""
    category: Optional[PromptCategory] = None
    tags: List[str] = None
    author_id: Optional[str] = None
    min_rating: float = 0.0
    featured_only: bool = False
    verified_only: bool = False
    sort_by: str = "created_at"  # created_at, updated_at, rating, downloads
    sort_order: str = "desc"  # asc, desc
    limit: int = 50
    offset: int = 0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class CommunityService:
    """Service for managing community prompt library"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.current_user_id = None
        self.current_user_name = "Anonymous"
        self._init_database()
    
    def _init_database(self):
        """Initialize community-related database tables"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Community prompts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS community_prompts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    visibility TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    download_count INTEGER DEFAULT 0,
                    rating_average REAL DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    is_featured BOOLEAN DEFAULT FALSE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    version TEXT DEFAULT '1.0',
                    license TEXT DEFAULT 'CC BY 4.0'
                )
            """)
            
            # Prompt reviews table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_reviews (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    helpful_count INTEGER DEFAULT 0,
                    FOREIGN KEY (prompt_id) REFERENCES community_prompts (id) ON DELETE CASCADE
                )
            """)
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    bio TEXT DEFAULT '',
                    avatar_url TEXT DEFAULT '',
                    created_at TIMESTAMP NOT NULL,
                    last_active TIMESTAMP NOT NULL,
                    prompts_shared INTEGER DEFAULT 0,
                    total_downloads INTEGER DEFAULT 0,
                    average_rating REAL DEFAULT 0.0,
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_moderator BOOLEAN DEFAULT FALSE
                )
            """)
            
            # User downloads table (track what users have downloaded)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    downloaded_at TIMESTAMP NOT NULL,
                    UNIQUE(user_id, prompt_id),
                    FOREIGN KEY (prompt_id) REFERENCES community_prompts (id) ON DELETE CASCADE
                )
            """)
            
            # User favorites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    favorited_at TIMESTAMP NOT NULL,
                    UNIQUE(user_id, prompt_id),
                    FOREIGN KEY (prompt_id) REFERENCES community_prompts (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    def set_current_user(self, user_id: str, user_name: str):
        """Set the current user for the session"""
        self.current_user_id = user_id
        self.current_user_name = user_name
    
    def create_user_profile(self, username: str, display_name: str, email: str, 
                           bio: str = "", avatar_url: str = "") -> str:
        """Create a new user profile"""
        import sqlite3
        
        user_id = str(uuid.uuid4())
        now = datetime.now()
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO user_profiles 
                    (id, username, display_name, email, bio, avatar_url, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username, display_name, email, bio, avatar_url, 
                      now.isoformat(), now.isoformat()))
                
                conn.commit()
                return user_id
                
            except sqlite3.IntegrityError:
                raise ValueError(f"Username '{username}' already exists")
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, email, bio, avatar_url,
                       created_at, last_active, prompts_shared, total_downloads,
                       average_rating, is_verified, is_moderator
                FROM user_profiles WHERE id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return UserProfile(
                    id=row[0],
                    username=row[1],
                    display_name=row[2],
                    email=row[3],
                    bio=row[4],
                    avatar_url=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    last_active=datetime.fromisoformat(row[7]),
                    prompts_shared=row[8],
                    total_downloads=row[9],
                    average_rating=row[10],
                    is_verified=bool(row[11]),
                    is_moderator=bool(row[12])
                )
            return None
    
    def share_prompt(self, local_prompt_id: int, title: str, description: str,
                    category: PromptCategory, tags: List[str], 
                    visibility: PromptVisibility = PromptVisibility.PUBLIC) -> str:
        """Share a local prompt to the community"""
        if not self.current_user_id:
            raise ValueError("User must be logged in to share prompts")
        
        # Get the local prompt
        local_prompt = self.db.get_prompt(local_prompt_id)
        if not local_prompt:
            raise ValueError("Local prompt not found")
        
        # Create community prompt
        prompt_id = str(uuid.uuid4())
        now = datetime.now()
        
        community_prompt = CommunityPrompt(
            id=prompt_id,
            title=title,
            content=local_prompt['content'],
            description=description,
            category=category,
            tags=tags,
            author_id=self.current_user_id,
            author_name=self.current_user_name,
            visibility=visibility,
            created_at=now,
            updated_at=now
        )
        
        # Store in database
        self._store_community_prompt(community_prompt)
        
        # Update user stats
        self._update_user_stats(self.current_user_id)
        
        return prompt_id
    
    def search_prompts(self, filters: SearchFilters) -> List[CommunityPrompt]:
        """Search community prompts with filters"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Build query
            query = """
                SELECT id, title, content, description, category, tags,
                       author_id, author_name, visibility, created_at, updated_at,
                       download_count, rating_average, rating_count,
                       is_featured, is_verified, version, license
                FROM community_prompts
                WHERE visibility IN ('public', 'community')
            """
            
            params = []
            
            # Add filters
            if filters.query:
                query += " AND (title LIKE ? OR description LIKE ? OR content LIKE ?)"
                search_term = f"%{filters.query}%"
                params.extend([search_term, search_term, search_term])
            
            if filters.category:
                query += " AND category = ?"
                params.append(filters.category.value)
            
            if filters.tags:
                for tag in filters.tags:
                    query += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            
            if filters.author_id:
                query += " AND author_id = ?"
                params.append(filters.author_id)
            
            if filters.min_rating > 0:
                query += " AND rating_average >= ?"
                params.append(filters.min_rating)
            
            if filters.featured_only:
                query += " AND is_featured = 1"
            
            if filters.verified_only:
                query += " AND is_verified = 1"
            
            # Add sorting
            sort_columns = {
                "created_at": "created_at",
                "updated_at": "updated_at",
                "rating": "rating_average",
                "downloads": "download_count",
                "title": "title"
            }
            
            sort_column = sort_columns.get(filters.sort_by, "created_at")
            sort_direction = "DESC" if filters.sort_order == "desc" else "ASC"
            query += f" ORDER BY {sort_column} {sort_direction}"
            
            # Add pagination
            query += " LIMIT ? OFFSET ?"
            params.extend([filters.limit, filters.offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            prompts = []
            for row in rows:
                prompt = CommunityPrompt(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    description=row[3],
                    category=PromptCategory(row[4]),
                    tags=json.loads(row[5]) if row[5] else [],
                    author_id=row[6],
                    author_name=row[7],
                    visibility=PromptVisibility(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10]),
                    download_count=row[11],
                    rating_average=row[12],
                    rating_count=row[13],
                    is_featured=bool(row[14]),
                    is_verified=bool(row[15]),
                    version=row[16],
                    license=row[17]
                )
                prompts.append(prompt)
            
            return prompts
    
    def get_community_prompt(self, prompt_id: str) -> Optional[CommunityPrompt]:
        """Get a specific community prompt"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, content, description, category, tags,
                       author_id, author_name, visibility, created_at, updated_at,
                       download_count, rating_average, rating_count,
                       is_featured, is_verified, version, license
                FROM community_prompts WHERE id = ?
            """, (prompt_id,))
            
            row = cursor.fetchone()
            if row:
                return CommunityPrompt(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    description=row[3],
                    category=PromptCategory(row[4]),
                    tags=json.loads(row[5]) if row[5] else [],
                    author_id=row[6],
                    author_name=row[7],
                    visibility=PromptVisibility(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10]),
                    download_count=row[11],
                    rating_average=row[12],
                    rating_count=row[13],
                    is_featured=bool(row[14]),
                    is_verified=bool(row[15]),
                    version=row[16],
                    license=row[17]
                )
            return None
    
    def download_prompt(self, prompt_id: str) -> Optional[int]:
        """Download a community prompt to local library"""
        if not self.current_user_id:
            raise ValueError("User must be logged in to download prompts")
        
        # Get community prompt
        community_prompt = self.get_community_prompt(prompt_id)
        if not community_prompt:
            raise ValueError("Community prompt not found")
        
        # Create local prompt
        local_prompt_id = self.db.create_prompt(
            title=f"[Community] {community_prompt.title}",
            content=community_prompt.content,
            folder_id=None,
            is_favorite=False,
            is_template=False
        )
        
        # Add tags if they exist locally
        for tag_name in community_prompt.tags:
            # Try to find existing tag or create new one
            tags = self.db.get_tags()
            existing_tag = next((t for t in tags if t['name'].lower() == tag_name.lower()), None)
            
            if existing_tag:
                tag_id = existing_tag['id']
            else:
                tag_id = self.db.create_tag(tag_name)
            
            self.db.add_tag_to_prompt(local_prompt_id, tag_id)
        
        # Record download
        self._record_download(prompt_id)
        
        return local_prompt_id
    
    def rate_prompt(self, prompt_id: str, rating: PromptRating, comment: str = "") -> str:
        """Rate and review a community prompt"""
        if not self.current_user_id:
            raise ValueError("User must be logged in to rate prompts")
        
        review_id = str(uuid.uuid4())
        now = datetime.now()
        
        review = PromptReview(
            id=review_id,
            prompt_id=prompt_id,
            user_id=self.current_user_id,
            user_name=self.current_user_name,
            rating=rating,
            comment=comment,
            created_at=now
        )
        
        # Store review
        self._store_review(review)
        
        # Update prompt rating
        self._update_prompt_rating(prompt_id)
        
        return review_id
    
    def get_prompt_reviews(self, prompt_id: str) -> List[PromptReview]:
        """Get reviews for a community prompt"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, prompt_id, user_id, user_name, rating, comment,
                       created_at, helpful_count
                FROM prompt_reviews WHERE prompt_id = ?
                ORDER BY created_at DESC
            """, (prompt_id,))
            
            reviews = []
            for row in cursor.fetchall():
                review = PromptReview(
                    id=row[0],
                    prompt_id=row[1],
                    user_id=row[2],
                    user_name=row[3],
                    rating=PromptRating(row[4]),
                    comment=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    helpful_count=row[7]
                )
                reviews.append(review)
            
            return reviews
    
    def get_featured_prompts(self, limit: int = 10) -> List[CommunityPrompt]:
        """Get featured community prompts"""
        filters = SearchFilters(
            featured_only=True,
            sort_by="rating",
            sort_order="desc",
            limit=limit
        )
        return self.search_prompts(filters)
    
    def get_trending_prompts(self, days: int = 7, limit: int = 10) -> List[CommunityPrompt]:
        """Get trending prompts based on recent downloads"""
        import sqlite3
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cp.id, cp.title, cp.content, cp.description, cp.category, cp.tags,
                       cp.author_id, cp.author_name, cp.visibility, cp.created_at, cp.updated_at,
                       cp.download_count, cp.rating_average, cp.rating_count,
                       cp.is_featured, cp.is_verified, cp.version, cp.license,
                       COUNT(ud.id) as recent_downloads
                FROM community_prompts cp
                LEFT JOIN user_downloads ud ON cp.id = ud.prompt_id 
                    AND ud.downloaded_at >= ?
                WHERE cp.visibility IN ('public', 'community')
                GROUP BY cp.id
                ORDER BY recent_downloads DESC, cp.rating_average DESC
                LIMIT ?
            """, (cutoff_date.isoformat(), limit))
            
            prompts = []
            for row in cursor.fetchall():
                prompt = CommunityPrompt(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    description=row[3],
                    category=PromptCategory(row[4]),
                    tags=json.loads(row[5]) if row[5] else [],
                    author_id=row[6],
                    author_name=row[7],
                    visibility=PromptVisibility(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10]),
                    download_count=row[11],
                    rating_average=row[12],
                    rating_count=row[13],
                    is_featured=bool(row[14]),
                    is_verified=bool(row[15]),
                    version=row[16],
                    license=row[17]
                )
                prompts.append(prompt)
            
            return prompts
    
    def get_user_prompts(self, user_id: str) -> List[CommunityPrompt]:
        """Get prompts shared by a specific user"""
        filters = SearchFilters(
            author_id=user_id,
            sort_by="created_at",
            sort_order="desc"
        )
        return self.search_prompts(filters)
    
    def get_user_favorites(self, user_id: str) -> List[CommunityPrompt]:
        """Get user's favorite community prompts"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cp.id, cp.title, cp.content, cp.description, cp.category, cp.tags,
                       cp.author_id, cp.author_name, cp.visibility, cp.created_at, cp.updated_at,
                       cp.download_count, cp.rating_average, cp.rating_count,
                       cp.is_featured, cp.is_verified, cp.version, cp.license
                FROM community_prompts cp
                JOIN user_favorites uf ON cp.id = uf.prompt_id
                WHERE uf.user_id = ?
                ORDER BY uf.favorited_at DESC
            """, (user_id,))
            
            prompts = []
            for row in cursor.fetchall():
                prompt = CommunityPrompt(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    description=row[3],
                    category=PromptCategory(row[4]),
                    tags=json.loads(row[5]) if row[5] else [],
                    author_id=row[6],
                    author_name=row[7],
                    visibility=PromptVisibility(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10]),
                    download_count=row[11],
                    rating_average=row[12],
                    rating_count=row[13],
                    is_featured=bool(row[14]),
                    is_verified=bool(row[15]),
                    version=row[16],
                    license=row[17]
                )
                prompts.append(prompt)
            
            return prompts
    
    def add_to_favorites(self, prompt_id: str) -> bool:
        """Add a prompt to user's favorites"""
        if not self.current_user_id:
            return False
        
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO user_favorites (user_id, prompt_id, favorited_at)
                    VALUES (?, ?, ?)
                """, (self.current_user_id, prompt_id, datetime.now().isoformat()))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Already favorited
    
    def remove_from_favorites(self, prompt_id: str) -> bool:
        """Remove a prompt from user's favorites"""
        if not self.current_user_id:
            return False
        
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_favorites 
                WHERE user_id = ? AND prompt_id = ?
            """, (self.current_user_id, prompt_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_community_stats(self) -> Dict[str, Any]:
        """Get community statistics"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total prompts
            cursor.execute("SELECT COUNT(*) FROM community_prompts WHERE visibility IN ('public', 'community')")
            stats['total_prompts'] = cursor.fetchone()[0]
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM user_profiles")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Total downloads
            cursor.execute("SELECT COUNT(*) FROM user_downloads")
            stats['total_downloads'] = cursor.fetchone()[0]
            
            # Total reviews
            cursor.execute("SELECT COUNT(*) FROM prompt_reviews")
            stats['total_reviews'] = cursor.fetchone()[0]
            
            # Average rating
            cursor.execute("SELECT AVG(rating_average) FROM community_prompts WHERE rating_count > 0")
            avg_rating = cursor.fetchone()[0]
            stats['average_rating'] = round(avg_rating, 2) if avg_rating else 0.0
            
            # Prompts by category
            cursor.execute("""
                SELECT category, COUNT(*) 
                FROM community_prompts 
                WHERE visibility IN ('public', 'community')
                GROUP BY category
            """)
            stats['by_category'] = dict(cursor.fetchall())
            
            # Top authors
            cursor.execute("""
                SELECT author_name, COUNT(*) as prompt_count
                FROM community_prompts 
                WHERE visibility IN ('public', 'community')
                GROUP BY author_id, author_name
                ORDER BY prompt_count DESC
                LIMIT 10
            """)
            stats['top_authors'] = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            return stats
    
    def _store_community_prompt(self, prompt: CommunityPrompt):
        """Store community prompt in database"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO community_prompts 
                (id, title, content, description, category, tags, author_id, author_name,
                 visibility, created_at, updated_at, download_count, rating_average,
                 rating_count, is_featured, is_verified, version, license)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt.id, prompt.title, prompt.content, prompt.description,
                prompt.category.value, json.dumps(prompt.tags), prompt.author_id,
                prompt.author_name, prompt.visibility.value,
                prompt.created_at.isoformat(), prompt.updated_at.isoformat(),
                prompt.download_count, prompt.rating_average, prompt.rating_count,
                prompt.is_featured, prompt.is_verified, prompt.version, prompt.license
            ))
            conn.commit()
    
    def _store_review(self, review: PromptReview):
        """Store review in database"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO prompt_reviews 
                (id, prompt_id, user_id, user_name, rating, comment, created_at, helpful_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review.id, review.prompt_id, review.user_id, review.user_name,
                review.rating.value, review.comment, review.created_at.isoformat(),
                review.helpful_count
            ))
            conn.commit()
    
    def _record_download(self, prompt_id: str):
        """Record a prompt download"""
        if not self.current_user_id:
            return
        
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Record download
            try:
                cursor.execute("""
                    INSERT INTO user_downloads (user_id, prompt_id, downloaded_at)
                    VALUES (?, ?, ?)
                """, (self.current_user_id, prompt_id, datetime.now().isoformat()))
            except sqlite3.IntegrityError:
                # Already downloaded, update timestamp
                cursor.execute("""
                    UPDATE user_downloads
                    SET downloaded_at = ?
                    WHERE user_id = ? AND prompt_id = ?
                """, (datetime.now().isoformat(), self.current_user_id, prompt_id))
            
            # Increment download count
            cursor.execute("""
                UPDATE community_prompts
                SET download_count = download_count + 1
                WHERE id = ?
            """, (prompt_id,))
            
            conn.commit()
    
    def _update_prompt_rating(self, prompt_id: str):
        """Update prompt rating average"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Calculate new average
            cursor.execute("""
                SELECT AVG(rating), COUNT(rating)
                FROM prompt_reviews
                WHERE prompt_id = ?
            """, (prompt_id,))
            
            result = cursor.fetchone()
            if result and result[0] is not None:
                avg_rating = float(result[0])
                rating_count = int(result[1])
                
                cursor.execute("""
                    UPDATE community_prompts
                    SET rating_average = ?, rating_count = ?
                    WHERE id = ?
                """, (avg_rating, rating_count, prompt_id))
                
                conn.commit()
    
    def _update_user_stats(self, user_id: str):
        """Update user statistics"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Count prompts shared
            cursor.execute("""
                SELECT COUNT(*) FROM community_prompts WHERE author_id = ?
            """, (user_id,))
            prompts_shared = cursor.fetchone()[0]
            
            # Calculate total downloads
            cursor.execute("""
                SELECT SUM(download_count) FROM community_prompts WHERE author_id = ?
            """, (user_id,))
            total_downloads = cursor.fetchone()[0] or 0
            
            # Calculate average rating
            cursor.execute("""
                SELECT AVG(rating_average) FROM community_prompts
                WHERE author_id = ? AND rating_count > 0
            """, (user_id,))
            avg_rating = cursor.fetchone()[0] or 0.0
            
            # Update user profile
            cursor.execute("""
                UPDATE user_profiles
                SET prompts_shared = ?, total_downloads = ?, average_rating = ?, last_active = ?
                WHERE id = ?
            """, (prompts_shared, total_downloads, avg_rating, datetime.now().isoformat(), user_id))
            
            conn.commit()
                