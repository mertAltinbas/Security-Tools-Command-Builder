"""
Backend logic for the Security Command Builder application.

This module owns every non-UI concern:
- Reading and merging tool definitions from the JSON files under the
  `tools_data` directory (the "dynamic JSON reading" mechanism).
- Persisting changes back to those JSON files (used when presets are
  saved or deleted).
- Reading the current state of a tool's flag widgets and turning it
  into either a finished command-line string or a plain dict of
  {flag: value} (used for both the live preview and preset saving).

ui_manager.py calls into this module instead of touching files or
building the command string itself, so widget/layout code and
data/logic code never bleed into each other.
"""

import json
import os


def load_tools_data(tools_dir="tools_data"):
    """
    Read every *.json file inside `tools_dir` and merge them into a
    single dictionary keyed by tool name.

    Any JSON file dropped into the tools_data folder is automatically
    picked up and merged into the available tools without any code
    changes - this preserves the original dynamic JSON loading
    behavior exactly.
    """
    combined_data = {}

    if os.path.exists(tools_dir):
        for file_name in os.listdir(tools_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(tools_dir, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tool_json = json.load(f)
                        combined_data.update(tool_json)
                except Exception as e:
                    print(f"Error loading {file_name}: {e}")

    return combined_data


def persist_tool_data(tool_name, tools_data, tools_dir="tools_data", error_context="update"):
    """
    Write the current in-memory definition of `tool_name` back to its
    JSON file on disk, preserving any other top-level keys already
    present in that file.

    Returns True on success, False on failure. On failure, the error
    is printed (matching the original app's behavior) using
    `error_context` to describe what was being attempted
    (e.g. "saving preset", "during deletion").
    """
    file_path = os.path.join(tools_dir, f"{tool_name.lower()}.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        file_data[tool_name] = tools_data[tool_name]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(file_data, f, indent=4, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error {error_context}: Could not update JSON file. Details: {e}")
        return False


def get_selected_flag_values(flag_widgets):
    """
    Walk the list of flag widget dictionaries (as built by
    ui_manager._build_tool_frame) and return a dict of
    {flag: value} for every flag that is currently checked and
    visible (i.e. matches the active Basic/Advanced mode filter).

    An empty string value means the flag has no associated input
    (a plain boolean flag). Used when a preset is saved.
    """
    selected = {}
    for fw in flag_widgets:
        if fw["var"].get() and fw["frame"].winfo_ismapped():
            if fw["entry"]:
                if fw["is_dropdown"]:
                    val = fw["opt_var"].get()
                else:
                    val = fw["entry"].get().strip()
                selected[fw["flag"]] = val
            else:
                selected[fw["flag"]] = ""
    return selected


def build_command_string(tool_name, tool_info, target_input, flag_widgets):
    """
    Build the full command-line string for `tool_name` from the
    current state of its flag widgets.

    Reproduces the original ordering rule exactly: Nmap and Hydra put
    the target after all flags, every other tool puts the target
    immediately after the base command.
    """
    base = tool_info.get("base_command", "tool")

    if not target_input:
        target_input = "[TARGET]"

    selected_flags = []
    for fw in flag_widgets:
        if fw["var"].get() and fw["frame"].winfo_ismapped():
            if fw["entry"]:
                if fw["is_dropdown"]:
                    val = fw["opt_var"].get()
                else:
                    val = fw["entry"].get().strip()

                if val:
                    selected_flags.append(f"{fw['flag']} {val}")
                else:
                    selected_flags.append(fw['flag'])
            else:
                selected_flags.append(fw['flag'])

    if tool_name in ["Nmap", "Hydra"]:
        command_parts = [base] + selected_flags + [target_input]
    else:
        command_parts = [base, target_input] + selected_flags

    return " ".join(command_parts)
