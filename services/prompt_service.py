"""
Service layer for prompt management operations
"""

from typing import List, Dict, Optional
from models.database import DatabaseManager
from models.data_models import Prompt, Tag, SearchFilter


class PromptService:
    """Service class for prompt-related operations"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def search_prompts(self, search_filter: SearchFilter) -> List[Dict]:
        """Search prompts with advanced filtering"""
        return self.db.get_prompts(
            folder_id=search_filter.folder_id,
            search_term=search_filter.search_term,
            tag_ids=search_filter.tag_ids,
            is_favorite=search_filter.is_favorite,
            is_template=search_filter.is_template
        )
    
    def get_prompt_with_tags(self, prompt_id: int) -> Optional[Dict]:
        """Get a prompt with its associated tags"""
        prompt = self.db.get_prompt(prompt_id)
        if prompt:
            prompt['tags'] = self.db.get_prompt_tags(prompt_id)
        return prompt
    
    def create_prompt_from_template(self, template_id: int, title: str, 
                                  folder_id: Optional[int] = None) -> int:
        """Create a new prompt from a template"""
        template = self.db.get_prompt(template_id)
        if not template or not template['is_template']:
            raise ValueError("Invalid template ID")
        
        # Create new prompt from template
        prompt_id = self.db.create_prompt(
            title=title,
            content=template['content'],
            folder_id=folder_id,
            is_favorite=False,
            is_template=False
        )
        
        # Copy tags from template
        template_tags = self.db.get_prompt_tags(template_id)
        for tag in template_tags:
            self.db.add_tag_to_prompt(prompt_id, tag['id'])
        
        return prompt_id
    
    def get_templates(self) -> List[Dict]:
        """Get all template prompts"""
        return self.db.get_prompts(is_template=True)
    
    def get_favorites(self) -> List[Dict]:
        """Get all favorite prompts"""
        return self.db.get_prompts(is_favorite=True)
    
    def get_recent_prompts(self, limit: int = 10) -> List[Dict]:
        """Get recently updated prompts"""
        prompts = self.db.get_prompts()
        # Sort by updated_at and limit
        sorted_prompts = sorted(prompts, key=lambda x: x['updated_at'], reverse=True)
        return sorted_prompts[:limit]
    
    def get_prompt_statistics(self) -> Dict:
        """Get statistics about prompts"""
        all_prompts = self.db.get_prompts()
        templates = [p for p in all_prompts if p['is_template']]
        favorites = [p for p in all_prompts if p['is_favorite']]
        
        return {
            'total_prompts': len(all_prompts),
            'templates': len(templates),
            'favorites': len(favorites),
            'tags': len(self.db.get_tags()),
            'folders': len(self.db.get_all_folders())
        }
    
    def duplicate_prompt_with_modifications(self, prompt_id: int, 
                                          modifications: Dict) -> int:
        """Duplicate a prompt with specific modifications"""
        original = self.db.get_prompt(prompt_id)
        if not original:
            raise ValueError("Prompt not found")
        
        # Apply modifications
        title = modifications.get('title', f"{original['title']} (Copy)")
        content = modifications.get('content', original['content'])
        folder_id = modifications.get('folder_id', original['folder_id'])
        is_favorite = modifications.get('is_favorite', False)
        is_template = modifications.get('is_template', original['is_template'])
        
        # Create new prompt
        new_prompt_id = self.db.create_prompt(
            title=title,
            content=content,
            folder_id=folder_id,
            is_favorite=is_favorite,
            is_template=is_template
        )
        
        # Copy tags if not specified otherwise
        if modifications.get('copy_tags', True):
            original_tags = self.db.get_prompt_tags(prompt_id)
            for tag in original_tags:
                self.db.add_tag_to_prompt(new_prompt_id, tag['id'])
        
        return new_prompt_id
    
    def bulk_update_prompts(self, prompt_ids: List[int], updates: Dict) -> int:
        """Bulk update multiple prompts"""
        updated_count = 0
        
        for prompt_id in prompt_ids:
            try:
                if self.db.update_prompt(prompt_id, **updates):
                    updated_count += 1
            except Exception:
                continue  # Skip failed updates
        
        return updated_count
    
    def move_prompts_to_folder(self, prompt_ids: List[int], 
                              folder_id: Optional[int]) -> int:
        """Move multiple prompts to a folder"""
        return self.bulk_update_prompts(prompt_ids, {'folder_id': folder_id})
    
    def add_tag_to_multiple_prompts(self, prompt_ids: List[int], 
                                   tag_id: int) -> int:
        """Add a tag to multiple prompts"""
        added_count = 0
        
        for prompt_id in prompt_ids:
            if self.db.add_tag_to_prompt(prompt_id, tag_id):
                added_count += 1
        
        return added_count
    
    def remove_tag_from_multiple_prompts(self, prompt_ids: List[int], 
                                        tag_id: int) -> int:
        """Remove a tag from multiple prompts"""
        removed_count = 0
        
        for prompt_id in prompt_ids:
            if self.db.remove_tag_from_prompt(prompt_id, tag_id):
                removed_count += 1
        
        return removed_count
    
    def get_prompts_by_tag(self, tag_id: int) -> List[Dict]:
        """Get all prompts that have a specific tag"""
        return self.db.get_prompts(tag_ids=[tag_id])
    
    def get_orphaned_prompts(self) -> List[Dict]:
        """Get prompts that don't belong to any folder"""
        return self.db.get_prompts(folder_id=None)
    
    def get_untagged_prompts(self) -> List[Dict]:
        """Get prompts that don't have any tags"""
        all_prompts = self.db.get_prompts()
        untagged = []
        
        for prompt in all_prompts:
            tags = self.db.get_prompt_tags(prompt['id'])
            if not tags:
                untagged.append(prompt)
        
        return untagged