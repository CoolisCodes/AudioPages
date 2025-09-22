# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

AudioPages is a Python-based text-to-speech application that uses the ElevenLabs API to convert text to audio. The application offers both command-line and graphical user interfaces, with support for PDF text extraction and various audio playback methods.

## Architecture

### Single-File Application Structure
The entire application is contained in `AudioPages.py` with two main architectures:

1. **TextToSpeechApp** - Core business logic and CLI interface
2. **TextToSpeechGUI** - Tkinter-based graphical user interface

### Key Components

#### Core Classes
- `TextToSpeechApp`: Handles ElevenLabs API integration, voice selection, audio generation, and playback
- `TextToSpeechGUI`: Provides GUI wrapper around TextToSpeechApp with threading support

#### External Dependencies
- **elevenlabs**: Primary API for text-to-speech conversion
- **pygame**: Audio playback (with fallback options)
- **PyPDF2**: PDF text extraction
- **tkinter**: GUI framework (built into Python)
- **requests**: Alternative API calling method

#### Fallback Systems
The application implements robust fallback mechanisms:
- Multiple audio players (pygame → system players → xdg-open)
- Alternative API calling methods (direct SDK → manual HTTP requests)
- Cross-platform audio support (Windows/macOS/Linux)

## Development Commands

### Running the Application
```bash
# Run with interface selection prompt
python3 AudioPages.py

# Run GUI directly  
python3 -c "from AudioPages import run_gui; run_gui()"

# Run CLI directly
python3 -c "from AudioPages import main; main()"
```

### Dependency Management
```bash
# Install required packages (automated in the script)
pip install elevenlabs pygame requests PyPDF2

# Install with user flag (if system install fails)
pip install --user elevenlabs pygame requests PyPDF2

# Reinstall elevenlabs if import issues occur
pip uninstall elevenlabs
pip install elevenlabs
```

### Testing Dependencies
```bash
# Check if all dependencies are available
python3 -c "from AudioPages import ELEVENLABS_AVAILABLE, PYGAME_AVAILABLE, PDF_AVAILABLE; print(f'ElevenLabs: {ELEVENLABS_AVAILABLE}, pygame: {PYGAME_AVAILABLE}, PDF: {PDF_AVAILABLE}')"

# Test ElevenLabs API connection (requires API key)
python3 -c "from AudioPages import TextToSpeechApp; app = TextToSpeechApp(); app.setup_api_key(); app.list_available_voices()"
```

### Audio System Testing
```bash
# Test available audio players on Linux
which mpg123 mpv vlc mplayer aplay

# Test pygame audio initialization
python3 -c "import pygame; pygame.mixer.init(); print('pygame audio OK')"
```

## Configuration

### Environment Variables
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (optional, can be entered at runtime)

### API Key Setup
The application will prompt for an API key if not found in environment variables. Get your key from:
1. Sign up at https://elevenlabs.io/
2. Navigate to profile settings
3. Copy your API key

## Key Features to Understand

### Dynamic Package Installation
The application automatically installs missing dependencies using subprocess calls to pip, with fallback to user installations.

### Threaded Operations
GUI operations use threading to prevent UI freezing during:
- Voice list retrieval
- Audio generation
- Audio playback
- PDF text extraction

### Error Handling Patterns
- Graceful degradation when optional dependencies are missing
- Multiple fallback methods for critical operations
- User-friendly error messages with actionable solutions

### Cross-Platform Compatibility
- Automatic detection of operating system for audio playback
- Platform-specific audio player selection
- Consistent behavior across Windows, macOS, and Linux

## File Structure Context
```
AudioPages/
├── AudioPages.py          # Single-file application containing all functionality
├── README.md             # Basic project description (minimal)
├── LICENSE               # Project license
├── .gitignore           # Standard Python gitignore
└── .git/                # Git repository
```

## Common Workflows

### Adding New Features
When extending the application, consider:
1. Both CLI and GUI interfaces need updates
2. Threading requirements for GUI operations  
3. Error handling and user feedback
4. Cross-platform compatibility
5. Fallback mechanisms for robustness

### Debugging Issues
1. Check dependency availability flags: `ELEVENLABS_AVAILABLE`, `PYGAME_AVAILABLE`, `PDF_AVAILABLE`
2. Verify API key configuration
3. Test audio system compatibility
4. Check network connectivity for ElevenLabs API
5. Review console output for detailed error messages

### Performance Considerations
- Large PDFs are truncated to 5000 characters for audio generation
- Audio generation and playback operations are CPU/network intensive
- GUI uses threading to maintain responsiveness during long operations