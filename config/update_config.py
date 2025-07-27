#!/usr/bin/env python3
"""
Configuration for the GitHub update system.
Update these values with your actual GitHub repository details.
"""

# GitHub Repository Configuration
# GitHub Repository Configuration
GITHUB_REPO_OWNER = "M80wulf"  # Your GitHub username
GITHUB_REPO_NAME = "ForgePromptTool"  # Your repository name

# Application Version
# Update this when you release new versions
CURRENT_VERSION = "1.0.0"

# Update Settings
AUTO_CHECK_ON_STARTUP = False  # Set to True to check for updates on startup
INCLUDE_PRERELEASES = False    # Set to True to include pre-release versions
CHECK_INTERVAL_HOURS = 24      # How often to check for updates (if auto-check enabled)

# Branch Configuration
# The branch that contains the latest stable releases
RELEASE_BRANCH = "main"

# Update Instructions for Users
UPDATE_INSTRUCTIONS = """
To set up automatic updates for your Prompt Organizer:

1. Create a GitHub repository for your project
2. Update the configuration in config/update_config.py:
   - Set GITHUB_REPO_OWNER to your GitHub username
   - Set GITHUB_REPO_NAME to your repository name
   - Update CURRENT_VERSION when you release new versions

3. Create releases on GitHub:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Tag version (e.g., "v1.1.0")
   - Add release notes
   - Attach a ZIP file of your code (optional)

4. The update system will:
   - Check for new releases using GitHub API
   - Download and install updates automatically
   - Backup your current version before updating
   - Restart the application after successful update

5. Users can check for updates via:
   - Help → Check for Updates (Ctrl+U)
   - Automatic checks on startup (if enabled)
"""

def get_repo_config():
    """Get repository configuration"""
    return {
        "owner": GITHUB_REPO_OWNER,
        "name": GITHUB_REPO_NAME,
        "current_version": CURRENT_VERSION,
        "auto_check": AUTO_CHECK_ON_STARTUP,
        "include_prereleases": INCLUDE_PRERELEASES,
        "check_interval": CHECK_INTERVAL_HOURS,
        "release_branch": RELEASE_BRANCH
    }

def get_update_instructions():
    """Get setup instructions for the update system"""
    return UPDATE_INSTRUCTIONS