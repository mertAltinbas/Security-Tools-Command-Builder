"""
Entry point for the Security Command Builder application.

Run with: python main.py

This file only bootstraps the application: it configures the
CustomTkinter theme and starts the CommandBuilderApp defined in
ui_manager.py. It contains no widget-construction, business-logic,
or file-I/O code of its own.
"""

import customtkinter as ctk

from ui_manager import CommandBuilderApp

# Set the appearance and color theme for the custom Tkinter UI.
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


if __name__ == "__main__":
    app = CommandBuilderApp()
    app.mainloop()
