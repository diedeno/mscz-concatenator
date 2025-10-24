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
import ms_concatenate  # must be in the same folder or installed as a module


class ConcatenateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MuseScore Concatenator v1.4")
        self.files = []

        # --- File Management ---
        file_frame = tk.LabelFrame(root, text="File Management", padx=10, pady=5)
        file_frame.pack(padx=10, pady=5, fill="x")

        # Input files listbox with scrollbars
        frame_list = tk.Frame(file_frame)
        frame_list.pack(padx=5, pady=5, fill="both", expand=True)

        self.listbox = tk.Listbox(frame_list, width=60, height=10, selectmode=tk.EXTENDED)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        vscroll = tk.Scrollbar(frame_list, orient="vertical", command=self.listbox.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll = tk.Scrollbar(frame_list, orient="horizontal", command=self.listbox.xview)
        hscroll.grid(row=1, column=0, sticky="ew")

        self.listbox.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        frame_list.grid_rowconfigure(0, weight=1)
        frame_list.grid_columnconfigure(0, weight=1)

        # Buttons for managing file list
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add Files", command=self.add_files).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Move Up", command=self.move_up).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Move Down", command=self.move_down).grid(row=0, column=4, padx=5)

        # Skip incompatible files option (right under file buttons)
        self.skip_incompatible_var = tk.BooleanVar(value=False)
        tk.Checkbutton(file_frame, text="Skip files with incompatible instrumentation", 
                       variable=self.skip_incompatible_var).pack(anchor="w", pady=2)

        # --- Logging Options ---
        logging_frame = tk.LabelFrame(root, text="Logging Options", padx=10, pady=5)
        logging_frame.pack(padx=10, pady=5, fill="x")

        # Enable logging checkbox
        self.enable_logging_var = tk.BooleanVar(value=False)
        tk.Checkbutton(logging_frame, text="Enable logging", 
                       variable=self.enable_logging_var,
                       command=self.toggle_logging_options).pack(anchor="w", pady=2)

        # Logging options frame (only shown when logging is enabled)
        self.logging_options_frame = tk.Frame(logging_frame)

        # Log level
        log_level_frame = tk.Frame(self.logging_options_frame)
        log_level_frame.pack(fill="x", pady=2)

        tk.Label(log_level_frame, text="Log Level:").pack(side="left", padx=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_menu = tk.OptionMenu(log_level_frame, self.log_level_var, "WARN", "INFO", "DEBUG")
        log_level_menu.pack(side="left", padx=5)

        # Info text about default log location         
        info_text = "Default: mscz-cat.log - WARN: Skipped files only | INFO: Basic details | DEBUG: All details"
        info_label = tk.Label(
            log_level_frame, 
            text=info_text,
            fg="gray",
            font=("Arial", 8)
        )
        info_label.pack(side="left", padx=10)
        
        # overwrite logfiles?
        self.overwrite_log_var = tk.BooleanVar(value=False)
        self.overwrite_cb = tk.Checkbutton(
            self.logging_options_frame, 
            text="Overwrite log file (instead of appending)", 
            variable=self.overwrite_log_var
        )
        self.overwrite_cb.pack(anchor="w", pady=2)

        # Custom log file location checkbox
        self.custom_log_location_var = tk.BooleanVar(value=False)
        self.custom_log_cb = tk.Checkbutton(
            self.logging_options_frame, 
            text="Use custom log file location", 
            variable=self.custom_log_location_var,
            command=self.toggle_custom_log_location
        )
        self.custom_log_cb.pack(anchor="w", pady=2)

        # Log file location (hidden by default)
        self.log_file_frame = tk.Frame(self.logging_options_frame)

        tk.Label(self.log_file_frame, text="Log file:").pack(side="left", padx=5)
        self.log_file_var = tk.StringVar()
        self.log_file_entry = tk.Entry(self.log_file_frame, textvariable=self.log_file_var, width=30)
        self.log_file_entry.pack(side="left", padx=5)
        tk.Button(self.log_file_frame, text="Browse", command=self.select_log_file).pack(side="left", padx=5)

        # Initially hide everything
        self.logging_options_frame.pack_forget()
        self.log_file_frame.pack_forget()  
        
             
        # --- Content copying options ---
        options_frame = tk.LabelFrame(root, text="Content Copying Options for Subsequent Scores", padx=10, pady=5)
        options_frame.pack(padx=10, pady=5, fill="x")

        # Copy frames option
        self.copy_frames_var = tk.BooleanVar(value=True)
        self.copy_frames_cb = tk.Checkbutton(
            options_frame, 
            text="Copy frames from subsequent scores", 
            variable=self.copy_frames_var,
            command=self.toggle_title_frames_option
        )
        self.copy_frames_cb.grid(row=0, column=0, sticky="w", pady=2)

        # Copy title frames option (only enabled when copy_frames is True)
        self.copy_title_frames_var = tk.BooleanVar(value=True)
        self.copy_title_frames_cb = tk.Checkbutton(
            options_frame, 
            text="Copy title frames from subsequent scores", 
            variable=self.copy_title_frames_var
        )
        self.copy_title_frames_cb.grid(row=1, column=0, sticky="w", padx=20, pady=2)

        # Copy system locks option
        self.copy_system_locks_var = tk.BooleanVar(value=True)
        self.copy_system_locks_cb = tk.Checkbutton(
            options_frame, 
            text="Copy system locks from subsequent scores", 
            variable=self.copy_system_locks_var
        )
        self.copy_system_locks_cb.grid(row=2, column=0, sticky="w", pady=2)
        
        # Copy pictures option
        self.copy_pictures_var = tk.BooleanVar(value=True)
        self.copy_pictures_cb = tk.Checkbutton(
            options_frame, 
            text="Copy embedded pictures from subsequent scores", 
            variable=self.copy_pictures_var
        )
        self.copy_pictures_cb.grid(row=3, column=0, sticky="w", pady=2)

        # --- Layout Break Options ---
        break_frame = tk.LabelFrame(root, text="Add Layout Break Between Scores", padx=10, pady=5)
        break_frame.pack(padx=10, pady=5, fill="x")

        # Break type selection - checkboxes with mutual exclusion
        break_type_frame = tk.Frame(break_frame)
        break_type_frame.pack(fill="x", pady=5)

        self.break_system_var = tk.BooleanVar(value=False)
        self.break_page_var = tk.BooleanVar(value=False)
        self.break_section_var = tk.BooleanVar(value=False)

        def on_system_break_change(*args):
            if self.break_system_var.get():
                # System break means same page, so uncheck page break (contradictory)
                self.break_page_var.set(False)
                # System and section are mutually exclusive
                self.break_section_var.set(False)
                # Show system break info
                self.system_info_frame.pack(fill="x", padx=10, pady=5)
            else:
                # Hide system break info
                self.system_info_frame.pack_forget()

        def on_page_break_change(*args):
            if self.break_page_var.get():
                # Page break implies system break, so uncheck system break to avoid redundancy
                self.break_system_var.set(False)
                # Hide system break info if it was showing
                self.system_info_frame.pack_forget()

        def on_section_break_change(*args):
            if self.break_section_var.get():
                # Section and system are mutually exclusive
                self.break_system_var.set(False)
                # Section break can coexist with page break
                self.section_options_frame.pack(fill="x", padx=10, pady=5)
                # Hide system break info
                self.system_info_frame.pack_forget()
            else:
                self.section_options_frame.pack_forget()

        # Make sure all checkboxes trigger the mutual exclusion
        self.break_system_var.trace('w', on_system_break_change)
        self.break_page_var.trace('w', on_page_break_change) 
        self.break_section_var.trace('w', on_section_break_change)


        tk.Checkbutton(break_type_frame, text="System break", variable=self.break_system_var).pack(side="left", padx=10)
        tk.Checkbutton(break_type_frame, text="Page break", variable=self.break_page_var).pack(side="left", padx=10)
        tk.Checkbutton(break_type_frame, text="Section break", variable=self.break_section_var).pack(side="left", padx=10)
        
        # System break info frame (only shown when system break is selected)
        self.system_info_frame = tk.Frame(break_frame)
        self.system_info_frame.pack(fill="x", padx=10, pady=5)

        # System break info message
        system_info_label = tk.Label(
            self.system_info_frame, 
            text="Note: System breaks will not be added if there is a system lock in the measure",
            fg="blue",
            font=("Arial", 9)
        )
        system_info_label.pack(side="left", padx=5)

        # Initially hide system info
        self.system_info_frame.pack_forget()
        
 
        # Section break options frame (only shown when section break is selected)
        self.section_options_frame = tk.Frame(break_frame)
        # Don't pack it initially - it will be packed when section break is selected
        
        # Section break options frame (only shown when section break is selected)
        self.section_options_frame = tk.Frame(break_frame)
        self.section_options_frame.pack(fill="x", padx=10, pady=5)

        # Section break options in a compact grid
        self.section_pause_var = tk.StringVar(value="3")  # Default pause is 3 seconds
        self.start_long_names_var = tk.BooleanVar(value=True)
        self.start_measure_one_var = tk.BooleanVar(value=True)
        self.first_system_indent_var = tk.BooleanVar(value=True)
        self.show_courtesy_sig_var = tk.BooleanVar(value=True)  # Checked by default, same as MuseScore

        # First row: pause and repeat option
        row1 = tk.Frame(self.section_options_frame)
        row1.pack(fill="x", pady=2)

        tk.Label(row1, text="Pause (seconds):").pack(side="left", padx=5)
        self.pause_entry = tk.Entry(row1, textvariable=self.section_pause_var, width=4)
        self.pause_entry.pack(side="left", padx=5)

        # Add repeat detection option
        self.has_repeats_var = tk.BooleanVar(value=False)
        self.has_repeats_cb = tk.Checkbutton(
            row1, 
            text="Auto-set pause=0 for files with repeats", 
            variable=self.has_repeats_var,
            command=self.on_repeat_checkbox_change
        )
        self.has_repeats_cb.pack(side="left", padx=15)

        # Second row: checkboxes with better labels
        row2 = tk.Frame(self.section_options_frame)
        row2.pack(fill="x", pady=2)

        tk.Checkbutton(row2, text="Start with long instrument names", variable=self.start_long_names_var).pack(side="left", padx=5)
        tk.Checkbutton(row2, text="Reset measure numbers", variable=self.start_measure_one_var).pack(side="left", padx=15)

        # Third row: remaining checkbox
        row3 = tk.Frame(self.section_options_frame)
        row3.pack(fill="x", pady=2)

        tk.Checkbutton(row3, text="Indent first system", variable=self.first_system_indent_var).pack(side="left", padx=5)
        tk.Checkbutton(row3, text="Hide courtesy clefs and signatures", variable=self.show_courtesy_sig_var).pack(side="left", padx=15)


        # Initially hide section options
        self.section_options_frame.pack_forget()

  
        # Update the toggle method name and logic
        def toggle_frame_options(self):
            """Enable/disable the frame options based on copy_frames state"""
            if self.copy_frames_var.get():
                self.copy_title_frames_cb.config(state="normal")
            else:
                self.copy_title_frames_cb.config(state="disabled")
                self.copy_title_frames_var.set(False)  # Auto-uncheck when frames are disabled
                self.copy_title_frames_cb.grid(row=1, column=0, sticky="w", padx=20, pady=2)

              
                      

        # --- Output file selector ---
        out_frame = tk.Frame(root)
        out_frame.pack(pady=5, fill="x")

        tk.Label(out_frame, text="Output File:").pack(side="left", padx=5)
        self.output_entry = tk.Entry(out_frame, width=40)
        self.output_entry.pack(side="left", padx=5)
        tk.Button(out_frame, text="Browse", command=self.select_output).pack(side="left", padx=5)

        # --- Run and About buttons ---
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="Concatenate", command=self.run).pack(side="left", padx=10)
        tk.Button(bottom_frame, text="About", command=self.show_about).pack(side="left", padx=10)
        tk.Button(bottom_frame, text="Exit", command=self.root.quit).pack(side="left", padx=10)

        # --- Status ---
        self.status = tk.StringVar()
        self.status.set("Ready")
        tk.Label(root, textvariable=self.status, fg="blue").pack(pady=5)
        
        # --- Progress Bar ---
        self.progress = ttk.Progressbar(root, mode='determinate')
        self.progress.pack(pady=5, fill="x", padx=10)
        self.progress.pack_forget()  # Hide initially
        
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
                    log_level=log_level,  # None if logging disabled
                    log_file=log_file,     # None if logging disabled
                    console_output=False,  # Never output to console
                    overwrite_log=self.overwrite_log_var.get()  #overwrite logfile         
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
        tk.Label(about, text="Version 1.4 (20251023)", font=("Arial", 11)).pack(pady=2)
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
