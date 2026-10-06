#!/usr/bin/python3

#  Copyright 2025-2026 Diego Denolf <graffesmusic@gmail.com> 
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

"""
GUI wrapper for ms_concatenate.py
---------------------------------
Provides a simple Tkinter interface to concatenate MuseScore files.
Supports multiple languages via JSON translation files.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import traceback
import os
import sys
import json
import locale
from appdirs import user_config_dir
import ms_concatenate


# Application metadata
APP_NAME = "mscz-concatenator"
APP_VERSION = "1.6"
APP_DATE = "20261006"

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'fr': 'Français',
    'de': 'Deutsch',
    'nl': 'Nederlands',
    'sk': 'Slovenčina'
}

# Config directory (OS-specific, provided by appdirs)
CONFIG_DIR = user_config_dir(APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config():
    """Load user configuration from disk"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config):
    """Save user configuration to disk"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save config: {e}")


def get_system_language():
    """Detect the system language and return a 2-letter code"""
    try:
        # Use the non-deprecated API (Python 3.11+)
        lang, _ = locale.getlocale()
        if not lang:
            # Fallback to environment variables (works on Linux/macOS)
            lang = os.environ.get('LANG') or os.environ.get('LC_ALL') or os.environ.get('LC_MESSAGES')
        if lang:
            code = lang.split('_')[0].split('.')[0].lower()
            if code in SUPPORTED_LANGUAGES:
                return code
    except Exception:
        pass
    return 'en'


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class Translation:
    """Handles loading and accessing translations"""
    
    def __init__(self, lang='en'):
        self.lang = lang
        self.strings = self._load(lang)
    
    def _load(self, lang):
        """Load translation from JSON file, fallback to English"""
        locale_file = get_resource_path(os.path.join('locales', f'{lang}.json'))
        
        if os.path.exists(locale_file):
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load locale file {locale_file}: {e}")
        
        # Fallback to English
        if lang != 'en':
            return self._load('en')
        return {}
    
    def __getitem__(self, key):
        """Get translation string, return key if missing"""
        return self.strings.get(key, key)
    
    def format(self, key, **kwargs):
        """Get translation string and format with parameters"""
        template = self.strings.get(key, key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template


class ConcatenateGUI:
    def __init__(self, root):
        self.root = root
        
        # Load config and determine language
        self.config = load_config()
        self.lang = self.config.get('language') or get_system_language()
        self.t = Translation(self.lang)
        
        self.root.title(f"{self.t['app_title']} v{APP_VERSION}")
        self.root.minsize(900, 650)
        
        self.files = []
        
       
        # Main container with 2 columns
        main_container = tk.Frame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left column - File Management
        left_column = tk.Frame(main_container)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Right column - Options  
        right_column = tk.Frame(main_container)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # --- LEFT COLUMN: File Management ---
        file_frame = tk.LabelFrame(left_column, text=self.t['file_management'], padx=10, pady=5)
        file_frame.pack(fill="both", expand=True)
        
        # Input files listbox with scrollbars
        frame_list = tk.Frame(file_frame)
        frame_list.pack(padx=5, pady=5, fill="both", expand=True)
        
        self.listbox = tk.Listbox(frame_list, height=8, selectmode=tk.EXTENDED)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        
        vscroll = tk.Scrollbar(frame_list, orient="vertical", command=self.listbox.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll = tk.Scrollbar(frame_list, orient="horizontal", command=self.listbox.xview)
        hscroll.grid(row=1, column=0, sticky="ew")
        
        self.listbox.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        frame_list.grid_rowconfigure(0, weight=1)
        frame_list.grid_columnconfigure(0, weight=1)
        
        # Buttons for managing file list (2 rows to save space)
        btn_frame1 = tk.Frame(file_frame)
        btn_frame1.pack(pady=2)
        
        tk.Button(btn_frame1, text=self.t['add_files'], command=self.add_files).pack(side="left", padx=2)
        tk.Button(btn_frame1, text=self.t['remove_selected'], command=self.remove_selected).pack(side="left", padx=2)
        tk.Button(btn_frame1, text=self.t['clear_all'], command=self.clear_all).pack(side="left", padx=2)
        tk.Button(btn_frame1, text=self.t['move_up'], command=self.move_up).pack(side="left", padx=2)
        tk.Button(btn_frame1, text=self.t['move_down'], command=self.move_down).pack(side="left", padx=2)
        
        btn_frame2 = tk.Frame(file_frame)
        btn_frame2.pack(pady=2)
        
        tk.Button(btn_frame2, text=self.t['save_list'], command=self.save_file_list).pack(side="left", padx=2)
        tk.Button(btn_frame2, text=self.t['load_list'], command=self.load_file_list).pack(side="left", padx=2)
        
        # Options below buttons
        options_frame = tk.Frame(file_frame)
        options_frame.pack(fill="x", pady=5)
        
        self.skip_incompatible_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text=self.t['skip_incompatible'], 
                      variable=self.skip_incompatible_var).pack(anchor="w", pady=1)
        
        self.fuzzy_matching_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text=self.t['fuzzy_matching'], 
                      variable=self.fuzzy_matching_var,
                      command=self.toggle_fuzzy_options).pack(anchor="w", pady=1)
        
        # Fuzzy options (hidden by default)
        self.fuzzy_options_frame = tk.Frame(file_frame)
        
        fuzzy_opts = tk.Frame(self.fuzzy_options_frame)
        fuzzy_opts.pack(fill="x", pady=2)
        
        tk.Label(fuzzy_opts, text=self.t['match_threshold']).pack(side="left", padx=5)
        self.match_threshold_var = tk.StringVar(value="0.7")
        self.threshold_entry = tk.Entry(fuzzy_opts, textvariable=self.match_threshold_var, width=4)
        self.threshold_entry.pack(side="left", padx=2)
        
        tk.Label(fuzzy_opts, text=self.t['number_strategy']).pack(side="left", padx=5)
        self.number_strategy_var = tk.StringVar(value="prefer")
        strategy_menu = tk.OptionMenu(fuzzy_opts, self.number_strategy_var, "ignore", "prefer", "match")
        strategy_menu.pack(side="left", padx=2)
        
        self.fuzzy_options_frame.pack_forget()
        
        # --- RIGHT COLUMN: All Options ---
        
        # Content Copying Options
        content_frame = tk.LabelFrame(right_column, text=self.t['content_copying'], padx=10, pady=5)
        content_frame.pack(fill="x", pady=(0, 5))
        
        self.copy_frames_var = tk.BooleanVar(value=True)
        self.copy_frames_cb = tk.Checkbutton(content_frame, text=self.t['copy_frames'], 
                                            variable=self.copy_frames_var,
                                            command=self.toggle_title_frames_option)
        self.copy_frames_cb.pack(anchor="w", pady=1)
        
        self.copy_title_frames_var = tk.BooleanVar(value=True)
        self.copy_title_frames_cb = tk.Checkbutton(content_frame, text=self.t['copy_title_frames'], 
                                                  variable=self.copy_title_frames_var)
        self.copy_title_frames_cb.pack(anchor="w", padx=15, pady=1)
        
        self.copy_system_locks_var = tk.BooleanVar(value=True)
        tk.Checkbutton(content_frame, text=self.t['copy_system_locks'], 
                      variable=self.copy_system_locks_var).pack(anchor="w", pady=1)
        
        self.copy_pictures_var = tk.BooleanVar(value=True)
        tk.Checkbutton(content_frame, text=self.t['copy_pictures'], 
                      variable=self.copy_pictures_var).pack(anchor="w", pady=1)
        
        # Layout Break Options
        break_frame = tk.LabelFrame(right_column, text=self.t['layout_breaks'], padx=10, pady=5)
        break_frame.pack(fill="x", pady=(0, 5))
        
        break_type_frame = tk.Frame(break_frame)
        break_type_frame.pack(fill="x", pady=2)
        
        self.break_system_var = tk.BooleanVar(value=False)
        self.break_page_var = tk.BooleanVar(value=False)
        self.break_section_var = tk.BooleanVar(value=False)
        
        def on_system_break_change(*args):
            if self.break_system_var.get():
                self.break_page_var.set(False)
                self.break_section_var.set(False)
                self.system_info_frame.pack(fill="x", padx=5, pady=2)
            else:
                self.system_info_frame.pack_forget()
        
        def on_page_break_change(*args):
            if self.break_page_var.get():
                self.break_system_var.set(False)
                self.system_info_frame.pack_forget()
        
        def on_section_break_change(*args):
            if self.break_section_var.get():
                self.break_system_var.set(False)
                self.section_options_frame.pack(fill="x", padx=5, pady=2)
            else:
                self.section_options_frame.pack_forget()
        
        self.break_system_var.trace('w', on_system_break_change)
        self.break_page_var.trace('w', on_page_break_change) 
        self.break_section_var.trace('w', on_section_break_change)
        
        tk.Checkbutton(break_type_frame, text=self.t['break_system'], 
                      variable=self.break_system_var).pack(side="left", padx=5)
        tk.Checkbutton(break_type_frame, text=self.t['break_page'], 
                      variable=self.break_page_var).pack(side="left", padx=5)
        tk.Checkbutton(break_type_frame, text=self.t['break_section'], 
                      variable=self.break_section_var).pack(side="left", padx=5)
        
        # System break info
        self.system_info_frame = tk.Frame(break_frame)
        system_info_label = tk.Label(self.system_info_frame, 
                                   text=self.t['system_break_note'],
                                   fg="blue", font=("Arial", 8))
        system_info_label.pack(side="left", padx=5)
        self.system_info_frame.pack_forget()
        
        # Section break options
        self.section_options_frame = tk.Frame(break_frame)
        
        section_row1 = tk.Frame(self.section_options_frame)
        section_row1.pack(fill="x", pady=1)
        tk.Label(section_row1, text=self.t['section_pause']).pack(side="left", padx=5)
        self.section_pause_var = tk.StringVar(value="3")
        self.pause_entry = tk.Entry(section_row1, textvariable=self.section_pause_var, width=4)
        self.pause_entry.pack(side="left", padx=2)
        
        self.has_repeats_var = tk.BooleanVar(value=False)
        tk.Checkbutton(section_row1, text=self.t['section_auto_pause'], 
                      variable=self.has_repeats_var).pack(side="left", padx=10)
        
        section_row2 = tk.Frame(self.section_options_frame)
        section_row2.pack(fill="x", pady=1)
        self.start_long_names_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row2, text=self.t['section_long_names'], 
                      variable=self.start_long_names_var).pack(side="left", padx=5)
        self.start_measure_one_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row2, text=self.t['section_reset_measures'], 
                      variable=self.start_measure_one_var).pack(side="left", padx=10)
        
        section_row3 = tk.Frame(self.section_options_frame)
        section_row3.pack(fill="x", pady=1)
        self.first_system_indent_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row3, text=self.t['section_indent_first'], 
                      variable=self.first_system_indent_var).pack(side="left", padx=5)
        self.show_courtesy_sig_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row3, text=self.t['section_hide_courtesy'], 
                      variable=self.show_courtesy_sig_var).pack(side="left", padx=10)
        
        self.section_options_frame.pack_forget()
        
        # Logging Options
        logging_frame = tk.LabelFrame(right_column, text=self.t['logging'], padx=10, pady=5)
        logging_frame.pack(fill="x", pady=(0, 5))
        
        self.enable_logging_var = tk.BooleanVar(value=False)
        tk.Checkbutton(logging_frame, text=self.t['enable_logging'], 
                      variable=self.enable_logging_var,
                      command=self.toggle_logging_options).pack(anchor="w", pady=1)
        
        self.logging_options_frame = tk.Frame(logging_frame)
        
        log_level_frame = tk.Frame(self.logging_options_frame)
        log_level_frame.pack(fill="x", pady=1)
        tk.Label(log_level_frame, text=self.t['log_level']).pack(side="left", padx=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_menu = tk.OptionMenu(log_level_frame, self.log_level_var, "WARN", "INFO", "DEBUG")
        log_level_menu.pack(side="left", padx=2)
        
        self.overwrite_log_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.logging_options_frame, text=self.t['log_overwrite'], 
                      variable=self.overwrite_log_var).pack(anchor="w", pady=1)
        
        self.custom_log_location_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.logging_options_frame, text=self.t['log_custom_location'], 
                      variable=self.custom_log_location_var,
                      command=self.toggle_custom_log_location).pack(anchor="w", pady=1)
        
        self.log_file_frame = tk.Frame(self.logging_options_frame)
        tk.Label(self.log_file_frame, text=self.t['log_file']).pack(side="left", padx=5)
        self.log_file_var = tk.StringVar()
        self.log_file_entry = tk.Entry(self.log_file_frame, textvariable=self.log_file_var, width=20)
        self.log_file_entry.pack(side="left", padx=2, fill="x", expand=True)
        tk.Button(self.log_file_frame, text=self.t['browse'], command=self.select_log_file).pack(side="left", padx=2)
        
        self.logging_options_frame.pack_forget()
        self.log_file_frame.pack_forget()
        
        # --- BOTTOM: Output and buttons ---
        bottom_container = tk.Frame(root)
        bottom_container.pack(fill="x", padx=10, pady=5)
        
        out_frame = tk.Frame(bottom_container)
        out_frame.pack(fill="x", pady=5)
        tk.Label(out_frame, text=self.t['output_file']).pack(side="left", padx=5)
        self.output_entry = tk.Entry(out_frame)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        tk.Button(out_frame, text=self.t['browse'], command=self.select_output).pack(side="left", padx=5)
        
        # Action buttons
        action_frame = tk.Frame(bottom_container)
        action_frame.pack(pady=5)
        tk.Button(action_frame, text=self.t['concatenate'], command=self.run).pack(side="left", padx=5)
        tk.Button(action_frame, text=self.t['language_menu'], command=self.show_language_dialog).pack(side="left", padx=5)
        tk.Button(action_frame, text=self.t['about'], command=self.show_about).pack(side="left", padx=5)
        tk.Button(action_frame, text=self.t['exit'], command=self.root.quit).pack(side="left", padx=5)
        
        # Status and progress
        self.status = tk.StringVar()
        self.status.set(self.t['status_ready'])
        tk.Label(bottom_container, textvariable=self.status, fg="blue").pack(pady=2)
        
        self.progress = ttk.Progressbar(bottom_container, mode='determinate')
        self.progress.pack(fill="x", pady=5)
        self.progress.pack_forget()
    
    # -------------------------------------------------------------------------
    # Menu and language
    # -------------------------------------------------------------------------
    
    def show_language_dialog(self):
        """Show a dialog to select the language"""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t['language_menu'])
        dialog.transient(self.root)
        dialog.resizable(False, False)
        
        tk.Label(dialog, text=self.t['language_menu'], 
                font=("Arial", 11, "bold")).pack(pady=10, padx=20)
        
        # Create radio buttons for each language
        lang_var = tk.StringVar(value=self.lang)
        
        for code, name in SUPPORTED_LANGUAGES.items():
            tk.Radiobutton(
                dialog, 
                text=name, 
                variable=lang_var, 
                value=code
            ).pack(anchor="w", padx=30, pady=2)
        
        def apply():
            selected = lang_var.get()
            dialog.destroy()
            if selected != self.lang:
                self.change_language(selected)
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=apply, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side="left", padx=5)
        
        # Center dialog on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")


    def change_language(self, lang):
        """Change language and save preference"""
        if lang == self.lang:
            return
        
        # Save preference
        self.config['language'] = lang
        save_config(self.config)
        
        # Ask user if they want to restart now
        if messagebox.askyesno(
            self.t['restart_now_title'],
            self.t['restart_now_message']
        ):
            self.restart_app()
        else:
            lang_name = SUPPORTED_LANGUAGES.get(lang, lang)
            messagebox.showinfo(
                self.t['language_changed_title'],
                self.t.format('language_changed_message', lang=lang_name)
            )


    def restart_app(self):
        """Restart the application"""
        self.root.destroy()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # -------------------------------------------------------------------------
    # Toggle methods
    # -------------------------------------------------------------------------
    
    def toggle_title_frames_option(self):
        """Enable/disable the title frames checkbox based on copy_frames state"""
        if self.copy_frames_var.get():
            self.copy_title_frames_cb.config(state="normal")
        else:
            self.copy_title_frames_cb.config(state="disabled")
            self.copy_title_frames_var.set(False)
            
    def toggle_logging_options(self):
        """Show/hide logging options based on checkbox state"""
        if self.enable_logging_var.get():
            self.logging_options_frame.pack(fill="x", padx=10, pady=5)
            self.custom_log_location_var.set(False)
            self.log_file_frame.pack_forget()
        else:
            self.logging_options_frame.pack_forget()
            self.log_file_frame.pack_forget()

    def toggle_custom_log_location(self):
        """Show/hide custom log file location"""
        if self.custom_log_location_var.get():
            self.log_file_frame.pack(fill="x", padx=10, pady=2)
        else:
            self.log_file_frame.pack_forget()        

    def toggle_fuzzy_options(self):
        """Show/hide fuzzy matching options"""
        if self.fuzzy_matching_var.get():
            self.fuzzy_options_frame.pack(fill="x", padx=5, pady=2)
        else:
            self.fuzzy_options_frame.pack_forget()
    
    # -------------------------------------------------------------------------
    # File handling
    # -------------------------------------------------------------------------
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title=self.t['select_files_title'],
            filetypes=[("MuseScore compressed", "*.mscz")]
        )
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.listbox.insert(tk.END, f)

    def select_log_file(self):
        """Select a log file location"""
        log_file = filedialog.asksaveasfilename(
            title=self.t['select_log_file_title'],
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        if log_file:
            self.log_file_var.set(log_file)

    def select_output(self):
        f = filedialog.asksaveasfilename(
            title=self.t['select_output_title'],
            defaultextension=".mscz",
            filetypes=[("MuseScore compressed", "*.mscz")]
        )
        if f:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, f)
    
    def get_output_path(self):
        """Get output path with guaranteed .mscz extension"""
        output_path = self.output_entry.get().strip()
        if output_path and not output_path.lower().endswith('.mscz'):
            output_path += '.mscz'
        return output_path        

    def remove_selected(self):
        selections = self.listbox.curselection()
        if selections:
            for index in sorted(selections, reverse=True):
                self.files.pop(index)
                self.listbox.delete(index)

    def clear_all(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)
        
    def save_file_list(self):
        """Save the current file list to a text file"""
        if not self.files:
            messagebox.showwarning(self.t['warning_title'], self.t['warning_no_files_save'])
            return
            
        filename = filedialog.asksaveasfilename(
            title=self.t['save_list_title'],
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for file_path in self.files:
                        f.write(file_path + '\n')
                messagebox.showinfo(self.t['success_title'], 
                                   self.t.format('save_list_success', filename=filename))
            except Exception as e:
                messagebox.showerror(self.t['error_title'], 
                                    self.t.format('save_list_error', error=str(e)))
                
    def load_file_list(self):
        """Load a file list from a text file"""
        filename = filedialog.askopenfilename(
            title=self.t['load_list_title'],
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    new_files = [line.strip() for line in f if line.strip()]
                
                valid_files = []
                missing_files = []
                
                for file_path in new_files:
                    if os.path.exists(file_path):
                        valid_files.append(file_path)
                    else:
                        missing_files.append(file_path)
                
                if missing_files:
                    messagebox.showwarning(
                        self.t['missing_files_title'], 
                        self.t.format('missing_files_message',
                                     count=len(missing_files),
                                     files="\n".join(missing_files[:10]) + 
                                           ("\n..." if len(missing_files) > 10 else ""))
                    )
                
                if valid_files:
                    self.files = valid_files
                    self.refresh_listbox()
                    messagebox.showinfo(self.t['success_title'], 
                                       self.t.format('load_list_success', count=len(valid_files)))
                else:
                    messagebox.showwarning(self.t['warning_title'], 
                                          self.t['warning_no_valid_files'])
                    
            except Exception as e:
                messagebox.showerror(self.t['error_title'], 
                                    self.t.format('load_list_error', error=str(e)))

    # -------------------------------------------------------------------------
    # List reordering
    # -------------------------------------------------------------------------
    
    def move_up(self):
        selections = self.listbox.curselection()
        if len(selections) == 1 and selections[0] > 0:
            idx = selections[0]
            self.files[idx-1], self.files[idx] = self.files[idx], self.files[idx-1]
            self.refresh_listbox(idx-1)

    def move_down(self):
        selections = self.listbox.curselection()
        if len(selections) == 1 and selections[0] < len(self.files)-1:
            idx = selections[0]
            self.files[idx+1], self.files[idx] = self.files[idx], self.files[idx+1]
            self.refresh_listbox(idx+1)

    def refresh_listbox(self, new_index=None):
        self.listbox.delete(0, tk.END)
        for f in self.files:
            self.listbox.insert(tk.END, f)
        if new_index is not None:
            self.listbox.selection_set(new_index)
            self.listbox.activate(new_index)

    # -------------------------------------------------------------------------
    # Run concatenation
    # -------------------------------------------------------------------------
    
    def run(self):
        # Show progress bar at start
        self.progress.pack(pady=5, fill="x", padx=10)
        self.progress['value'] = 0
        self.root.update_idletasks()
    
        if not self.files:
            messagebox.showerror(self.t['error_title'], self.t['error_no_files'])
            return
        output = self.get_output_path()
        if not output:
            messagebox.showerror(self.t['error_title'], self.t['error_no_output'])
            return

        try:
            self.progress.pack(pady=5, fill="x", padx=10)
            self.progress['maximum'] = len(self.files)
            self.progress['value'] = 0
            
            self.status.set(self.t['status_starting'])
            self.root.update_idletasks()
            
            log_level = None
            log_file = None
            
            if self.enable_logging_var.get():
                log_level = self.log_level_var.get()
                if self.log_file_var.get().strip():
                    log_file = self.log_file_var.get().strip()
                else:
                    log_file = "mscz-cat.log"

            # Get frame copying options
            copy_frames = self.copy_frames_var.get()
            copy_title_frames = self.copy_title_frames_var.get() if copy_frames else False
            copy_system_locks = self.copy_system_locks_var.get()
            copy_pictures = self.copy_pictures_var.get()  
            
            # Get break options
            break_types = []
            if self.break_system_var.get():
                break_types.append("line")
            if self.break_page_var.get():
                break_types.append("page") 
            if self.break_section_var.get():
                break_types.append("section")

            if not break_types:
                break_type = "none"
            else:
                break_type = ",".join(break_types)

            break_options = None
            if "section" in break_types:
                try:
                    pause_value = float(self.section_pause_var.get())
                except ValueError:
                    pause_value = 3.0
                
                break_options = {
                    'pause': pause_value,
                    'start_with_long_names': self.start_long_names_var.get(),
                    'start_with_measure_one': self.start_measure_one_var.get(),
                    'first_system_indentation': self.first_system_indent_var.get(),
                    'show_courtesy_sig': self.show_courtesy_sig_var.get(),
                    'auto_detect_repeats': self.has_repeats_var.get()
                }
            elif break_type == "page":
                break_options = {'page_break': True}
            elif break_type == "line":
                break_options = {'system_break': True}

            # Get fuzzy matching options
            fuzzy_matching = self.fuzzy_matching_var.get()
            number_strategy = self.number_strategy_var.get().upper()
            try:
                match_threshold = float(self.match_threshold_var.get())
                match_threshold = max(0.0, min(1.0, match_threshold))
            except ValueError:
                match_threshold = 0.7

            # Call the concatenate function
            success, skipped_files = ms_concatenate.concatenate(
                    self.files, 
                    output, 
                    copy_frames=copy_frames,
                    copy_title_frames=copy_title_frames,
                    copy_system_locks=copy_system_locks,
                    copy_pictures=copy_pictures,
                    break_type=break_type,
                    break_options=break_options,
                    skip_incompatible=self.skip_incompatible_var.get(),
                    fuzzy_matching=fuzzy_matching,
                    match_threshold=match_threshold,
                    number_strategy=number_strategy,
                    log_level=log_level,
                    log_file=log_file,
                    console_output=False,
                    overwrite_log=self.overwrite_log_var.get(),
                    progress_callback=self.update_progress     
                )
     
            self.status.set(self.t['status_done'])
            self.progress.pack_forget()
            messagebox.showinfo(self.t['success_title'], 
                               self.t.format('success_message', output=output))
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.t['error_title'], 
                                self.t.format('error_occurred', error=str(e)))
            self.status.set(self.t['status_error'])
            self.progress.pack_forget()

    def update_progress(self, current, total):
        """Callback function to update progress bar"""
        self.progress['value'] = current
        self.status.set(self.t.format('status_processing', current=current, total=total))
        self.root.update_idletasks()

    # -------------------------------------------------------------------------
    # About dialog
    # -------------------------------------------------------------------------
    
    def show_about(self):
        about = tk.Toplevel(self.root)
        about.title(self.t['about'])
        about.geometry("400x275")
        about.resizable(False, False)

        tk.Label(about, text=self.t['app_title'], font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(about, text=self.t.format('about_version', version=APP_VERSION, date=APP_DATE), 
                font=("Arial", 11)).pack(pady=2)
        tk.Label(about, text=self.t['about_author'], font=("Arial", 10)).pack(pady=2)
        
        msg = (
            "Source: https://github.com/diedeno/mscz-concatenator\n" 
            "Based on the mscore library and script © 2025 Leon Dionne https://github.com/Zen-Master-SoSo/mscore\n\n"
            + self.t['about_license']
        )
        tk.Label(about, text=msg, wraplength=360, justify="left").pack(padx=15, pady=10)

        tk.Button(about, text="Close", command=about.destroy).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = ConcatenateGUI(root)
    root.mainloop()
