import customtkinter as ctk
import json
import os

# Set the appearance and color theme for the custom Tkinter UI.
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class CommandBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Window title and startup size.
        self.title("Security Command Builder")
        self.geometry("1100x700")

        # Load tool configurations from data.json.
        self.tools_data = self.load_data()

        # Allow the main content area to expand when resizing.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Tools", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.tools_scroll_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.tools_scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.tools_scroll_frame.grid_columnconfigure(0, weight=1)

        self.disclaimer_frame = ctk.CTkFrame(self.sidebar_frame, corner_radius=0, fg_color=("gray85", "gray17"))
        self.disclaimer_frame.grid(row=2, column=0, sticky="ew")
        self.disclaimer_frame.grid_columnconfigure(0, weight=1)

        self.disclaimer_label = ctk.CTkLabel(
            self.disclaimer_frame,
            text="Note: It is the user's responsibility to ensure selected flags are compatible. Conflicting flags may cause the tool to fail in the terminal.",
            text_color="#FF7300",
            font=ctk.CTkFont(size=13),
            justify="left",
            wraplength=180,
            anchor="w"
        )
        self.disclaimer_label.grid(row=0, column=0, sticky="ew", padx=20, pady=15)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.current_mode = ctk.StringVar(value="Basic")
        self.mode_selector = ctk.CTkSegmentedButton(
            self.main_frame,
            values=["Basic", "Advanced"],
            variable=self.current_mode,
            command=self.on_mode_change
        )
        self.mode_selector.grid(row=0, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.target_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Enter Target IP or URL (e.g., 10.10.10.10)", height=40)
        self.target_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.target_entry.bind("<KeyRelease>", self.update_command)
        self.target_entry.bind("<Control-a>", self.select_all)

        self.preset_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.preset_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        self.preset_label = ctk.CTkLabel(self.preset_frame, text="Presets:")
        self.preset_label.pack(side="left", padx=(0, 10))

        self.preset_var = ctk.StringVar(value="Custom")
        self.preset_menu = ctk.CTkOptionMenu(self.preset_frame, variable=self.preset_var, command=self.apply_preset)
        self.preset_menu.pack(side="left")

        self.output_frame = ctk.CTkFrame(self.main_frame)
        self.output_frame.grid(row=4, column=0, sticky="ew")
        self.output_frame.grid_columnconfigure(0, weight=1)

        self.command_display = ctk.CTkEntry(self.output_frame, state="disabled", font=ctk.CTkFont(family="Courier", weight="bold", size=14), height=45)
        self.command_display.grid(row=0, column=0, sticky="ew", padx=(10, 10), pady=10)
        self.command_display.bind("<Control-a>", self.select_all)

        self.copy_btn = ctk.CTkButton(self.output_frame, text="Copy", command=self.copy_command, width=120, height=45)
        self.copy_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.tool_caches = {}
        self.current_tool_frame = None
        self.current_tool = None
        self.flag_widgets = []
        self.category_groups = []

        for i, tool_name in enumerate(self.tools_data.keys()):
            btn = ctk.CTkButton(self.tools_scroll_frame, text=tool_name, 
                                command=lambda t=tool_name: self.load_tool(t),
                                fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
            btn.grid(row=i, column=0, padx=20, pady=10, sticky="ew")

        if self.tools_data:
            first_tool = list(self.tools_data.keys())[0]
            self.load_tool(first_tool)

    def select_all(self, event):
        # Select all text in an entry widget when Ctrl+A is pressed.
        event.widget.select_range(0, 'end')
        event.widget.icursor('end')
        return 'break'

    def load_data(self):
        # Read tool definitions from the local JSON file.
        tools_dir = "tools_data"
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

    def load_tool(self, tool_name):
        self.current_tool = tool_name
        tool_info = self.tools_data[tool_name]
        
        presets = list(tool_info.get("presets", {"Custom": {}}).keys())
        self.preset_menu.configure(values=presets)
        self.preset_var.set("Custom")

        if self.current_tool_frame:
            self.current_tool_frame.grid_remove()

        if tool_name in self.tool_caches:
            self.current_tool_frame = self.tool_caches[tool_name]["frame"]
            self.flag_widgets = self.tool_caches[tool_name]["flag_widgets"]
            self.current_tool_frame.grid() 
        else:
            new_frame = ctk.CTkScrollableFrame(self.main_frame, label_text=f"{tool_name} Parameters")
            new_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 15))
            
            new_flag_widgets = []
            category_groups = [] 
            categories = tool_info.get("categories", {})
            row_index = 0

            for category_name, flags in categories.items():
                cat_label = ctk.CTkLabel(new_frame, text=f"── {category_name} ──", 
                                         font=ctk.CTkFont(size=14, weight="bold"), text_color="#3B8ED0")
                cat_label.grid(row=row_index, column=0, columnspan=2, sticky="w", pady=(15, 5), padx=5)
                row_index += 1

                category_rows = []
                category_groups.append((cat_label, category_rows))

                for flag_item in flags:
                    flag = flag_item["flag"]
                    desc = flag_item["desc"]
                    has_input = flag_item.get("has_input", False)
                    options = flag_item.get("options", None)
                    # Only flags explicitly marked "basic": true in the JSON show
                    # up in Basic mode. Anything without the key (or with it set
                    # to false) is treated as advanced-only.
                    is_basic = flag_item.get("basic", False)
                    
                    var = ctk.StringVar(value="")
                    
                    row_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
                    row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
                    row_frame.grid_columnconfigure(1, weight=1)
                    row_index += 1
                    category_rows.append(row_frame)
                    
                    display_text = f"{flag:<6} | {desc}"
                    
                    cb = ctk.CTkCheckBox(row_frame, text=display_text, variable=var, 
                                         onvalue=flag, offvalue="", 
                                         font=ctk.CTkFont(family="Courier", size=13))
                    cb.grid(row=0, column=0, sticky="w", padx=(15, 10))
                    
                    entry = None
                    opt_var = None
                    is_dropdown = False
                    
                    if has_input:
                        if options:
                            is_dropdown = True
                            opt_var = ctk.StringVar(value=options[0])
                            entry = ctk.CTkOptionMenu(row_frame, values=options, variable=opt_var, state="disabled", width=250, command=self.update_command)
                            entry.grid(row=0, column=1, sticky="w", padx=(10, 10))
                        else:
                            placeholder = flag_item.get("placeholder", "")
                            entry = ctk.CTkEntry(row_frame, placeholder_text=placeholder, width=250, state="disabled")
                            entry.grid(row=0, column=1, sticky="w", padx=(10, 10))
                            entry.bind("<KeyRelease>", self.update_command)
                            entry.bind("<Control-a>", self.select_all)
                        
                    widget_dict = {
                        "flag": flag, 
                        "var": var, 
                        "cb": cb, 
                        "entry": entry, 
                        "opt_var": opt_var,
                        "is_dropdown": is_dropdown,
                        "frame": row_frame,
                        "is_basic": is_basic
                    }
                    new_flag_widgets.append(widget_dict)
                    
                    cb.configure(command=lambda w=widget_dict: self.on_checkbox_click(w))

            self.tool_caches[tool_name] = {
                "frame": new_frame,
                "flag_widgets": new_flag_widgets,
                "category_groups": category_groups
            }
            
            self.current_tool_frame = new_frame
            self.flag_widgets = new_flag_widgets
            self.category_groups = category_groups

        if tool_name in self.tool_caches:
            self.category_groups = self.tool_caches[tool_name]["category_groups"]

        self.apply_mode_filter()
        self.update_command()

    def on_checkbox_click(self, widget_dict):
        # Switch to custom mode when the user modifies a flag selection.
        self.preset_var.set("Custom")
        if widget_dict["var"].get():
            if widget_dict["entry"]:
                widget_dict["entry"].configure(state="normal")
                
                if not widget_dict["is_dropdown"]:
                    current_placeholder = widget_dict["entry"].cget("placeholder_text")
                    widget_dict["entry"].configure(placeholder_text="")
                    widget_dict["entry"].configure(placeholder_text=current_placeholder)
        else:
            if widget_dict["entry"]:
                if not widget_dict["is_dropdown"]:
                    widget_dict["entry"].delete(0, "end")
                widget_dict["entry"].configure(state="disabled")
                
        self.update_command()

    def apply_preset(self, preset_name):
        # Apply the selected preset values to the current tool's flags.
        if not self.current_tool:
            return
            
        preset_data = self.tools_data[self.current_tool]["presets"].get(preset_name, {})
        
        for fw in self.flag_widgets:
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
                    
        self.update_command()

    def update_command(self, event=None):
        # Rebuild the command string whenever inputs change.
        if not self.current_tool:
            return

        tool_info = self.tools_data[self.current_tool]
        
        base = tool_info.get("base_command", "tool")
        
        target_input = self.target_entry.get().strip()
        if not target_input:
            target_input = "[TARGET]"

        selected_flags = []
        for fw in self.flag_widgets:
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

        if self.current_tool in ["Nmap", "Hydra"]:
            command_parts = [base] + selected_flags + [target_input]
        else:
            command_parts = [base, target_input] + selected_flags

        final_command = " ".join(command_parts)

        self.command_display.configure(state="normal")
        self.command_display.delete(0, "end")
        self.command_display.insert(0, final_command)
        self.command_display.configure(state="disabled")

    def copy_command(self):
        # Copy the generated command to clipboard and show temporary feedback.
        self.clipboard_clear()
        self.clipboard_append(self.command_display.get())
        
        self.copy_btn.configure(text="Copied!")
        self.after(1500, lambda: self.copy_btn.configure(text="Copy"))

    def on_mode_change(self, selected_mode):
        # Re-filter the currently visible tool's flags for the new mode.
        self.apply_mode_filter()
        self.update_command()

    def apply_mode_filter(self):
        # Show/hide individual flag rows depending on Basic vs Advanced mode.
        # In Basic mode only flags explicitly marked "basic": true are shown;
        # everything else (missing key or "basic": false) is advanced-only.
        mode = self.current_mode.get()

        for fw in self.flag_widgets:
            show = True if mode == "Advanced" else fw.get("is_basic", False)
            if show:
                fw["frame"].grid()
            else:
                fw["frame"].grid_remove()

        for cat_label, row_frames in self.category_groups:
            any_visible = any(rf.winfo_ismapped() for rf in row_frames)
            if any_visible:
                cat_label.grid()
            else:
                cat_label.grid_remove()

if __name__ == "__main__":
    app = CommandBuilderApp()
    app.mainloop()