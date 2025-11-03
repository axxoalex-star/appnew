import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Database path
DB_PATH = Path(__file__).parent / "axxo_builder.db"

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=3)

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create status_checks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_checks (
                id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Create projects table for saving user projects
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                blocks TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                shared_menu TEXT
            )
        ''')
        
        # Create pages table for multiple pages per project
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                blocks TEXT NOT NULL,
                is_home INTEGER DEFAULT 0,
                page_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        
        # Create settings table for project settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL UNIQUE,
                site_name TEXT,
                site_description TEXT,
                site_logo TEXT,
                favicon TEXT,
                meta_title TEXT,
                meta_description TEXT,
                meta_keywords TEXT,
                og_title TEXT,
                og_description TEXT,
                og_image TEXT,
                google_analytics_id TEXT,
                facebook_pixel_id TEXT,
                custom_css TEXT,
                custom_js TEXT,
                header_scripts TEXT,
                footer_scripts TEXT,
                primary_font TEXT,
                primary_color TEXT,
                secondary_color TEXT,
                accent_color TEXT,
                border_radius TEXT,
                spacing TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def insert_status_check(self, client_name: str) -> Dict[str, Any]:
        """Insert a new status check"""
        def _insert():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            status_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            cursor.execute(
                'INSERT INTO status_checks (id, client_name, timestamp) VALUES (?, ?, ?)',
                (status_id, client_name, timestamp)
            )
            conn.commit()
            conn.close()
            
            return {
                'id': status_id,
                'client_name': client_name,
                'timestamp': timestamp
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _insert)
    
    async def get_status_checks(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all status checks"""
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM status_checks ORDER BY timestamp DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _get)
    
    async def save_project(self, project_id: str, name: str, blocks: List[Dict]) -> Dict[str, Any]:
        """Save a project"""
        def _save():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            blocks_json = json.dumps(blocks)
            
            # Check if project exists
            cursor.execute('SELECT id FROM projects WHERE id = ?', (project_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    'UPDATE projects SET name = ?, blocks = ?, updated_at = ? WHERE id = ?',
                    (name, blocks_json, now, project_id)
                )
            else:
                cursor.execute(
                    'INSERT INTO projects (id, name, blocks, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                    (project_id, name, blocks_json, now, now)
                )
            
            conn.commit()
            conn.close()
            
            return {
                'id': project_id,
                'name': name,
                'blocks': blocks,
                'updated_at': now
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _save)
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM projects ORDER BY updated_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            projects = []
            for row in rows:
                project = dict(row)
                project['blocks'] = json.loads(project['blocks'])
                projects.append(project)
            
            return projects
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _get)
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project"""
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                project = dict(row)
                project['blocks'] = json.loads(project['blocks'])
                return project
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _get)
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        def _delete():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return deleted
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _delete)

    # ============ PAGES METHODS ============
    
    async def create_page(self, project_id: str, name: str, blocks: List[Dict], is_home: bool = False) -> Dict[str, Any]:
        """Create a new page"""
        def _create():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            page_id = str(uuid.uuid4())
            blocks_json = json.dumps(blocks)
            now = datetime.utcnow().isoformat()
            
            # Get max order for this project
            cursor.execute('SELECT MAX(page_order) FROM pages WHERE project_id = ?', (project_id,))
            max_order = cursor.fetchone()[0]
            order = (max_order or 0) + 1
            
            # If this is home page, unset other home pages
            if is_home:
                cursor.execute('UPDATE pages SET is_home = 0 WHERE project_id = ?', (project_id,))
            
            cursor.execute(
                'INSERT INTO pages (id, project_id, name, blocks, is_home, page_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (page_id, project_id, name, blocks_json, 1 if is_home else 0, order, now, now)
            )
            conn.commit()
            conn.close()
            
            return {
                'id': page_id,
                'project_id': project_id,
                'name': name,
                'blocks': blocks,
                'is_home': is_home,
                'page_order': order,
                'created_at': now,
                'updated_at': now
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _create)
    
    async def get_pages(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all pages for a project"""
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM pages WHERE project_id = ? ORDER BY page_order ASC', (project_id,))
            rows = cursor.fetchall()
            conn.close()
            
            pages = []
            for row in rows:
                page = dict(row)
                page['blocks'] = json.loads(page['blocks'])
                page['is_home'] = bool(page['is_home'])
                pages.append(page)
            
            return pages
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _get)
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific page"""
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM pages WHERE id = ?', (page_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                page = dict(row)
                page['blocks'] = json.loads(page['blocks'])
                page['is_home'] = bool(page['is_home'])
                return page
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _get)
    
    async def update_page(self, page_id: str, name: str = None, blocks: List[Dict] = None, is_home: bool = None) -> Dict[str, Any]:
        """Update a page"""
        def _update():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get current page
            cursor.execute('SELECT * FROM pages WHERE id = ?', (page_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            current_page = dict(row)
            now = datetime.utcnow().isoformat()
            
            # Build update query
            updates = []
            params = []
            
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            
            if blocks is not None:
                updates.append('blocks = ?')
                params.append(json.dumps(blocks))
            
            if is_home is not None:
                # If setting as home, unset other home pages
                if is_home:
                    cursor.execute('UPDATE pages SET is_home = 0 WHERE project_id = ?', (current_page['project_id'],))
                updates.append('is_home = ?')
                params.append(1 if is_home else 0)
            
            updates.append('updated_at = ?')
            params.append(now)
            params.append(page_id)
            
            query = f'UPDATE pages SET {", ".join(updates)} WHERE id = ?'
            cursor.execute(query, params)
            conn.commit()
            
            # Get updated page
            cursor.execute('SELECT * FROM pages WHERE id = ?', (page_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                page = dict(row)
                page['blocks'] = json.loads(page['blocks'])
                page['is_home'] = bool(page['is_home'])
                return page
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _update)
    
    async def delete_page(self, page_id: str) -> bool:
        """Delete a page"""
        def _delete():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM pages WHERE id = ?', (page_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return deleted
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _delete)
    
    async def duplicate_page(self, page_id: str, new_name: str) -> Dict[str, Any]:
        """Duplicate a page"""
        def _duplicate():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get original page
            cursor.execute('SELECT * FROM pages WHERE id = ?', (page_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            original_page = dict(row)
            
            # Create new page
            new_page_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            # Get max order for this project
            cursor.execute('SELECT MAX(page_order) FROM pages WHERE project_id = ?', (original_page['project_id'],))
            max_order = cursor.fetchone()[0]
            order = (max_order or 0) + 1
            
            cursor.execute(
                'INSERT INTO pages (id, project_id, name, blocks, is_home, page_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (new_page_id, original_page['project_id'], new_name, original_page['blocks'], 0, order, now, now)
            )
            conn.commit()
            
            # Get new page
            cursor.execute('SELECT * FROM pages WHERE id = ?', (new_page_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                page = dict(row)
                page['blocks'] = json.loads(page['blocks'])
                page['is_home'] = bool(page['is_home'])
                return page
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _duplicate)
    
    async def update_shared_menu(self, project_id: str, shared_menu: Dict) -> bool:
        """Update shared menu for a project"""
        def _update():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            menu_json = json.dumps(shared_menu) if shared_menu else None
            now = datetime.utcnow().isoformat()
            
            cursor.execute(
                'UPDATE projects SET shared_menu = ?, updated_at = ? WHERE id = ?',
                (menu_json, now, project_id)
            )
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return updated
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _update)
    
    async def get_shared_menu(self, project_id: str) -> Optional[Dict]:
        """Get shared menu for a project"""
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT shared_menu FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row and row['shared_menu']:
                return json.loads(row['shared_menu'])
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _get)

    # ============ SETTINGS METHODS ============
    
    async def get_settings(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get settings for a project"""
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM settings WHERE project_id = ?', (project_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _get)
    
    async def save_settings(self, project_id: str, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update settings for a project"""
        def _save():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            
            # Check if settings exist
            cursor.execute('SELECT id FROM settings WHERE project_id = ?', (project_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing settings
                updates = []
                params = []
                
                for key, value in settings_data.items():
                    if key not in ['id', 'project_id', 'created_at']:
                        updates.append(f'{key} = ?')
                        params.append(value)
                
                updates.append('updated_at = ?')
                params.append(now)
                params.append(project_id)
                
                query = f'UPDATE settings SET {", ".join(updates)} WHERE project_id = ?'
                cursor.execute(query, params)
            else:
                # Create new settings
                settings_id = str(uuid.uuid4())
                
                columns = ['id', 'project_id', 'created_at', 'updated_at']
                values = [settings_id, project_id, now, now]
                placeholders = ['?', '?', '?', '?']
                
                for key, value in settings_data.items():
                    if key not in ['id', 'project_id', 'created_at', 'updated_at']:
                        columns.append(key)
                        values.append(value)
                        placeholders.append('?')
                
                query = f'INSERT INTO settings ({", ".join(columns)}) VALUES ({", ".join(placeholders)})'
                cursor.execute(query, values)
            
            conn.commit()
            
            # Get updated settings
            cursor.execute('SELECT * FROM settings WHERE project_id = ?', (project_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, _save)


# Global database instance
db = Database()
