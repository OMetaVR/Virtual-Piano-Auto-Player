# MIDI Maestro

MIDI Maestro is a sophisticated Python-based MIDI player featuring a custom sheet music format and an intuitive PyQt5 GUI. This application empowers users to load, play, and manipulate both MIDI files and custom sheet music with ease.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Custom Sheet Format](#custom-sheet-format)
- [File Structure](#file-structure)
- [Controls](#controls)
- [Contributing](#contributing)
- [License](#license)

## Features

- [x] Load and play standard MIDI files (.mid, .midi)
- [x] Support for proprietary sheet music format (.sheet)
- [x] Sleek PyQt5-based graphical user interface
- [x] Real-time playback control (play, pause, stop)
- [x] Comprehensive song list with search functionality
- [x] Dynamic BPM (tempo) and transposition display
- [x] Visual progress bar for playback tracking
- [x] Convenient keyboard shortcuts for playback control
- [x] Multi-threaded playback for smooth performance
- [x] Error handling and user feedback system

## Requirements

- Python 3.7+
- PyQt5
- mido
- pynput

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/midi-maestro.git
   cd midi-maestro
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Launch the application:
   ```
   python init.py
   ```

2. Place your MIDI files (.mid, .midi) or custom sheet files (.sheet) in the `songs` directory.

3. Use the GUI to:
   - Select and play songs
   - Control playback (play, pause, stop)
   - Search for specific tracks
   - Adjust tempo and transposition

## Custom Sheet Format

MIDI Maestro supports a proprietary sheet music format (.sheet) alongside standard MIDI files. The format is structured as follows:

1. **Line 1**: Tempo (BPM)
2. **Line 2**: Transposition value
3. **Remaining lines**: Note sequences using custom notation

Example:
```
120
0
C D E F G A B C
```

## File Structure

- `init.py`: Main application file with GUI implementation
- `midi.py`: MIDI file handling and translation logic
- `player.py`: Core music playback engine
- `classes.py`: Data classes for song representation

## Controls

- **F1**: Navigate to previous song
- **F2**: Toggle play/pause
- **F3**: Skip to next song

## Contributing

We welcome contributions to MIDI Maestro! If you'd like to contribute, please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your code adheres to our coding standards and includes appropriate tests.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
