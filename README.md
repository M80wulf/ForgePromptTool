# Prompt Organizer

A desktop application for organizing and managing prompts with advanced features like hierarchical folders, tagging, search, and future LLM integration.

## Features

### Core Features
- **Hierarchical Organization**: Organize prompts in folders and subfolders
- **Tag System**: Multi-tag support for flexible categorization
- **Advanced Search**: Full-text search with filtering by tags, favorites, and templates
- **Rich Text Editor**: Syntax highlighting for prompt formatting
- **Copy Without Saving**: Modify and copy prompts without affecting the saved version
- **Template System**: Create reusable prompt templates
- **Favorites**: Mark important prompts as favorites
- **Version History**: Track changes to prompts over time

### Import/Export
- **JSON Export**: Full data export with all metadata
- **Import Support**: Import prompts from JSON files
- **Backup System**: Automated backups with configurable intervals

### Future Features
- **LLM Integration**: Connect to local or cloud LLMs for:
  - Prompt rewriting and improvement
  - Automatic tag generation
  - Prompt explanation and analysis
  - Style and clarity improvements

## Installation

### Prerequisites
- Python 3.8 or higher
- PyQt6
- Pygments (for syntax highlighting)

### Setup
1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Getting Started
1. **Create Folders**: Use the left panel to create a folder structure
2. **Add Prompts**: Click "New" to create your first prompt
3. **Add Tags**: Create tags to categorize your prompts
4. **Search**: Use the search bar to find prompts quickly

### Key Features

#### Folder Management
- **Add Folder**: Right-click in the folder tree or use the "Add" button
- **Rename/Delete**: Right-click on folders for context menu options
- **Drag & Drop**: Move prompts between folders (planned feature)

#### Prompt Management
- **Create**: Click "New" or use Ctrl+N
- **Edit**: Select a prompt from the list to load it in the editor
- **Save**: Click "Save" or use Ctrl+S
- **Duplicate**: Right-click on prompts for duplication option
- **Delete**: Select and delete unwanted prompts

#### Tagging System
- **Create Tags**: Use the "Add Tag" button in the left panel
- **Color Coding**: Assign colors to tags for visual organization
- **Multi-tagging**: Add multiple tags to each prompt
- **Filter by Tags**: Click on tags to filter prompts

#### Search and Filtering
- **Text Search**: Search in prompt titles and content
- **Filter Options**: Show only favorites, templates, or specific folders
- **Tag Filtering**: Click tags to filter by category
- **Clear Filters**: Reset all filters with one click

#### Copy Features
- **Copy Original**: Copy the saved version of a prompt
- **Copy Modified**: Copy the current editor content without saving
- **Template Usage**: Create new prompts from templates

### Keyboard Shortcuts
- **Ctrl+N**: New prompt
- **Ctrl+S**: Save prompt
- **Ctrl+C**: Copy to clipboard
- **F5**: Refresh all data
- **Ctrl+Q**: Quit application

## File Structure

```
prompt_organizer/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── models/
│   ├── database.py        # Database operations
│   └── data_models.py     # Data structures
├── ui/
│   └── main_window.py     # Main window implementation
├── services/
│   ├── prompt_service.py  # Prompt management logic
│   └── llm_service.py     # LLM integration (future)
└── config/
    └── settings.py        # Configuration management
```

## Database

The application uses SQLite for local storage with the following structure:

- **folders**: Hierarchical folder organization
- **prompts**: Prompt content and metadata
- **tags**: Tag definitions with colors
- **prompt_tags**: Many-to-many relationship between prompts and tags
- **prompt_versions**: Version history for prompts

## Configuration

Settings are stored in:
- **Windows**: `%USERPROFILE%\.promptorganizer\config.json`
- **macOS/Linux**: `~/.promptorganizer/config.json`

### Configuration Options
- Auto-save settings
- UI preferences (font, theme)
- LLM integration settings
- Backup configuration

## LLM Integration (Future)

The application is designed to support multiple LLM providers:

### Supported Providers
- **Local LLMs**: Ollama, LocalAI, etc.
- **Cloud APIs**: OpenAI, Anthropic, etc.

### LLM Features
- **Prompt Rewriting**: Improve clarity and effectiveness
- **Auto-tagging**: Generate relevant tags automatically
- **Explanation**: Understand what prompts do
- **Suggestions**: Get improvement recommendations

### Configuration Example
```json
{
  "llm": {
    "enabled": true,
    "provider": "local",
    "local_base_url": "http://localhost:11434",
    "local_model": "llama2"
  }
}
```

## Development

### Architecture
The application follows a layered architecture:
- **UI Layer**: PyQt6 interface components
- **Service Layer**: Business logic and operations
- **Data Layer**: Database operations and models
- **Configuration**: Settings and preferences management

### Adding Features
1. **Database Changes**: Update `models/database.py` and migration scripts
2. **UI Components**: Add to `ui/` directory
3. **Business Logic**: Implement in `services/` directory
4. **Configuration**: Update `config/settings.py` if needed

### Testing
Run the application in development mode:
```bash
python main.py
```

## Troubleshooting

### Common Issues
1. **Database Errors**: Check file permissions and disk space
2. **UI Issues**: Ensure PyQt6 is properly installed
3. **Import Errors**: Verify all dependencies are installed

### Logs
Application logs are stored in the configuration directory.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. See LICENSE file for details.

## Roadmap

### Version 1.1
- [ ] Drag and drop support
- [ ] Advanced search operators
- [ ] Prompt templates with variables
- [ ] Export to multiple formats

### Version 1.2
- [ ] LLM integration
- [ ] Plugin system
- [ ] Collaborative features
- [ ] Cloud synchronization

### Version 2.0
- [ ] Web interface
- [ ] Mobile companion app
- [ ] Advanced analytics
- [ ] Team collaboration features