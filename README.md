# Security Command Builder

A simple desktop GUI application built with Python and CustomTkinter to help construct command-line arguments for common security tools (`Nmap`, `Hydra`, and `ffuf`).

## Features
- **Interactive Flag Selection:** Toggle flags and provide parameters easily without memorizing CLI syntax.
- **Basic & Advanced Modes:** Filter between common everyday flags and the full set of tool options.
- **Custom Presets:** Load built-in presets or save and delete your own custom flag combinations.
- **Dynamic Tool Loading:** Automatically loads any `.json` tool configuration placed in the `tools_data/` folder.
- **One-Click Copy:** Copy the generated command directly to your clipboard.

## Requirements
- Python 3.8+
- `customtkinter`

## Installation & Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

## Project Structure
- `main.py` — Application entry point.
- `ui_manager.py` — GUI layout and user interaction handlers.
- `backend_logic.py` — JSON data loading, saving, and CLI command string generation.
- `preset_manager.py` — Logic for applying, saving, and deleting presets.
- `tools_data/` — JSON configuration files for each supported tool (`nmap.json`, `hydra.json`, `ffuf.json`).