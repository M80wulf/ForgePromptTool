#!/usr/bin/env python3
"""
Update service for checking GitHub releases and updating the application.
"""

import os
import sys
import json
import zipfile
import shutil
import subprocess
from typing import Dict, Optional, Tuple
from datetime import datetime
import requests
from packaging import version


class UpdateInfo:
    """Information about an available update"""
    
    def __init__(self, version_tag: str, release_name: str, description: str, 
                 download_url: str, published_at: str, is_prerelease: bool = False):
        self.version_tag = version_tag
        self.release_name = release_name
        self.description = description
        self.download_url = download_url
        self.published_at = published_at
        self.is_prerelease = is_prerelease
    
    @property
    def version_number(self) -> str:
        """Get clean version number (remove 'v' prefix if present)"""
        return self.version_tag.lstrip('v')


class GitHubUpdateService:
    """Service for checking and downloading updates from GitHub"""
    
    def __init__(self, repo_owner: str, repo_name: str, current_version: str = "1.0.0"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.api_base = "https://api.github.com"
        self.repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        
    def check_for_updates(self, include_prereleases: bool = False) -> Optional[UpdateInfo]:
        """Check if updates are available"""
        try:
            # Get latest release from GitHub API
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            if not releases:
                return None
            
            # Find the latest suitable release
            for release in releases:
                if release['draft']:
                    continue
                    
                if release['prerelease'] and not include_prereleases:
                    continue
                
                release_version = release['tag_name'].lstrip('v')
                
                # Compare versions
                if version.parse(release_version) > version.parse(self.current_version):
                    # Find download URL for the main asset
                    download_url = None
                    for asset in release.get('assets', []):
                        if asset['name'].endswith('.zip'):
                            download_url = asset['browser_download_url']
                            break
                    
                    # If no zip asset, use the source code zip
                    if not download_url:
                        download_url = release['zipball_url']
                    
                    return UpdateInfo(
                        version_tag=release['tag_name'],
                        release_name=release['name'] or release['tag_name'],
                        description=release['body'] or "No description available",
                        download_url=download_url,
                        published_at=release['published_at'],
                        is_prerelease=release['prerelease']
                    )
            
            return None
            
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None
    
    def download_update(self, update_info: UpdateInfo, download_path: str) -> bool:
        """Download the update to specified path"""
        try:
            response = requests.get(update_info.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"Error downloading update: {e}")
            return False
    
    def extract_update(self, zip_path: str, extract_to: str) -> bool:
        """Extract the downloaded update"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
            
        except Exception as e:
            print(f"Error extracting update: {e}")
            return False
    
    def apply_update(self, extracted_path: str, app_path: str, backup_path: str = None) -> bool:
        """Apply the update by replacing application files"""
        try:
            # Create backup if requested
            if backup_path:
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                shutil.copytree(app_path, backup_path)
            
            # Find the actual source folder in extracted content
            source_folder = extracted_path
            
            # If extracted folder contains a single subfolder, use that
            items = os.listdir(extracted_path)
            if len(items) == 1 and os.path.isdir(os.path.join(extracted_path, items[0])):
                source_folder = os.path.join(extracted_path, items[0])
            
            # Copy new files over existing ones
            for root, dirs, files in os.walk(source_folder):
                # Skip hidden directories and __pycache__
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                rel_path = os.path.relpath(root, source_folder)
                dest_dir = os.path.join(app_path, rel_path) if rel_path != '.' else app_path
                
                os.makedirs(dest_dir, exist_ok=True)
                
                for file in files:
                    # Skip certain files
                    if file.startswith('.') or file.endswith('.pyc'):
                        continue
                    
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    
                    shutil.copy2(src_file, dest_file)
            
            return True
            
        except Exception as e:
            print(f"Error applying update: {e}")
            return False
    
    def get_current_branch_info(self) -> Dict[str, str]:
        """Get information about the current branch (if in a git repository)"""
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode != 0:
                return {"error": "Not in a git repository"}
            
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            current_branch = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            # Get current commit hash
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            current_commit = result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
            
            # Get remote URL
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            remote_url = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            return {
                "branch": current_branch,
                "commit": current_commit,
                "remote": remote_url,
                "is_git_repo": True
            }
            
        except Exception as e:
            return {"error": str(e), "is_git_repo": False}
    
    def restart_application(self):
        """Restart the application after update"""
        try:
            # Get the current script path
            script_path = sys.argv[0]
            
            # Start new instance
            if sys.platform.startswith('win'):
                subprocess.Popen([sys.executable, script_path])
            else:
                subprocess.Popen([sys.executable, script_path])
            
            # Exit current instance
            sys.exit(0)
            
        except Exception as e:
            print(f"Error restarting application: {e}")


class UpdateManager:
    """High-level update manager"""
    
    def __init__(self, repo_owner: str, repo_name: str, current_version: str = "1.0.0"):
        self.update_service = GitHubUpdateService(repo_owner, repo_name, current_version)
        self.temp_dir = os.path.join(os.path.expanduser("~"), ".prompt_organizer_updates")
        
    def check_and_notify_updates(self, include_prereleases: bool = False) -> Optional[UpdateInfo]:
        """Check for updates and return update info if available"""
        return self.update_service.check_for_updates(include_prereleases)
    
    def download_and_prepare_update(self, update_info: UpdateInfo) -> Tuple[bool, str]:
        """Download and prepare update for installation"""
        try:
            # Create temp directory
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # Download update
            zip_path = os.path.join(self.temp_dir, f"update_{update_info.version_tag}.zip")
            
            if not self.update_service.download_update(update_info, zip_path):
                return False, "Failed to download update"
            
            # Extract update
            extract_path = os.path.join(self.temp_dir, f"extracted_{update_info.version_tag}")
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)
            
            if not self.update_service.extract_update(zip_path, extract_path):
                return False, "Failed to extract update"
            
            return True, extract_path
            
        except Exception as e:
            return False, f"Error preparing update: {str(e)}"
    
    def install_update(self, extract_path: str, create_backup: bool = True) -> Tuple[bool, str]:
        """Install the prepared update"""
        try:
            app_path = os.path.dirname(os.path.abspath(__file__))
            app_path = os.path.dirname(app_path)  # Go up one level from services/
            
            backup_path = None
            if create_backup:
                backup_path = os.path.join(self.temp_dir, "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            if self.update_service.apply_update(extract_path, app_path, backup_path):
                return True, "Update installed successfully"
            else:
                return False, "Failed to apply update"
                
        except Exception as e:
            return False, f"Error installing update: {str(e)}"
    
    def cleanup_temp_files(self):
        """Clean up temporary update files"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
    
    def get_version_info(self) -> Dict[str, str]:
        """Get current version and git information"""
        git_info = self.update_service.get_current_branch_info()
        
        return {
            "current_version": self.update_service.current_version,
            "repo_url": self.update_service.repo_url,
            **git_info
        }


# Example usage and configuration
if __name__ == "__main__":
    # Example configuration - replace with your actual GitHub repo
    REPO_OWNER = "your-username"  # Replace with your GitHub username
    REPO_NAME = "prompt-organizer"  # Replace with your repository name
    CURRENT_VERSION = "1.0.0"  # Replace with your current version
    
    # Create update manager
    update_manager = UpdateManager(REPO_OWNER, REPO_NAME, CURRENT_VERSION)
    
    # Check for updates
    print("Checking for updates...")
    update_info = update_manager.check_and_notify_updates()
    
    if update_info:
        print(f"Update available: {update_info.version_tag}")
        print(f"Release: {update_info.release_name}")
        print(f"Description: {update_info.description[:100]}...")
        
        # Download and prepare update
        success, result = update_manager.download_and_prepare_update(update_info)
        if success:
            print(f"Update prepared at: {result}")
        else:
            print(f"Failed to prepare update: {result}")
    else:
        print("No updates available")
    
    # Show version info
    version_info = update_manager.get_version_info()
    print(f"\nVersion info: {version_info}")