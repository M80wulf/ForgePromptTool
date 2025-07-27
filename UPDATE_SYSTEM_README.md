# GitHub Update System Setup

The Prompt Organizer includes an automatic update system that checks GitHub for new releases and can download/install them automatically.

## 🚀 Quick Setup

### 1. Create Your GitHub Repository

1. Create a new repository on GitHub (or use an existing one)
2. Upload your Prompt Organizer code to the repository
3. Note your GitHub username and repository name

### 2. Configure the Update System

Edit `config/update_config.py` and update these values:

```python
# Replace with your actual details
GITHUB_REPO_OWNER = "your-github-username"
GITHUB_REPO_NAME = "your-repository-name"
CURRENT_VERSION = "1.0.0"  # Your current version
```

### 3. Create Releases on GitHub

1. Go to your repository on GitHub
2. Click **"Releases"** → **"Create a new release"**
3. Set the tag version (e.g., `v1.1.0`)
4. Add a title and description
5. Optionally attach a ZIP file of your code
6. Click **"Publish release"**

## 📋 How It Works

### For Users:
- **Manual Check**: Help → Check for Updates (Ctrl+U)
- **Automatic Check**: Can be enabled in config (checks on startup)
- **Safe Updates**: Creates backups before installing
- **One-Click Install**: Downloads, installs, and restarts automatically

### For Developers:
- **GitHub API**: Uses GitHub's releases API to check for updates
- **Version Comparison**: Uses semantic versioning to compare versions
- **Asset Download**: Downloads release assets or source code
- **Backup System**: Creates backups before applying updates
- **Restart Handling**: Automatically restarts the application after update

## 🔧 Configuration Options

In `config/update_config.py`:

```python
# Basic Configuration
GITHUB_REPO_OWNER = "your-username"
GITHUB_REPO_NAME = "prompt-organizer"
CURRENT_VERSION = "1.0.0"

# Update Behavior
AUTO_CHECK_ON_STARTUP = False    # Enable automatic checks
INCLUDE_PRERELEASES = False      # Include beta/pre-release versions
CHECK_INTERVAL_HOURS = 24        # How often to check (if auto-check enabled)
RELEASE_BRANCH = "main"          # Branch for stable releases
```

## 📦 Release Best Practices

### Version Numbering
Use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Notes
Include clear release notes:
```markdown
## What's New in v1.1.0

### ✨ New Features
- AI Prompt Generator
- Improved editor layout
- GitHub update system

### 🐛 Bug Fixes
- Fixed PyQt6 compatibility issues
- Improved error handling

### 🔧 Improvements
- Better performance
- Enhanced UI responsiveness
```

### Release Assets
You can attach files to releases:
- **Source Code**: Automatically included by GitHub
- **Compiled Binaries**: For different platforms
- **Documentation**: User guides, changelogs
- **Custom Packages**: ZIP files with specific configurations

## 🛡️ Security Features

### Safe Updates
- **Backup Creation**: Automatic backup before updates
- **Rollback Capability**: Can restore from backup if needed
- **Verification**: Checks download integrity
- **User Confirmation**: Always asks before installing

### Privacy
- **No Data Collection**: Only checks GitHub API for releases
- **Local Processing**: All updates handled locally
- **Optional**: Users can disable automatic checks

## 🔍 Troubleshooting

### Common Issues

**"No updates available" but you know there's a new release:**
- Check that `CURRENT_VERSION` is correct
- Verify repository owner/name in config
- Ensure release is published (not draft)

**Download fails:**
- Check internet connection
- Verify GitHub repository is public
- Check if release has downloadable assets

**Installation fails:**
- Ensure write permissions to application directory
- Check available disk space
- Try running as administrator (Windows)

### Debug Mode
Enable debug output by setting environment variable:
```bash
export PROMPT_ORGANIZER_DEBUG=1
```

## 🌟 Advanced Features

### Custom Update Branches
You can create different update channels:
```python
# In update_config.py
RELEASE_BRANCH = "stable"    # For stable releases
# RELEASE_BRANCH = "beta"    # For beta releases
```

### Pre-release Support
Enable pre-release versions:
```python
INCLUDE_PRERELEASES = True
```

### Automatic Updates
Enable startup checks:
```python
AUTO_CHECK_ON_STARTUP = True
CHECK_INTERVAL_HOURS = 6  # Check every 6 hours
```

## 📝 Example Workflow

### For Repository Owners:

1. **Develop Features**: Work on new features in development branch
2. **Test Thoroughly**: Ensure everything works correctly
3. **Update Version**: Increment version in `config/update_config.py`
4. **Create Release**: Use GitHub's release system
5. **Notify Users**: Users will be notified of updates automatically

### For Users:

1. **Check for Updates**: Help → Check for Updates
2. **Review Changes**: Read release notes in the dialog
3. **Download**: Click "Download Update"
4. **Install**: Click "Install & Restart"
5. **Enjoy**: New features are ready to use!

## 🤝 Contributing

If you want to contribute to the update system:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

The update system is part of the Prompt Organizer project and follows the same license terms.

---

**Need Help?** 
- Check the troubleshooting section above
- Create an issue on GitHub
- Review the configuration files for examples