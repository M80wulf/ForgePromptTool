"""
Sharing and collaboration service for the Prompt Organizer
"""

import sqlite3
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from models.sharing_models import (
    SharedPrompt, Collaborator, ShareLink, CollaborationSession,
    PromptComment, PromptVersion, ShareActivity, ShareNotification,
    SharePermission, ShareStatus, ShareNotificationType,
    SharingConfig, ShareRequest, ShareInvitation, ShareFormat,
    ShareExport, CollaborationWorkspace
)


class SharingService:
    """Service for managing prompt sharing and collaboration"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.config = SharingConfig()
        self._init_sharing_tables()
    
    def _init_sharing_tables(self):
        """Initialize sharing-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Shared prompts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shared_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    share_token TEXT UNIQUE NOT NULL,
                    owner_id TEXT NOT NULL,
                    owner_name TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    description TEXT DEFAULT '',
                    is_public BOOLEAN DEFAULT 0,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Collaborators table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collaborators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    last_active TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
                    UNIQUE(prompt_id, user_id)
                )
            """)
            
            # Share links table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS share_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    permission TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    max_uses INTEGER,
                    current_uses INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    description TEXT DEFAULT '',
                    last_accessed TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Prompt comments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    parent_id INTEGER,
                    is_resolved BOOLEAN DEFAULT 0,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_id) REFERENCES prompt_comments (id) ON DELETE CASCADE
                )
            """)
            
            # Prompt versions table (for collaboration)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    change_summary TEXT DEFAULT '',
                    is_current BOOLEAN DEFAULT 0,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
                    UNIQUE(prompt_id, version_number)
                )
            """)
            
            # Share activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS share_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Share notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS share_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    prompt_id INTEGER,
                    sender_id TEXT,
                    sender_name TEXT,
                    created_at TEXT NOT NULL,
                    read_at TEXT,
                    is_read BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Share invitations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS share_invitations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    sender_id TEXT NOT NULL,
                    sender_name TEXT NOT NULL,
                    recipient_email TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    invitation_token TEXT UNIQUE NOT NULL,
                    message TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    accepted_at TEXT,
                    declined_at TEXT,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Collaboration workspaces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collaboration_workspaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    owner_id TEXT NOT NULL,
                    owner_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    prompt_ids TEXT DEFAULT '[]',
                    is_public BOOLEAN DEFAULT 0,
                    settings TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error initializing sharing tables: {e}")
        finally:
            conn.close()
    
    def generate_share_token(self) -> str:
        """Generate a unique share token"""
        return str(uuid.uuid4())
    
    def create_share_link(self, prompt_id: int, created_by: str, 
                         permission: SharePermission = SharePermission.READ,
                         expires_in_days: Optional[int] = None,
                         max_uses: Optional[int] = None,
                         description: str = "") -> ShareLink:
        """Create a shareable link for a prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            token = self.generate_share_token()
            created_at = datetime.now().isoformat()
            expires_at = None
            
            if expires_in_days:
                expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
            
            cursor.execute("""
                INSERT INTO share_links 
                (prompt_id, token, permission, created_by, created_at, expires_at, max_uses, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (prompt_id, token, permission.value, created_by, created_at, 
                  expires_at, max_uses, description))
            
            link_id = cursor.lastrowid
            conn.commit()
            
            # Log activity
            self._log_activity(prompt_id, created_by, created_by, "share_link_created", 
                             f"Created share link with {permission.value} permission")
            
            return ShareLink(
                id=link_id,
                prompt_id=prompt_id,
                token=token,
                permission=permission,
                created_by=created_by,
                created_at=created_at,
                expires_at=expires_at,
                max_uses=max_uses,
                current_uses=0,
                is_active=True,
                description=description
            )
            
        except sqlite3.Error as e:
            print(f"Error creating share link: {e}")
            return None
        finally:
            conn.close()
    
    def get_share_link(self, token: str) -> Optional[ShareLink]:
        """Get share link by token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM share_links WHERE token = ? AND is_active = 1
            """, (token,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Check if link has expired
            if row[7] and datetime.fromisoformat(row[7]) < datetime.now():
                return None
            
            # Check if max uses exceeded
            if row[8] and row[9] >= row[8]:
                return None
            
            return ShareLink(
                id=row[0],
                prompt_id=row[1],
                token=row[2],
                permission=SharePermission(row[3]),
                created_by=row[4],
                created_at=row[5],
                expires_at=row[6] if len(row) > 6 else None,
                max_uses=row[7] if len(row) > 7 else None,
                current_uses=row[8] if len(row) > 8 else 0,
                is_active=bool(row[9]) if len(row) > 9 else True,
                description=row[10] if len(row) > 10 else ""
            )
            
        except sqlite3.Error as e:
            print(f"Error getting share link: {e}")
            return None
        finally:
            conn.close()
    
    def access_shared_prompt(self, token: str, user_id: str = "anonymous") -> Optional[Dict[str, Any]]:
        """Access a shared prompt using a share token"""
        share_link = self.get_share_link(token)
        if not share_link:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get the prompt
            cursor.execute("SELECT * FROM prompts WHERE id = ?", (share_link.prompt_id,))
            prompt_row = cursor.fetchone()
            
            if not prompt_row:
                return None
            
            # Update access count
            cursor.execute("""
                UPDATE share_links 
                SET current_uses = current_uses + 1, last_accessed = ?
                WHERE token = ?
            """, (datetime.now().isoformat(), token))
            
            # Log access
            self._log_activity(share_link.prompt_id, user_id, user_id, "prompt_accessed",
                             f"Accessed shared prompt via link")
            
            conn.commit()
            
            return {
                'prompt': {
                    'id': prompt_row[0],
                    'title': prompt_row[1],
                    'content': prompt_row[2],
                    'created_at': prompt_row[5],
                    'updated_at': prompt_row[6]
                },
                'permission': share_link.permission,
                'share_info': {
                    'created_by': share_link.created_by,
                    'created_at': share_link.created_at,
                    'description': share_link.description
                }
            }
            
        except sqlite3.Error as e:
            print(f"Error accessing shared prompt: {e}")
            return None
        finally:
            conn.close()
    
    def add_collaborator(self, prompt_id: int, user_id: str, user_name: str, 
                        email: str, permission: SharePermission,
                        added_by: str) -> bool:
        """Add a collaborator to a prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            added_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO collaborators 
                (prompt_id, user_id, user_name, email, permission, added_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (prompt_id, user_id, user_name, email, permission.value, added_at))
            
            conn.commit()
            
            # Log activity
            self._log_activity(prompt_id, added_by, added_by, "collaborator_added",
                             f"Added {user_name} as collaborator with {permission.value} permission")
            
            # Create notification
            self._create_notification(
                user_id, ShareNotificationType.COLLABORATION_INVITE,
                "Collaboration Invitation",
                f"You've been invited to collaborate on a prompt with {permission.value} permission",
                prompt_id, added_by, added_by
            )
            
            return True
            
        except sqlite3.Error as e:
            print(f"Error adding collaborator: {e}")
            return False
        finally:
            conn.close()
    
    def get_collaborators(self, prompt_id: int) -> List[Collaborator]:
        """Get all collaborators for a prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM collaborators 
                WHERE prompt_id = ? AND is_active = 1
                ORDER BY added_at
            """, (prompt_id,))
            
            collaborators = []
            for row in cursor.fetchall():
                collaborators.append(Collaborator(
                    id=row[0],
                    user_id=row[2],
                    user_name=row[3],
                    email=row[4],
                    permission=SharePermission(row[5]),
                    added_at=row[6],
                    last_active=row[7],
                    is_active=bool(row[8])
                ))
            
            return collaborators
            
        except sqlite3.Error as e:
            print(f"Error getting collaborators: {e}")
            return []
        finally:
            conn.close()
    
    def add_comment(self, prompt_id: int, user_id: str, user_name: str,
                   content: str, parent_id: Optional[int] = None) -> Optional[PromptComment]:
        """Add a comment to a shared prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            created_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO prompt_comments 
                (prompt_id, user_id, user_name, content, created_at, parent_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (prompt_id, user_id, user_name, content, created_at, parent_id))
            
            comment_id = cursor.lastrowid
            conn.commit()
            
            # Log activity
            self._log_activity(prompt_id, user_id, user_name, "comment_added",
                             f"Added comment: {content[:50]}...")
            
            return PromptComment(
                id=comment_id,
                prompt_id=prompt_id,
                user_id=user_id,
                user_name=user_name,
                content=content,
                created_at=created_at,
                parent_id=parent_id
            )
            
        except sqlite3.Error as e:
            print(f"Error adding comment: {e}")
            return None
        finally:
            conn.close()
    
    def get_comments(self, prompt_id: int) -> List[PromptComment]:
        """Get all comments for a prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM prompt_comments 
                WHERE prompt_id = ?
                ORDER BY created_at
            """, (prompt_id,))
            
            comments = []
            for row in cursor.fetchall():
                comments.append(PromptComment(
                    id=row[0],
                    prompt_id=row[1],
                    user_id=row[2],
                    user_name=row[3],
                    content=row[4],
                    created_at=row[5],
                    updated_at=row[6],
                    parent_id=row[7],
                    is_resolved=bool(row[8])
                ))
            
            return comments
            
        except sqlite3.Error as e:
            print(f"Error getting comments: {e}")
            return []
        finally:
            conn.close()
    
    def create_prompt_version(self, prompt_id: int, title: str, content: str,
                            created_by: str, change_summary: str = "") -> Optional[PromptVersion]:
        """Create a new version of a prompt for collaboration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get next version number
            cursor.execute("""
                SELECT MAX(version_number) FROM prompt_versions WHERE prompt_id = ?
            """, (prompt_id,))
            
            max_version = cursor.fetchone()[0] or 0
            version_number = max_version + 1
            created_at = datetime.now().isoformat()
            
            # Mark all previous versions as not current
            cursor.execute("""
                UPDATE prompt_versions SET is_current = 0 WHERE prompt_id = ?
            """, (prompt_id,))
            
            # Insert new version
            cursor.execute("""
                INSERT INTO prompt_versions 
                (prompt_id, version_number, title, content, created_by, created_at, change_summary, is_current)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (prompt_id, version_number, title, content, created_by, created_at, change_summary))
            
            version_id = cursor.lastrowid
            conn.commit()
            
            # Log activity
            self._log_activity(prompt_id, created_by, created_by, "version_created",
                             f"Created version {version_number}: {change_summary}")
            
            return PromptVersion(
                id=version_id,
                prompt_id=prompt_id,
                version_number=version_number,
                title=title,
                content=content,
                created_by=created_by,
                created_at=created_at,
                change_summary=change_summary,
                is_current=True
            )
            
        except sqlite3.Error as e:
            print(f"Error creating prompt version: {e}")
            return None
        finally:
            conn.close()
    
    def get_prompt_versions(self, prompt_id: int) -> List[PromptVersion]:
        """Get all versions of a prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM prompt_versions 
                WHERE prompt_id = ?
                ORDER BY version_number DESC
            """, (prompt_id,))
            
            versions = []
            for row in cursor.fetchall():
                versions.append(PromptVersion(
                    id=row[0],
                    prompt_id=row[1],
                    version_number=row[2],
                    title=row[3],
                    content=row[4],
                    created_by=row[5],
                    created_at=row[6],
                    change_summary=row[7],
                    is_current=bool(row[8])
                ))
            
            return versions
            
        except sqlite3.Error as e:
            print(f"Error getting prompt versions: {e}")
            return []
        finally:
            conn.close()
    
    def get_share_activity(self, prompt_id: int, limit: int = 50) -> List[ShareActivity]:
        """Get activity log for a shared prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM share_activity 
                WHERE prompt_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (prompt_id, limit))
            
            activities = []
            for row in cursor.fetchall():
                metadata = None
                if row[7]:
                    try:
                        metadata = json.loads(row[7])
                    except json.JSONDecodeError:
                        pass
                
                activities.append(ShareActivity(
                    id=row[0],
                    prompt_id=row[1],
                    user_id=row[2],
                    user_name=row[3],
                    action=row[4],
                    details=row[5],
                    timestamp=row[6],
                    metadata=metadata
                ))
            
            return activities
            
        except sqlite3.Error as e:
            print(f"Error getting share activity: {e}")
            return []
        finally:
            conn.close()
    
    def _log_activity(self, prompt_id: int, user_id: str, user_name: str,
                     action: str, details: str, metadata: Optional[Dict[str, Any]] = None):
        """Log sharing activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            timestamp = datetime.now().isoformat()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO share_activity 
                (prompt_id, user_id, user_name, action, details, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (prompt_id, user_id, user_name, action, details, timestamp, metadata_json))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error logging activity: {e}")
        finally:
            conn.close()
    
    def _create_notification(self, user_id: str, notification_type: ShareNotificationType,
                           title: str, message: str, prompt_id: Optional[int] = None,
                           sender_id: Optional[str] = None, sender_name: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None):
        """Create a sharing notification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            created_at = datetime.now().isoformat()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO share_notifications 
                (user_id, type, title, message, prompt_id, sender_id, sender_name, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, notification_type.value, title, message, prompt_id, 
                  sender_id, sender_name, created_at, metadata_json))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error creating notification: {e}")
        finally:
            conn.close()
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[ShareNotification]:
        """Get notifications for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT * FROM share_notifications 
                WHERE user_id = ?
            """
            params = [user_id]
            
            if unread_only:
                query += " AND is_read = 0"
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            notifications = []
            for row in cursor.fetchall():
                metadata = None
                if row[11]:
                    try:
                        metadata = json.loads(row[11])
                    except json.JSONDecodeError:
                        pass
                
                notifications.append(ShareNotification(
                    id=row[0],
                    user_id=row[1],
                    type=ShareNotificationType(row[2]),
                    title=row[3],
                    message=row[4],
                    prompt_id=row[5],
                    sender_id=row[6],
                    sender_name=row[7],
                    created_at=row[8],
                    read_at=row[9],
                    is_read=bool(row[10]),
                    metadata=metadata
                ))
            
            return notifications
            
        except sqlite3.Error as e:
            print(f"Error getting notifications: {e}")
            return []
        finally:
            conn.close()
    
    def mark_notification_read(self, notification_id: int, user_id: str) -> bool:
        """Mark a notification as read"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            read_at = datetime.now().isoformat()
            
            cursor.execute("""
                UPDATE share_notifications 
                SET is_read = 1, read_at = ?
                WHERE id = ? AND user_id = ?
            """, (read_at, notification_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error marking notification as read: {e}")
            return False
        finally:
            conn.close()
    
    def revoke_share_link(self, token: str, user_id: str) -> bool:
        """Revoke a share link"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE share_links 
                SET is_active = 0
                WHERE token = ? AND created_by = ?
            """, (token, user_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                # Get prompt_id for logging
                cursor.execute("SELECT prompt_id FROM share_links WHERE token = ?", (token,))
                prompt_id = cursor.fetchone()[0]
                
                self._log_activity(prompt_id, user_id, user_id, "share_link_revoked",
                                 "Revoked share link")
                return True
            
            return False
            
        except sqlite3.Error as e:
            print(f"Error revoking share link: {e}")
            return False
        finally:
            conn.close()
    
    def get_shared_prompts_by_user(self, user_id: str) -> List[SharedPrompt]:
        """Get all prompts shared by a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT sl.*, p.title 
                FROM share_links sl
                JOIN prompts p ON sl.prompt_id = p.id
                WHERE sl.created_by = ? AND sl.is_active = 1
                ORDER BY sl.created_at DESC
            """, (user_id,))
            
            shared_prompts = []
            for row in cursor.fetchall():
                shared_prompts.append(SharedPrompt(
                    id=row[0],
                    prompt_id=row[1],
                    share_token=row[2],
                    owner_id=row[4],
                    owner_name=row[4],  # Using user_id as name for now
                    permission=SharePermission(row[3]),
                    status=ShareStatus.ACTIVE,
                    created_at=row[5],
                    expires_at=row[7],
                    access_count=row[9],
                    last_accessed=row[6],  # This might be wrong field order
                    description=row[11]
                ))
            
            return shared_prompts
            
        except sqlite3.Error as e:
            print(f"Error getting shared prompts: {e}")
            return []
        finally:
            conn.close()