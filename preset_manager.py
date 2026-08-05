"""
Preset management for the Security Command Builder application.

Handles applying, saving, and deleting custom presets for the tool
that is currently loaded. Every function here takes the running
CommandBuilderApp instance (`app`) as its first argument so it can
read the current tool/flag-widget state and update the preset
dropdown - but none of these functions build or lay out widgets
themselves, and none of them touch files directly (that stays in
backend_logic.py).

`app` is only imported under TYPE_CHECKING for editor/type-checker
support; at runtime this module never imports ui_manager, which
avoids a circular import between the two modules.
"""

from typing import TYPE_CHECKING

import customtkinter as ctk

import backend_logic

if TYPE_CHECKING:
    from ui_manager import CommandBuilderApp


def apply_preset(app: "CommandBuilderApp", preset_name):
    """Apply the selected preset's flag values onto the current tool's widgets."""
    if not app.current_tool:
        return

    preset_data = app.tools_data[app.current_tool]["presets"].get(preset_name, {})

    for fw in app.flag_widgets:
        if fw["flag"] in preset_data:
            fw["var"].set(fw["flag"])
            if fw["entry"]:
                fw["entry"].configure(state="normal")
                if fw["is_dropdown"]:
                    fw["opt_var"].set(preset_data[fw["flag"]])
                else:
                    fw["entry"].delete(0, "end")
                    fw["entry"].insert(0, preset_data[fw["flag"]])
        else:
            fw["var"].set("")
            if fw["entry"]:
                if not fw["is_dropdown"]:
                    fw["entry"].delete(0, "end")
                fw["entry"].configure(state="disabled")

    app.update_command()


def save_preset(app: "CommandBuilderApp"):
    """
    Prompt the user for a preset name, capture the currently selected
    flags/values, and persist them into the tool's JSON file.
    """
    if not app.current_tool:
        return

    dialog = ctk.CTkInputDialog(text="Enter a name for the preset:", title="Save Preset")
    preset_name = dialog.get_input()

    if not preset_name or preset_name.strip() == "":
        return

    preset_name = preset_name.strip()

    if preset_name.lower() == "custom":
        print("Error: 'Custom' is a reserved preset name. Please choose a different name.")
        return

    tagged_preset_name = f"[Custom] {preset_name}"

    new_preset_data = backend_logic.get_selected_flag_values(app.flag_widgets)

    if "presets" not in app.tools_data[app.current_tool]:
        app.tools_data[app.current_tool]["presets"] = {}

    app.tools_data[app.current_tool]["presets"][tagged_preset_name] = new_preset_data

    success = backend_logic.persist_tool_data(
        app.current_tool, app.tools_data, error_context="saving preset"
    )

    if not success:
        return

    file_path_for_log = f"tools_data/{app.current_tool.lower()}.json"
    print(f"Success: '{tagged_preset_name}' preset saved to {file_path_for_log}.")

    presets = list(app.tools_data[app.current_tool]["presets"].keys())

    app.preset_menu.configure(values=presets)
    app.preset_var.set(tagged_preset_name)


def delete_preset(app: "CommandBuilderApp"):
    """Delete the currently selected preset and persist the change."""
    if not app.current_tool:
        return

    selected_preset = app.preset_var.get()

    if selected_preset.lower() == "custom":
        print("Error: Cannot delete the 'Custom' preset. It is reserved for user input.")
        return

    if selected_preset in app.tools_data[app.current_tool].get("presets", {}):
        del app.tools_data[app.current_tool]["presets"][selected_preset]

        success = backend_logic.persist_tool_data(
            app.current_tool, app.tools_data, error_context="during deletion"
        )

        if not success:
            return

        file_path_for_log = f"tools_data/{app.current_tool.lower()}.json"
        print(f"Success: Preset '{selected_preset}' deleted successfully from {file_path_for_log}.")

        presets = list(app.tools_data[app.current_tool]["presets"].keys())

        app.preset_menu.configure(values=presets)

        app.preset_var.set("Custom")
        apply_preset(app, "Custom")

    else:
        print(f"Error: Preset '{selected_preset}' not found in the database.")
