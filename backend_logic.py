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

MANDATORY_FLAG_MAP = {
    "ffuf": {
        "Target URL": "-u",
        "Wordlist": "-w",
    },
}

POSITIONAL_BEFORE_FLAGS = set()


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


def get_mandatory_values(mandatory_widgets):
    """
    Return a dict of {label: value} for the current tool's mandatory
    field widgets (as built by ui_manager._build_tool_frame). An
    empty string means the user hasn't filled that field in yet.
    """
    return {mw["label"]: mw["entry"].get().strip() for mw in mandatory_widgets}


def build_command_string(tool_name, tool_info, flag_widgets, mandatory_widgets):
    """
    Build the full command-line string for `tool_name` from the
    current state of its optional flag widgets and its mandatory
    field widgets.

    Each mandatory field is either:
      - flag-bound (its label is found in MANDATORY_FLAG_MAP for this
        tool): rendered as "{flag} {value}" and placed at the front
        of the optional flags, exactly like a regular checked flag.
      - positional (label not in MANDATORY_FLAG_MAP): rendered as a
        bare word and placed before or after the optional flags
        depending on whether `tool_name` is in
        POSITIONAL_BEFORE_FLAGS (after, by default).

    An empty mandatory field is rendered as "[Label]" so the user can
    see at a glance what's still missing - this replaces the old
    single "[TARGET]" placeholder.
    """
    base = tool_info.get("base_command", "tool")
    flag_map = MANDATORY_FLAG_MAP.get(tool_name, {})

    # Optional flags - unchanged from before.
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

    # Mandatory fields - split into flag-bound vs positional.
    flag_bound_parts = []
    positional_parts = []
    for mw in mandatory_widgets:
        label = mw["label"]
        value = mw["entry"].get().strip()
        display_value = value if value else f"[{label}]"

        if label in flag_map:
            flag_bound_parts.append(f"{flag_map[label]} {display_value}")
        else:
            positional_parts.append(display_value)

    # Flag-bound mandatory fields behave like regular flags, so they
    # sit at the front of the flags portion of the command.
    all_flags = flag_bound_parts + selected_flags

    if tool_name in POSITIONAL_BEFORE_FLAGS:
        command_parts = [base] + positional_parts + all_flags
    else:
        command_parts = [base] + all_flags + positional_parts

    return " ".join(command_parts)