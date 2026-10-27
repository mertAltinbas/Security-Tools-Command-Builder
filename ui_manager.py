"""
UI construction and event handling for the Security Command Builder application.
"""

import customtkinter as ctk

import backend_logic
import preset_manager


class CommandBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Security Command Builder")
        self.geometry("1100x700")

        self.tools_data = backend_logic.load_tools_data()

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

        self.mandatory_frame_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.mandatory_frame_container.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.mandatory_frame_container.grid_columnconfigure(0, weight=1)
        self.current_mandatory_frame = None

        self.preset_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.preset_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        self.preset_label = ctk.CTkLabel(self.preset_frame, text="Presets:")
        self.preset_label.pack(side="left", padx=(0, 10))

        self.preset_var = ctk.StringVar(value="Custom")
        self.preset_menu = ctk.CTkOptionMenu(self.preset_frame, variable=self.preset_var, command=self.apply_preset)
        self.preset_menu.pack(side="left")

        self.save_btn = ctk.CTkButton(self.preset_frame, text="Save Preset", width=60, command=self.save_preset)
        self.save_btn.pack(side="left", padx=(10, 0))

        self.delete_btn = ctk.CTkButton(self.preset_frame, text="Delete Preset", width=60, command=self.delete_preset)
        self.delete_btn.pack(side="left", padx=(10, 0))

        self.output_frame = ctk.CTkFrame(self.main_frame)
        self.output_frame.grid(row=4, column=0, sticky="ew")
        self.output_frame.grid_columnconfigure(0, weight=1)

        self.command_display = ctk.CTkEntry(
            self.output_frame,
            state="readonly",
            font=ctk.CTkFont(family="Courier", weight="bold", size=14),
            height=45
        )
        self.command_display.grid(row=0, column=0, sticky="ew", padx=(10, 10), pady=10)
        self.command_display.bind("<Control-a>", self.select_all)

        self.copy_btn = ctk.CTkButton(self.output_frame, text="Copy", command=self.copy_command, width=120, height=45)
        self.copy_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.tool_caches = {}
        self.current_tool_frame = None
        self.current_tool = None
        self.flag_widgets = []
        self.category_groups = []
        self.mandatory_widgets = []

        self.tool_buttons = []
        for i, tool_name in enumerate(self.tools_data.keys()):
            btn = ctk.CTkButton(
                self.tools_scroll_frame,
                text=tool_name,
                command=lambda t=tool_name: self.load_tool(t),
                fg_color="transparent",
                border_width=1,
                text_color=("gray10", "#DCE4EE")
            )
            btn.grid(row=i, column=0, padx=20, pady=10, sticky="ew")
            self.tool_buttons.append(btn)

        for btn in self.tool_buttons:
            btn.configure(state="disabled")

        self.loading_overlay = ctk.CTkFrame(self, fg_color=("gray90", "gray13"))
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.loading_label = ctk.CTkLabel(
            self.loading_overlay, text="Loading tools...", font=ctk.CTkFont(size=16)
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

        self._tools_to_build = list(self.tools_data.keys())
        self._tools_total = len(self._tools_to_build)
        self.after(1, self._build_tools_incrementally)

    def _build_tools_incrementally(self):
        if self._tools_to_build:
            tool_name = self._tools_to_build.pop(0)
            self._build_tool_frame(tool_name)

            done = self._tools_total - len(self._tools_to_build)
            self.loading_label.configure(text=f"Loading tools... ({done}/{self._tools_total})")

            self.after(1, self._build_tools_incrementally)
        else:
            self.loading_overlay.destroy()
            for btn in self.tool_buttons:
                btn.configure(state="normal")

            if self.tools_data:
                first_tool = list(self.tools_data.keys())[0]
                self.load_tool(first_tool)

    def select_all(self, event):
        event.widget.select_range(0, "end")
        event.widget.icursor("end")
        return "break"

    def on_flag_input_change(self, event=None):
        """When a user edits a flag's value or dropdown, mark preset as Custom."""
        self.preset_var.set("Custom")
        if self.current_tool in self.tool_caches:
            self.tool_caches[self.current_tool]["active_preset"] = "Custom"
        self.update_command()

    def _build_tool_frame(self, tool_name):
        tool_info = self.tools_data[tool_name]

        new_mandatory_frame = ctk.CTkFrame(self.mandatory_frame_container, fg_color="transparent")
        new_mandatory_frame.grid_columnconfigure(0, weight=1)

        new_mandatory_widgets = []
        for i, label in enumerate(tool_info.get("mandatory_inputs", [])):
            field_label = ctk.CTkLabel(
                new_mandatory_frame, text=label, anchor="w", font=ctk.CTkFont(size=12)
            )
            field_label.grid(row=i * 2, column=0, sticky="w", padx=(5, 0))

            entry = ctk.CTkEntry(new_mandatory_frame, placeholder_text=f"Enter {label}", height=36)
            entry.grid(row=i * 2 + 1, column=0, sticky="ew", pady=(0, 8))
            entry.bind("<KeyRelease>", self.update_command)
            entry.bind("<Control-a>", self.select_all)

            new_mandatory_widgets.append({"label": label, "entry": entry})

        new_mandatory_frame.grid(row=0, column=0, sticky="ew")
        new_mandatory_frame.grid_remove()

        new_frame = ctk.CTkScrollableFrame(self.main_frame, label_text=f"{tool_name} Parameters")
        new_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 15))

        new_flag_widgets = []
        category_groups = []
        categories = tool_info.get("categories", {})
        row_index = 0

        for category_name, flags in categories.items():
            cat_label = ctk.CTkLabel(
                new_frame,
                text=f"── {category_name} ──",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#3B8ED0"
            )
            cat_label.grid(row=row_index, column=0, columnspan=2, sticky="w", pady=(15, 5), padx=5)
            row_index += 1

            category_rows = []
            category_groups.append((cat_label, category_rows))

            for flag_item in flags:
                flag = flag_item["flag"]
                desc = flag_item["desc"]
                has_input = flag_item.get("has_input", False)
                options = flag_item.get("options", None)
                is_basic = flag_item.get("basic", False)

                var = ctk.StringVar(value="")

                row_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
                row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
                row_frame.grid_columnconfigure(1, weight=1)
                row_index += 1
                category_rows.append(row_frame)

                display_text = f"{flag:<6} | {desc}"

                cb = ctk.CTkCheckBox(
                    row_frame,
                    text=display_text,
                    variable=var,
                    onvalue=flag,
                    offvalue="",
                    font=ctk.CTkFont(family="Courier", size=13)
                )
                cb.grid(row=0, column=0, sticky="w", padx=(15, 10))

                entry = None
                opt_var = None
                is_dropdown = False

                if has_input:
                    if options:
                        is_dropdown = True
                        opt_var = ctk.StringVar(value=options[0])
                        entry = ctk.CTkOptionMenu(
                            row_frame,
                            values=options,
                            variable=opt_var,
                            state="disabled",
                            width=250,
                            command=self.on_flag_input_change
                        )
                        entry.grid(row=0, column=1, sticky="w", padx=(10, 10))
                    else:
                        placeholder = flag_item.get("placeholder", "")
                        entry = ctk.CTkEntry(
                            row_frame, placeholder_text=placeholder, width=250, state="disabled"
                        )
                        entry.grid(row=0, column=1, sticky="w", padx=(10, 10))
                        entry.bind("<KeyRelease>", self.on_flag_input_change)
                        entry.bind("<Control-a>", self.select_all)

                widget_dict = {
                    "flag": flag,
                    "var": var,
                    "cb": cb,
                    "entry": entry,
                    "opt_var": opt_var,
                    "is_dropdown": is_dropdown,
                    "frame": row_frame,
                    "is_basic": is_basic,
                    "is_visible": True
                }
                new_flag_widgets.append(widget_dict)

                cb.configure(command=lambda w=widget_dict: self.on_checkbox_click(w))

        self.tool_caches[tool_name] = {
            "frame": new_frame,
            "flag_widgets": new_flag_widgets,
            "category_groups": category_groups,
            "mandatory_frame": new_mandatory_frame,
            "mandatory_widgets": new_mandatory_widgets,
            "active_preset": "Custom"
        }

        new_frame.grid_remove()

    def load_tool(self, tool_name):
        self.current_tool = tool_name
        tool_info = self.tools_data[tool_name]

        if self.current_tool_frame:
            self.current_tool_frame.grid_remove()

        if self.current_mandatory_frame:
            self.current_mandatory_frame.grid_remove()

        if tool_name not in self.tool_caches:
            self._build_tool_frame(tool_name)

        cache = self.tool_caches[tool_name]
        self.current_tool_frame = cache["frame"]
        self.flag_widgets = cache["flag_widgets"]
        self.category_groups = cache["category_groups"]
        self.current_tool_frame.grid()

        self.current_mandatory_frame = cache["mandatory_frame"]
        self.mandatory_widgets = cache["mandatory_widgets"]
        self.current_mandatory_frame.grid()

        presets = list(tool_info.get("presets", {"Custom": {}}).keys())
        self.preset_menu.configure(values=presets)
        saved_preset = cache.get("active_preset", "Custom")
        self.preset_var.set(saved_preset if saved_preset in presets else "Custom")

        self.apply_mode_filter()
        self.update_command()

    def on_checkbox_click(self, widget_dict):
        self.preset_var.set("Custom")
        if self.current_tool in self.tool_caches:
            self.tool_caches[self.current_tool]["active_preset"] = "Custom"

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
        preset_manager.apply_preset(self, preset_name)

    def update_command(self, event=None):
        if not self.current_tool:
            return

        tool_info = self.tools_data[self.current_tool]

        final_command = backend_logic.build_command_string(
            self.current_tool, tool_info, self.flag_widgets, self.mandatory_widgets
        )

        self.command_display.configure(state="normal")
        self.command_display.delete(0, "end")
        self.command_display.insert(0, final_command)
        self.command_display.configure(state="readonly")

    def copy_command(self):
        self.clipboard_clear()
        self.clipboard_append(self.command_display.get())

        self.copy_btn.configure(text="Copied!")
        self.after(1500, lambda: self.copy_btn.configure(text="Copy"))

    def on_mode_change(self, selected_mode):
        self.apply_mode_filter()
        self.update_command()

    def apply_mode_filter(self):
        mode = self.current_mode.get()

        visible_frames = set()
        for fw in self.flag_widgets:
            show = True if mode == "Advanced" else fw.get("is_basic", False)
            fw["is_visible"] = show
            if show:
                fw["frame"].grid()
                visible_frames.add(fw["frame"])
            else:
                fw["frame"].grid_remove()

        for cat_label, row_frames in self.category_groups:
            any_visible = any(rf in visible_frames for rf in row_frames)
            if any_visible:
                cat_label.grid()
            else:
                cat_label.grid_remove()

        if self.current_tool_frame is not None:
            self.current_tool_frame.update_idletasks()
            self.current_tool_frame._parent_canvas.yview_moveto(0)

    def save_preset(self):
        preset_manager.save_preset(self)

    def delete_preset(self):
        preset_manager.delete_preset(self)