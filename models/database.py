"""
Database management for the Prompt Organizer application
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json


class DatabaseManager:
    """Manages SQLite database operations for the application"""
    
    def __init__(self, db_path: str = "prompts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create folders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES folders (id)
                )
            ''')
            
            # Create prompts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    folder_id INTEGER,
                    is_favorite BOOLEAN DEFAULT FALSE,
                    is_template BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders (id)
                )
            ''')
            
            # Create tags table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#007bff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create prompt_tags junction table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompt_tags (
                    prompt_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (prompt_id, tag_id),
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                )
            ''')
            
            # Create prompt_versions table for version history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            ''')
            
            # Create template tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT 'General',
                    tags TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS template_variables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    default_value TEXT DEFAULT '',
                    variable_type TEXT DEFAULT 'text',
                    choices TEXT DEFAULT '',
                    required BOOLEAN DEFAULT TRUE,
                    validation_pattern TEXT DEFAULT '',
                    FOREIGN KEY (template_id) REFERENCES prompt_templates (id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS template_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id INTEGER,
                    substitutions TEXT DEFAULT '{}',
                    generated_prompt_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES prompt_templates (id) ON DELETE CASCADE,
                    FOREIGN KEY (generated_prompt_id) REFERENCES prompts (id) ON DELETE SET NULL
                )
            ''')
            
            conn.commit()
            
            # Create default root folder if it doesn't exist
            cursor.execute('SELECT COUNT(*) FROM folders WHERE parent_id IS NULL')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO folders (name, parent_id) VALUES (?, ?)', ('Root', None))
                conn.commit()
    
    # Folder operations
    def create_folder(self, name: str, parent_id: Optional[int] = None) -> int:
        """Create a new folder"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO folders (name, parent_id) VALUES (?, ?)',
                (name, parent_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_folders(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get folders by parent ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, name, parent_id, created_at, updated_at FROM folders WHERE parent_id = ?',
                (parent_id,)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_folders(self) -> List[Dict]:
        """Get all folders"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, parent_id, created_at, updated_at FROM folders ORDER BY name')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_folder(self, folder_id: int, name: str) -> bool:
        """Update folder name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE folders SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (name, folder_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_folder(self, folder_id: int) -> bool:
        """Delete a folder and move its contents to parent"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get folder info
            cursor.execute('SELECT parent_id FROM folders WHERE id = ?', (folder_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            parent_id = result[0]
            
            # Move child folders to parent
            cursor.execute(
                'UPDATE folders SET parent_id = ? WHERE parent_id = ?',
                (parent_id, folder_id)
            )
            
            # Move prompts to parent folder
            cursor.execute(
                'UPDATE prompts SET folder_id = ? WHERE folder_id = ?',
                (parent_id, folder_id)
            )
            
            # Delete the folder
            cursor.execute('DELETE FROM folders WHERE id = ?', (folder_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Prompt operations
    def create_prompt(self, title: str, content: str, folder_id: Optional[int] = None,
                     is_favorite: bool = False, is_template: bool = False) -> int:
        """Create a new prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO prompts (title, content, folder_id, is_favorite, is_template)
                   VALUES (?, ?, ?, ?, ?)''',
                (title, content, folder_id, is_favorite, is_template)
            )
            prompt_id = cursor.lastrowid
            
            # Create initial version
            cursor.execute(
                'INSERT INTO prompt_versions (prompt_id, content) VALUES (?, ?)',
                (prompt_id, content)
            )
            
            conn.commit()
            return prompt_id
    
    def get_prompts(self, folder_id: Optional[int] = None, search_term: str = "",
                   tag_ids: List[int] = None, is_favorite: Optional[bool] = None,
                   is_template: Optional[bool] = None) -> List[Dict]:
        """Get prompts with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT DISTINCT p.id, p.title, p.content, p.folder_id, p.is_favorite, 
                       p.is_template, p.created_at, p.updated_at
                FROM prompts p
            '''
            
            conditions = []
            params = []
            
            if tag_ids:
                query += ' JOIN prompt_tags pt ON p.id = pt.prompt_id'
                conditions.append(f'pt.tag_id IN ({",".join("?" * len(tag_ids))})')
                params.extend(tag_ids)
            
            if folder_id is not None:
                conditions.append('p.folder_id = ?')
                params.append(folder_id)
            
            if search_term:
                conditions.append('(p.title LIKE ? OR p.content LIKE ?)')
                params.extend([f'%{search_term}%', f'%{search_term}%'])
            
            if is_favorite is not None:
                conditions.append('p.is_favorite = ?')
                params.append(is_favorite)
            
            if is_template is not None:
                conditions.append('p.is_template = ?')
                params.append(is_template)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY p.updated_at DESC'
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_prompt(self, prompt_id: int) -> Optional[Dict]:
        """Get a single prompt by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, title, content, folder_id, is_favorite, is_template, created_at, updated_at FROM prompts WHERE id = ?',
                (prompt_id,)
            )
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
    
    def update_prompt(self, prompt_id: int, title: str = None, content: str = None,
                     folder_id: int = None, is_favorite: bool = None,
                     is_template: bool = None) -> bool:
        """Update a prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current prompt for version history
            current_prompt = self.get_prompt(prompt_id)
            if not current_prompt:
                return False
            
            updates = []
            params = []
            
            if title is not None:
                updates.append('title = ?')
                params.append(title)
            
            if content is not None:
                updates.append('content = ?')
                params.append(content)
                
                # Create version if content changed
                if content != current_prompt['content']:
                    cursor.execute(
                        'INSERT INTO prompt_versions (prompt_id, content) VALUES (?, ?)',
                        (prompt_id, content)
                    )
            
            if folder_id is not None:
                updates.append('folder_id = ?')
                params.append(folder_id)
            
            if is_favorite is not None:
                updates.append('is_favorite = ?')
                params.append(is_favorite)
            
            if is_template is not None:
                updates.append('is_template = ?')
                params.append(is_template)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(prompt_id)
                
                query = f'UPDATE prompts SET {", ".join(updates)} WHERE id = ?'
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete a prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Tag operations
    def create_tag(self, name: str, color: str = '#007bff') -> int:
        """Create a new tag"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (name, color))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Tag already exists
                cursor.execute('SELECT id FROM tags WHERE name = ?', (name,))
                return cursor.fetchone()[0]
    
    def get_tags(self) -> List[Dict]:
        """Get all tags"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, color, created_at FROM tags ORDER BY name')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_prompt_tags(self, prompt_id: int) -> List[Dict]:
        """Get tags for a specific prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.name, t.color, t.created_at
                FROM tags t
                JOIN prompt_tags pt ON t.id = pt.tag_id
                WHERE pt.prompt_id = ?
                ORDER BY t.name
            ''', (prompt_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_tag_to_prompt(self, prompt_id: int, tag_id: int) -> bool:
        """Add a tag to a prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if prompt exists
            cursor.execute('SELECT id FROM prompts WHERE id = ?', (prompt_id,))
            if not cursor.fetchone():
                return False
            
            # Check if tag exists
            cursor.execute('SELECT id FROM tags WHERE id = ?', (tag_id,))
            if not cursor.fetchone():
                return False
            
            try:
                cursor.execute('INSERT INTO prompt_tags (prompt_id, tag_id) VALUES (?, ?)', (prompt_id, tag_id))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Already exists
    
    def remove_tag_from_prompt(self, prompt_id: int, tag_id: int) -> bool:
        """Remove a tag from a prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM prompt_tags WHERE prompt_id = ? AND tag_id = ?', (prompt_id, tag_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Version history
    def get_prompt_versions(self, prompt_id: int) -> List[Dict]:
        """Get version history for a prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, content, created_at FROM prompt_versions WHERE prompt_id = ? ORDER BY created_at DESC',
                (prompt_id,)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Backup and export
    def export_data(self) -> Dict:
        """Export all data as JSON"""
        data = {
            'folders': self.get_all_folders(),
            'prompts': self.get_prompts(),
            'tags': self.get_tags(),
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Add prompt_tags relationships
        prompt_tags = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT prompt_id, tag_id FROM prompt_tags')
            for row in cursor.fetchall():
                prompt_tags.append({'prompt_id': row[0], 'tag_id': row[1]})
        
        data['prompt_tags'] = prompt_tags
        
        # Add tags for each prompt for convenience
        for prompt in data['prompts']:
            prompt['tags'] = self.get_prompt_tags(prompt['id'])
        
        return data
    
    def import_data(self, data: Dict) -> bool:
        """Import data from JSON"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing data (optional - you might want to merge instead)
                # cursor.execute('DELETE FROM prompt_tags')
                # cursor.execute('DELETE FROM prompt_versions')
                # cursor.execute('DELETE FROM prompts')
                # cursor.execute('DELETE FROM tags')
                # cursor.execute('DELETE FROM folders WHERE parent_id IS NOT NULL')
                
                # Import folders
                folder_id_map = {}
                for folder in data.get('folders', []):
                    if folder['parent_id'] is None:
                        continue  # Skip root folder
                    
                    cursor.execute(
                        'INSERT INTO folders (name, parent_id) VALUES (?, ?)',
                        (folder['name'], folder_id_map.get(folder['parent_id']))
                    )
                    folder_id_map[folder['id']] = cursor.lastrowid
                
                # Import tags
                tag_id_map = {}
                for tag in data.get('tags', []):
                    tag_id = self.create_tag(tag['name'], tag['color'])
                    tag_id_map[tag['id']] = tag_id
                
                # Import prompts
                for prompt in data.get('prompts', []):
                    folder_id = folder_id_map.get(prompt['folder_id'])
                    prompt_id = self.create_prompt(
                        prompt['title'],
                        prompt['content'],
                        folder_id,
                        prompt['is_favorite'],
                        prompt['is_template']
                    )
                    
                    # Add tags
                    for tag in prompt.get('tags', []):
                        if tag['id'] in tag_id_map:
                            self.add_tag_to_prompt(prompt_id, tag_id_map[tag['id']])
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Import error: {e}")
            return False
    
    # Template operations
    def create_template(self, title: str, content: str, description: str = "",
                       category: str = "General", tags: str = "") -> int:
        """Create a new prompt template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO prompt_templates (title, content, description, category, tags)
                   VALUES (?, ?, ?, ?, ?)''',
                (title, content, description, category, tags)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_templates(self, category: str = None, search_term: str = "") -> List[Dict]:
        """Get templates with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT id, title, content, description, category, tags,
                       created_at, updated_at, usage_count
                FROM prompt_templates
            '''
            
            conditions = []
            params = []
            
            if category:
                conditions.append('category = ?')
                params.append(category)
            
            if search_term:
                conditions.append('(title LIKE ? OR description LIKE ? OR content LIKE ?)')
                params.extend([f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY usage_count DESC, updated_at DESC'
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Get a single template by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT id, title, content, description, category, tags,
                          created_at, updated_at, usage_count
                   FROM prompt_templates WHERE id = ?''',
                (template_id,)
            )
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
    
    def update_template(self, template_id: int, title: str = None, content: str = None,
                       description: str = None, category: str = None, tags: str = None) -> bool:
        """Update a template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if title is not None:
                updates.append('title = ?')
                params.append(title)
            
            if content is not None:
                updates.append('content = ?')
                params.append(content)
            
            if description is not None:
                updates.append('description = ?')
                params.append(description)
            
            if category is not None:
                updates.append('category = ?')
                params.append(category)
            
            if tags is not None:
                updates.append('tags = ?')
                params.append(tags)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(template_id)
                
                query = f'UPDATE prompt_templates SET {", ".join(updates)} WHERE id = ?'
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM prompt_templates WHERE id = ?', (template_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_template_usage(self, template_id: int) -> bool:
        """Increment template usage count"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE prompt_templates SET usage_count = usage_count + 1 WHERE id = ?',
                (template_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # Template variable operations
    def create_template_variable(self, template_id: int, name: str, description: str = "",
                                default_value: str = "", variable_type: str = "text",
                                choices: str = "", required: bool = True,
                                validation_pattern: str = "") -> int:
        """Create a template variable"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO template_variables
                   (template_id, name, description, default_value, variable_type,
                    choices, required, validation_pattern)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (template_id, name, description, default_value, variable_type,
                 choices, required, validation_pattern)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_template_variables(self, template_id: int) -> List[Dict]:
        """Get variables for a template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT id, template_id, name, description, default_value,
                          variable_type, choices, required, validation_pattern
                   FROM template_variables WHERE template_id = ?
                   ORDER BY name''',
                (template_id,)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_template_variable(self, variable_id: int, **kwargs) -> bool:
        """Update a template variable"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            valid_fields = ['name', 'description', 'default_value', 'variable_type',
                           'choices', 'required', 'validation_pattern']
            
            updates = []
            params = []
            
            for field, value in kwargs.items():
                if field in valid_fields and value is not None:
                    updates.append(f'{field} = ?')
                    params.append(value)
            
            if updates:
                params.append(variable_id)
                query = f'UPDATE template_variables SET {", ".join(updates)} WHERE id = ?'
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    def delete_template_variable(self, variable_id: int) -> bool:
        """Delete a template variable"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM template_variables WHERE id = ?', (variable_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_template_variables(self, template_id: int) -> bool:
        """Delete all variables for a template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM template_variables WHERE template_id = ?', (template_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Template usage operations
    def create_template_usage(self, template_id: int, substitutions: str,
                             generated_prompt_id: int = None) -> int:
        """Record template usage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO template_usage (template_id, substitutions, generated_prompt_id)
                   VALUES (?, ?, ?)''',
                (template_id, substitutions, generated_prompt_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_template_usage_history(self, template_id: int) -> List[Dict]:
        """Get usage history for a template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT id, template_id, substitutions, generated_prompt_id, created_at
                   FROM template_usage WHERE template_id = ?
                   ORDER BY created_at DESC''',
                (template_id,)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_template_categories(self) -> List[str]:
        """Get all unique template categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM prompt_templates ORDER BY category')
            return [row[0] for row in cursor.fetchall()]
    
    def close(self):
        """Close database connections (for cleanup)"""
        # SQLite connections are automatically closed when using context managers
        # This method is provided for compatibility with cleanup routines
        pass