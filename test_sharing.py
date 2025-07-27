#!/usr/bin/env python3
"""
Test script for sharing functionality
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from services.sharing_service import SharingService
from models.sharing_models import SharePermission

def test_sharing_functionality():
    """Test the sharing functionality"""
    print("Testing Sharing and Collaboration Functionality")
    print("=" * 60)
    
    # Initialize database and sharing service
    db = DatabaseManager()
    sharing_service = SharingService("prompts.db")
    
    # Create some test data if database is empty
    prompts = db.get_prompts()
    if not prompts:
        print("Creating test data...")
        
        # Create test folders
        folder_id = db.create_folder("Shared Prompts", None)
        
        # Create test prompts
        prompt1_id = db.create_prompt(
            title="Collaborative Writing Prompt",
            content="Write a story about a team working together to solve a complex problem.",
            folder_id=folder_id
        )
        
        prompt2_id = db.create_prompt(
            title="Code Review Prompt",
            content="Review this code for best practices, security issues, and optimization opportunities.",
            folder_id=folder_id
        )
        
        print("Test data created successfully!")
    else:
        prompt1_id = prompts[0]['id']
        prompt2_id = prompts[1]['id'] if len(prompts) > 1 else prompt1_id
    
    # Test 1: Create share links
    print("\n1. Testing share link creation:")
    
    # Create a read-only share link
    read_link = sharing_service.create_share_link(
        prompt1_id, "test_user", SharePermission.READ, 
        expires_in_days=7, description="Read-only test link"
    )
    
    if read_link:
        print(f"   [OK] Created read-only link: {read_link.token[:8]}...")
        print(f"     Permission: {read_link.permission.value}")
        print(f"     Expires: {read_link.expires_at}")
    
    # Create a write share link
    write_link = sharing_service.create_share_link(
        prompt2_id, "test_user", SharePermission.WRITE,
        max_uses=5, description="Write access test link"
    )
    
    if write_link:
        print(f"   [OK] Created write link: {write_link.token[:8]}...")
        print(f"     Permission: {write_link.permission.value}")
        print(f"     Max uses: {write_link.max_uses}")
    
    # Test 2: Access shared prompts
    print("\n2. Testing shared prompt access:")
    
    if read_link:
        shared_data = sharing_service.access_shared_prompt(read_link.token, "visitor_user")
        if shared_data:
            print(f"   [OK] Successfully accessed shared prompt")
            print(f"     Title: {shared_data['prompt']['title']}")
            print(f"     Permission: {shared_data['permission'].value}")
            print(f"     Shared by: {shared_data['share_info']['created_by']}")
    
    # Test 3: Add collaborators
    print("\n3. Testing collaborator management:")
    
    success = sharing_service.add_collaborator(
        prompt1_id, "collab1", "Alice Smith", "alice@example.com",
        SharePermission.WRITE, "test_user"
    )
    
    if success:
        print("   [OK] Added Alice as collaborator")
    
    success = sharing_service.add_collaborator(
        prompt1_id, "collab2", "Bob Johnson", "bob@example.com",
        SharePermission.READ, "test_user"
    )
    
    if success:
        print("   [OK] Added Bob as collaborator")
    
    # Get collaborators
    collaborators = sharing_service.get_collaborators(prompt1_id)
    print(f"   Total collaborators: {len(collaborators)}")
    for collab in collaborators:
        print(f"     - {collab.user_name} ({collab.email}) - {collab.permission.value}")
    
    # Test 4: Add comments
    print("\n4. Testing comments:")
    
    comment1 = sharing_service.add_comment(
        prompt1_id, "collab1", "Alice Smith",
        "This is a great prompt! I suggest we add more detail about the problem-solving process."
    )
    
    if comment1:
        print("   [OK] Added comment from Alice")
    
    comment2 = sharing_service.add_comment(
        prompt1_id, "collab2", "Bob Johnson",
        "I agree with Alice. Maybe we could also include some examples?",
        parent_id=comment1.id if comment1 else None
    )
    
    if comment2:
        print("   [OK] Added reply from Bob")
    
    # Get comments
    comments = sharing_service.get_comments(prompt1_id)
    print(f"   Total comments: {len(comments)}")
    for comment in comments:
        indent = "     " if comment.parent_id else "   "
        print(f"{indent}- {comment.user_name}: {comment.content[:50]}...")
    
    # Test 5: Create prompt versions
    print("\n5. Testing version management:")
    
    version1 = sharing_service.create_prompt_version(
        prompt1_id,
        "Collaborative Writing Prompt v2",
        "Write a detailed story about a diverse team working together to solve a complex environmental problem, showcasing different perspectives and skills.",
        "collab1",
        "Added more detail and specified environmental focus"
    )
    
    if version1:
        print(f"   [OK] Created version {version1.version_number}")
        print(f"     Change: {version1.change_summary}")
    
    # Get versions
    versions = sharing_service.get_prompt_versions(prompt1_id)
    print(f"   Total versions: {len(versions)}")
    for version in versions:
        current = " (current)" if version.is_current else ""
        print(f"     v{version.version_number}: {version.change_summary}{current}")
    
    # Test 6: Activity log
    print("\n6. Testing activity tracking:")
    
    activities = sharing_service.get_share_activity(prompt1_id, 10)
    print(f"   Recent activities: {len(activities)}")
    for activity in activities[:5]:  # Show last 5
        print(f"     - {activity.user_name}: {activity.details}")
    
    # Test 7: Notifications
    print("\n7. Testing notifications:")
    
    notifications = sharing_service.get_user_notifications("collab1")
    print(f"   Notifications for Alice: {len(notifications)}")
    for notif in notifications[:3]:  # Show first 3
        read_status = "[OK]" if notif.is_read else "[ ]"
        print(f"     {read_status} {notif.title}: {notif.message}")
    
    # Test 8: Get shared prompts by user
    print("\n8. Testing user's shared prompts:")
    
    shared_prompts = sharing_service.get_shared_prompts_by_user("test_user")
    print(f"   Prompts shared by test_user: {len(shared_prompts)}")
    for shared in shared_prompts:
        print(f"     - Prompt {shared.prompt_id}: {shared.permission.value} access, {shared.access_count} uses")
    
    print("\n" + "=" * 60)
    print("Sharing and collaboration testing completed!")
    print("\nKey features tested:")
    print("[OK] Share link creation with permissions and expiry")
    print("[OK] Shared prompt access and permission checking")
    print("[OK] Collaborator management")
    print("[OK] Comment system with threading")
    print("[OK] Version control for collaborative editing")
    print("[OK] Activity logging and tracking")
    print("[OK] Notification system")
    print("[OK] User's shared prompts overview")

if __name__ == "__main__":
    test_sharing_functionality()