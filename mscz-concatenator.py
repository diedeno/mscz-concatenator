#!/usr/bin/python3

#  Copyright 2025 Diego Denolf <graffesmusic@gmail.com> 
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
GUI wrapper for ms-concatenate.py
---------------------------------
Provides a simple Tkinter interface to concatenate MuseScore files.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import traceback
import os
import ms_concatenate  # must be in the same folder or installed as a module


class ConcatenateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MuseScore Concatenator v1.5")
        
        # Set reasonable minimum size
        self.root.minsize(900, 650)
        
        self.files = []

        # --- Main container with 2 columns ---
        main_container = tk.Frame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left column - File Management
        left_column = tk.Frame(main_container)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Right column - Options  
        right_column = tk.Frame(main_container)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # --- LEFT COLUMN: File Management ---
        file_frame = tk.LabelFrame(left_column, text="File Management", padx=10, pady=5)
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
        
        tk.Button(btn_frame1, text="Add Files", command=self.add_files).pack(side="left", padx=2)
        tk.Button(btn_frame1, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=2)
        tk.Button(btn_frame1, text="Clear All", command=self.clear_all).pack(side="left", padx=2)
        tk.Button(btn_frame1, text="Move Up", command=self.move_up).pack(side="left", padx=2)
        tk.Button(btn_frame1, text="Move Down", command=self.move_down).pack(side="left", padx=2)
        
        btn_frame2 = tk.Frame(file_frame)
        btn_frame2.pack(pady=2)
        
        tk.Button(btn_frame2, text="Save List", command=self.save_file_list).pack(side="left", padx=2)
        tk.Button(btn_frame2, text="Load List", command=self.load_file_list).pack(side="left", padx=2)

        # Options below buttons
        options_frame = tk.Frame(file_frame)
        options_frame.pack(fill="x", pady=5)

        self.skip_incompatible_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Skip incompatible files", 
                      variable=self.skip_incompatible_var).pack(anchor="w", pady=1)
        
        self.fuzzy_matching_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Fuzzy instrument matching", 
                      variable=self.fuzzy_matching_var,
                      command=self.toggle_fuzzy_options).pack(anchor="w", pady=1)

        # Fuzzy options (hidden by default)
        self.fuzzy_options_frame = tk.Frame(file_frame)
        
        fuzzy_opts = tk.Frame(self.fuzzy_options_frame)
        fuzzy_opts.pack(fill="x", pady=2)
        
        tk.Label(fuzzy_opts, text="Threshold:").pack(side="left", padx=5)
        self.match_threshold_var = tk.StringVar(value="0.7")
        self.threshold_entry = tk.Entry(fuzzy_opts, textvariable=self.match_threshold_var, width=4)
        self.threshold_entry.pack(side="left", padx=2)
        
        tk.Label(fuzzy_opts, text="Strategy:").pack(side="left", padx=5)
        self.number_strategy_var = tk.StringVar(value="prefer")
        strategy_menu = tk.OptionMenu(fuzzy_opts, self.number_strategy_var, "ignore", "prefer", "match")
        strategy_menu.pack(side="left", padx=2)
        
        self.fuzzy_options_frame.pack_forget()

        # --- RIGHT COLUMN: All Options ---
        
        # Content Copying Options
        content_frame = tk.LabelFrame(right_column, text="Content Copying", padx=10, pady=5)
        content_frame.pack(fill="x", pady=(0, 5))

        self.copy_frames_var = tk.BooleanVar(value=True)
        self.copy_frames_cb = tk.Checkbutton(content_frame, text="Copy frames", 
                                            variable=self.copy_frames_var,
                                            command=self.toggle_title_frames_option)
        self.copy_frames_cb.pack(anchor="w", pady=1)

        self.copy_title_frames_var = tk.BooleanVar(value=True)
        self.copy_title_frames_cb = tk.Checkbutton(content_frame, text="Copy title frames", 
                                                  variable=self.copy_title_frames_var)
        self.copy_title_frames_cb.pack(anchor="w", padx=15, pady=1)

        self.copy_system_locks_var = tk.BooleanVar(value=True)
        tk.Checkbutton(content_frame, text="Copy system locks", 
                      variable=self.copy_system_locks_var).pack(anchor="w", pady=1)
        
        self.copy_pictures_var = tk.BooleanVar(value=True)
        tk.Checkbutton(content_frame, text="Copy pictures", 
                      variable=self.copy_pictures_var).pack(anchor="w", pady=1)

        # Layout Break Options
        break_frame = tk.LabelFrame(right_column, text="Layout Breaks", padx=10, pady=5)
        break_frame.pack(fill="x", pady=(0, 5))

        break_type_frame = tk.Frame(break_frame)
        break_type_frame.pack(fill="x", pady=2)

        self.break_system_var = tk.BooleanVar(value=False)
        self.break_page_var = tk.BooleanVar(value=False)
        self.break_section_var = tk.BooleanVar(value=False)

        # Mutual exclusion functions (same as before)
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

        tk.Checkbutton(break_type_frame, text="System", variable=self.break_system_var).pack(side="left", padx=5)
        tk.Checkbutton(break_type_frame, text="Page", variable=self.break_page_var).pack(side="left", padx=5)
        tk.Checkbutton(break_type_frame, text="Section", variable=self.break_section_var).pack(side="left", padx=5)

        # System break info
        self.system_info_frame = tk.Frame(break_frame)
        system_info_label = tk.Label(self.system_info_frame, 
                                   text="Note: System breaks won't add with system locks",
                                   fg="blue", font=("Arial", 8))
        system_info_label.pack(side="left", padx=5)
        self.system_info_frame.pack_forget()

        # Section break options
        self.section_options_frame = tk.Frame(break_frame)
        
        section_row1 = tk.Frame(self.section_options_frame)
        section_row1.pack(fill="x", pady=1)
        tk.Label(section_row1, text="Pause:").pack(side="left", padx=5)
        self.section_pause_var = tk.StringVar(value="3")
        self.pause_entry = tk.Entry(section_row1, textvariable=self.section_pause_var, width=4)
        self.pause_entry.pack(side="left", padx=2)
        
        self.has_repeats_var = tk.BooleanVar(value=False)
        tk.Checkbutton(section_row1, text="Auto pause=0 for repeats", 
                      variable=self.has_repeats_var).pack(side="left", padx=10)
        
        section_row2 = tk.Frame(self.section_options_frame)
        section_row2.pack(fill="x", pady=1)
        self.start_long_names_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row2, text="Long names", variable=self.start_long_names_var).pack(side="left", padx=5)
        self.start_measure_one_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row2, text="Reset measures", variable=self.start_measure_one_var).pack(side="left", padx=10)
        
        section_row3 = tk.Frame(self.section_options_frame)
        section_row3.pack(fill="x", pady=1)
        self.first_system_indent_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row3, text="Indent first system", variable=self.first_system_indent_var).pack(side="left", padx=5)
        self.show_courtesy_sig_var = tk.BooleanVar(value=True)
        tk.Checkbutton(section_row3, text="Hide courtesy sigs", variable=self.show_courtesy_sig_var).pack(side="left", padx=10)
        
        self.section_options_frame.pack_forget()

        # Logging Options
        logging_frame = tk.LabelFrame(right_column, text="Logging", padx=10, pady=5)
        logging_frame.pack(fill="x", pady=(0, 5))

        self.enable_logging_var = tk.BooleanVar(value=False)
        tk.Checkbutton(logging_frame, text="Enable logging", 
                      variable=self.enable_logging_var,
                      command=self.toggle_logging_options).pack(anchor="w", pady=1)

        self.logging_options_frame = tk.Frame(logging_frame)
        
        log_level_frame = tk.Frame(self.logging_options_frame)
        log_level_frame.pack(fill="x", pady=1)
        tk.Label(log_level_frame, text="Level:").pack(side="left", padx=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_menu = tk.OptionMenu(log_level_frame, self.log_level_var, "WARN", "INFO", "DEBUG")
        log_level_menu.pack(side="left", padx=2)
        
        self.overwrite_log_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.logging_options_frame, text="Overwrite log", 
                      variable=self.overwrite_log_var).pack(anchor="w", pady=1)
        
        self.custom_log_location_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.logging_options_frame, text="Custom log location", 
                      variable=self.custom_log_location_var,
                      command=self.toggle_custom_log_location).pack(anchor="w", pady=1)
        
        self.log_file_frame = tk.Frame(self.logging_options_frame)
        tk.Label(self.log_file_frame, text="File:").pack(side="left", padx=5)
        self.log_file_var = tk.StringVar()
        self.log_file_entry = tk.Entry(self.log_file_frame, textvariable=self.log_file_var, width=20)
        self.log_file_entry.pack(side="left", padx=2, fill="x", expand=True)
        tk.Button(self.log_file_frame, text="Browse", command=self.select_log_file).pack(side="left", padx=2)
        
        self.logging_options_frame.pack_forget()
        self.log_file_frame.pack_forget()

        # --- BOTTOM: Output and buttons ---
        bottom_container = tk.Frame(root)
        bottom_container.pack(fill="x", padx=10, pady=5)

        out_frame = tk.Frame(bottom_container)
        out_frame.pack(fill="x", pady=5)
        tk.Label(out_frame, text="Output File:").pack(side="left", padx=5)
        self.output_entry = tk.Entry(out_frame)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        tk.Button(out_frame, text="Browse", command=self.select_output).pack(side="left", padx=5)

        # Action buttons
        action_frame = tk.Frame(bottom_container)
        action_frame.pack(pady=5)
        tk.Button(action_frame, text="Concatenate", command=self.run).pack(side="left", padx=5)
        tk.Button(action_frame, text="About", command=self.show_about).pack(side="left", padx=5)
        tk.Button(action_frame, text="Exit", command=self.root.quit).pack(side="left", padx=5)

        # Status and progress
        self.status = tk.StringVar()
        self.status.set("Ready")
        tk.Label(bottom_container, textvariable=self.status, fg="blue").pack(pady=2)
        
        self.progress = ttk.Progressbar(bottom_container, mode='determinate')
        self.progress.pack(fill="x", pady=5)
        self.progress.pack_forget()
        
    def toggle_title_frames_option(self):
        """Enable/disable the title frames checkbox based on copy_frames state"""
        if self.copy_frames_var.get():
            self.copy_title_frames_cb.config(state="normal")
        else:
            self.copy_title_frames_cb.config(state="disabled")
            self.copy_title_frames_var.set(False)  # Auto-uncheck when frames are disabled
            
    def on_repeat_checkbox_change(self):
        """Handle the repeat checkbox - just update the label, don't modify pause value"""
        if self.has_repeats_var.get():
            print("Auto-repeat detection enabled - files with repeats will get pause=0")
        else:
            print("Auto-repeat detection disabled - all files will use the pause value above")
        # Don't modify the pause value or field state - keep it always editable
            
    def toggle_logging_options(self):
        """Show/hide logging options based on checkbox state"""
        if self.enable_logging_var.get():
            self.logging_options_frame.pack(fill="x", padx=10, pady=5)
            # Reset custom location to hidden when enabling logging
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
            self.fuzzy_options_frame.pack(fill="x", padx=5, pady=2)  # Changed from fuzzy_strategy_frame
        else:
            self.fuzzy_options_frame.pack_forget()  # Changed from fuzzy_strategy_frame

    # -------------------------------------------------------------------------
    # File handling
    # -------------------------------------------------------------------------
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select MuseScore files",
            filetypes=[("MuseScore compressed", "*.mscz")]
        )
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.listbox.insert(tk.END, f)

    def select_log_file(self):
        """Select a log file location"""
        log_file = filedialog.asksaveasfilename(
            title="Select log file location",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        if log_file:
            self.log_file_var.set(log_file)   


    def select_output(self):
        f = filedialog.asksaveasfilename(
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
            # Remove from the end to avoid index shifting issues
            for index in sorted(selections, reverse=True):
                self.files.pop(index)
                self.listbox.delete(index)

    def clear_all(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)
        
    def save_file_list(self):
        """Save the current file list to a text file"""
        if not self.files:
            messagebox.showwarning("Warning", "No files to save")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save file list",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for file_path in self.files:
                        f.write(file_path + '\n')
                messagebox.showinfo("Success", f"File list saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file list:\n{e}")
                
    def load_file_list(self):
        """Load a file list from a text file"""
        filename = filedialog.askopenfilename(
            title="Load file list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    new_files = [line.strip() for line in f if line.strip()]
                
                # Validate that files exist
                valid_files = []
                missing_files = []
                
                for file_path in new_files:
                    if os.path.exists(file_path):
                        valid_files.append(file_path)
                    else:
                        missing_files.append(file_path)
                
                if missing_files:
                    messagebox.showwarning(
                        "Missing Files", 
                        f"{len(missing_files)} files could not be found and were skipped:\n\n" +
                        "\n".join(missing_files[:10]) + 
                        ("\n..." if len(missing_files) > 10 else "")
                    )
                
                if valid_files:
                    # Clear current list and add loaded files
                    self.files = valid_files
                    self.refresh_listbox()
                    messagebox.showinfo("Success", f"Loaded {len(valid_files)} files")
                else:
                    messagebox.showwarning("Warning", "No valid files found in the list")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file list:\n{e}")                

    # -------------------------------------------------------------------------
    # List reordering
    # -------------------------------------------------------------------------
    
    # allow only one file to move up/down
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
    """
    ## allow selection to move up/down
    def move_up(self):
        selections = self.listbox.curselection()
        if selections and selections[0] > 0:  # Only if first selected item can move up
            # For simplicity, let's just move the first selected item
            idx = selections[0]
            self.files[idx-1], self.files[idx] = self.files[idx], self.files[idx-1]
            self.refresh_listbox(idx-1)

    def move_down(self):
        selections = self.listbox.curselection()
        if selections and selections[-1] < len(self.files)-1:  # Only if last selected item can move down
            # For simplicity, let's just move the last selected item  
            idx = selections[-1]
            self.files[idx+1], self.files[idx] = self.files[idx], self.files[idx+1]
            self.refresh_listbox(idx+1)     
    ###               
    """        

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
        #logger.debug(f"RUN: Run method called")
        
        # Show progress bar at start
        self.progress.pack(pady=5, fill="x", padx=10)
        self.progress['value'] = 0
        self.root.update_idletasks()  # Force GUI update
    
    
        if not self.files:
            messagebox.showerror("Error", "No input files selected")
            return
        output = self.get_output_path()  # ← Use the new method
        if not output:
            messagebox.showerror("Error", "No output file specified")
            return

        try:
            # Show and reset progress bar
            self.progress.pack(pady=5, fill="x", padx=10)
            self.progress['maximum'] = len(self.files)  # Total files to process
            self.progress['value'] = 0
            
            self.status.set("Starting...")
            self.root.update_idletasks()  # Force GUI update
            
            log_level = None
            log_file = None
            
            if self.enable_logging_var.get():
                log_level = self.log_level_var.get()
                
                # Use custom log file if specified, otherwise use default
                if self.log_file_var.get().strip():
                    log_file = self.log_file_var.get().strip()
                else:
                    # Default log files in current directory
                    if log_level == "DEBUG":
                        log_file = "mscz-cat.log" # better log to same file after 2nd thought
                    else:
                        log_file = "mscz-cat.log"

            # Get the frame copying options
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

            # If no breaks selected, use "none"
            if not break_types:
                break_type = "none"  # Keep as string for backward compatibility
            else:
                break_type = ",".join(break_types)  # Join multiple types with commas

            break_options = None
            if "section" in break_types:  # Use break_types list here for the check
                # Get section break options
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
            elif break_type == "line":  # Add this for system breaks
                break_options = {'system_break': True}


            # Get fuzzy matching options
            fuzzy_matching = self.fuzzy_matching_var.get()
            number_strategy = self.number_strategy_var.get().upper()
            try:
                match_threshold = float(self.match_threshold_var.get())
                # Clamp threshold to valid range
                match_threshold = max(0.0, min(1.0, match_threshold))
            except ValueError:
                match_threshold = 0.7  # Default if invalid

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
                    fuzzy_matching=fuzzy_matching,           # fuzzy
                    match_threshold=match_threshold,         # fuzzy
                    log_level=log_level,  # None if logging disabled
                    log_file=log_file,     # None if logging disabled
                    console_output=False,  # Never output to console
                    overwrite_log=self.overwrite_log_var.get(),  #overwrite logfile     
                    progress_callback=self.update_progress     
                )
                
                
            # Show duplicate warnings if any -- removed messagebox - log instead
            #if duplicate_warnings:
                #logger.info(f"Duplicate eids automatically resolved in: {', '.join(duplicate_warnings)}")
                #info_msg = f"Duplicate eids detected in: {', '.join(duplicate_warnings)}\n\nEids were automatically renamed and system lock references were updated.\n\nAll system locks have been preserved."
                #messagebox.showinfo("EIDs Updated", info_msg)
     
            self.status.set("Done!")
            self.progress.pack_forget()  # Hide progress bar when done
            messagebox.showinfo("Success", f"Files concatenated into:\n{output}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"An error occurred:\n{e}")
            self.status.set("Error")
            self.progress.pack_forget()  # Hide progress bar on error

    def update_progress(self, current, total):
        """Callback function to update progress bar"""
        self.progress['value'] = current
        self.status.set(f"Processing file {current}/{total}")
        self.root.update_idletasks()  # Keep GUI responsive
            
    def toggle_logging_options(self):
                """Show/hide logging options based on checkbox state"""
                if self.enable_logging_var.get():
                    self.logging_options_frame.pack(fill="x", padx=10, pady=5)
                else:
                    self.logging_options_frame.pack_forget()                  

    # -------------------------------------------------------------------------
    # About dialog
    # -------------------------------------------------------------------------
    def show_about(self):
        about = tk.Toplevel(self.root)
        about.title("About MuseScore Concatenator")
        about.geometry("400x275")
        about.resizable(False, False)

        tk.Label(about, text="MuseScore Concatenator", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(about, text="Version 1.5 (20251031)", font=("Arial", 11)).pack(pady=2)
        tk.Label(about, text="© 2025 Diego Denolf", font=("Arial", 10)).pack(pady=2)
        
        msg = (
            "Source: https://github.com/diedeno/mscz-concatenator\n" 
            "Based on the mscore library and script © 2025 Leon Dionne https://github.com/Zen-Master-SoSo/mscore\n"
            
            "Licensed under the GNU GPL v3."
        )
        tk.Label(about, text=msg, wraplength=360, justify="left").pack(padx=15, pady=10)

        tk.Button(about, text="Close", command=about.destroy).pack(pady=5)




if __name__ == "__main__":
    root = tk.Tk()
    app = ConcatenateGUI(root)
    root.mainloop()
