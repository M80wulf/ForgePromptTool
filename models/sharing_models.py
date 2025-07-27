"""
Sharing and collaboration models for the Prompt Organizer
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SharePermission(Enum):
    """Permission levels for shared prompts"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class ShareStatus(Enum):
    """Status of shared prompts"""
    ACTIVE = "active"
    PENDING = "pending"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class SharedPrompt:
    """Shared prompt with collaboration metadata"""
    id: int
    prompt_id: int
    share_token: str
    owner_id: str
    owner_name: str
    permission: SharePermission
    status: ShareStatus
    created_at: str
    expires_at: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None
    description: str = ""
    is_public: bool = False


@dataclass
class Collaborator:
    """Collaborator information"""
    id: int
    user_id: str
    user_name: str
    email: str
    permission: SharePermission
    added_at: str
    last_active: Optional[str] = None
    is_active: bool = True


@dataclass
class ShareLink:
    """Share link for prompts"""
    id: int
    prompt_id: int
    token: str
    permission: SharePermission
    created_by: str
    created_at: str
    expires_at: Optional[str] = None
    max_uses: Optional[int] = None
    current_uses: int = 0
    is_active: bool = True
    description: str = ""


@dataclass
class CollaborationSession:
    """Real-time collaboration session"""
    id: int
    prompt_id: int
    session_token: str
    participants: List[Collaborator]
    created_at: str
    last_activity: str
    is_active: bool = True


@dataclass
class PromptComment:
    """Comment on a shared prompt"""
    id: int
    prompt_id: int
    user_id: str
    user_name: str
    content: str
    created_at: str
    updated_at: Optional[str] = None
    parent_id: Optional[int] = None  # For threaded comments
    is_resolved: bool = False


@dataclass
class PromptVersion:
    """Version of a shared prompt for collaboration"""
    id: int
    prompt_id: int
    version_number: int
    title: str
    content: str
    created_by: str
    created_at: str
    change_summary: str = ""
    is_current: bool = False


@dataclass
class ShareActivity:
    """Activity log for shared prompts"""
    id: int
    prompt_id: int
    user_id: str
    user_name: str
    action: str  # 'viewed', 'edited', 'commented', 'shared', etc.
    details: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ShareNotificationType(Enum):
    """Types of sharing notifications"""
    PROMPT_SHARED = "prompt_shared"
    PERMISSION_CHANGED = "permission_changed"
    COMMENT_ADDED = "comment_added"
    PROMPT_UPDATED = "prompt_updated"
    COLLABORATION_INVITE = "collaboration_invite"


@dataclass
class ShareNotification:
    """Notification for sharing events"""
    id: int
    user_id: str
    type: ShareNotificationType
    title: str
    message: str
    prompt_id: Optional[int] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    created_at: str = ""
    read_at: Optional[str] = None
    is_read: bool = False
    metadata: Optional[Dict[str, Any]] = None


# Sharing configuration and settings
@dataclass
class SharingConfig:
    """Configuration for sharing features"""
    enabled: bool = True
    allow_public_sharing: bool = True
    allow_anonymous_access: bool = False
    default_permission: SharePermission = SharePermission.READ
    max_collaborators: int = 10
    link_expiry_days: int = 30
    require_authentication: bool = False
    allow_comments: bool = True
    allow_version_history: bool = True
    notification_enabled: bool = True


# Share request and invitation models
@dataclass
class ShareRequest:
    """Request to share a prompt"""
    prompt_id: int
    recipient_email: str
    permission: SharePermission
    message: str = ""
    expires_in_days: Optional[int] = None
    allow_resharing: bool = False


@dataclass
class ShareInvitation:
    """Invitation to collaborate on a prompt"""
    id: int
    prompt_id: int
    sender_id: str
    sender_name: str
    recipient_email: str
    permission: SharePermission
    invitation_token: str
    message: str
    created_at: str
    expires_at: str
    accepted_at: Optional[str] = None
    declined_at: Optional[str] = None
    status: str = "pending"  # pending, accepted, declined, expired


# Export formats for sharing
class ShareFormat(Enum):
    """Formats for sharing prompts"""
    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"
    PDF = "pdf"
    HTML = "html"
    LINK = "link"


@dataclass
class ShareExport:
    """Export data for sharing"""
    prompt_id: int
    format: ShareFormat
    content: str
    metadata: Dict[str, Any]
    created_at: str
    expires_at: Optional[str] = None
    download_count: int = 0


# Collaboration workspace
@dataclass
class CollaborationWorkspace:
    """Workspace for collaborative prompt development"""
    id: int
    name: str
    description: str
    owner_id: str
    owner_name: str
    created_at: str
    updated_at: str
    prompt_ids: List[int]
    collaborators: List[Collaborator]
    is_public: bool = False
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}