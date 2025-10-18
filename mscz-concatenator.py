#!/usr/bin/python3
"""
GUI wrapper for ms-concatenate.py
---------------------------------
Provides a simple Tkinter interface to concatenate MuseScore files.
2025 Diego Denolf <graffesmusic@gmail.com>
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import traceback
import ms_concatenate  # must be in the same folder or installed as a module


class ConcatenateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MuseScore Concatenator v1.2")
        self.files = []

        # --- Input files listbox with scrollbars ---
        frame_list = tk.Frame(root)
        frame_list.pack(padx=10, pady=5, fill="both", expand=True)

        self.listbox = tk.Listbox(frame_list, width=60, height=10, selectmode=tk.SINGLE)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        vscroll = tk.Scrollbar(frame_list, orient="vertical", command=self.listbox.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll = tk.Scrollbar(frame_list, orient="horizontal", command=self.listbox.xview)
        hscroll.grid(row=1, column=0, sticky="ew")

        self.listbox.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        frame_list.grid_rowconfigure(0, weight=1)
        frame_list.grid_columnconfigure(0, weight=1)

        # --- Buttons for managing file list ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add Files", command=self.add_files).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Move Up", command=self.move_up).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Move Down", command=self.move_down).grid(row=0, column=4, padx=5)

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

    def select_output(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".mscz",
            filetypes=[("MuseScore compressed", "*.mscz")]
        )
        if f:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, f)

    def remove_selected(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.files.pop(idx)
            self.listbox.delete(idx)

    def clear_all(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)

    # -------------------------------------------------------------------------
    # List reordering
    # -------------------------------------------------------------------------
    def move_up(self):
        sel = self.listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            self.files[idx-1], self.files[idx] = self.files[idx], self.files[idx-1]
            self.refresh_listbox(idx-1)

    def move_down(self):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.files)-1:
            idx = sel[0]
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
        if not self.files:
            messagebox.showerror("Error", "No input files selected")
            return
        output = self.output_entry.get().strip()
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

            # Get the frame copying options
            copy_frames = self.copy_frames_var.get()
            copy_title_frames = self.copy_title_frames_var.get() if copy_frames else False
            copy_system_locks = self.copy_system_locks_var.get()

            # Call the concatenate function with progress updates
            success, duplicate_warnings = ms_concatenate.concatenate(
                self.files, 
                output, 
                copy_frames=copy_frames,
                copy_title_frames=copy_title_frames,
                copy_system_locks=copy_system_locks,
                verbose=False,
                progress_callback=self.update_progress
            )
      
            # Show duplicate warnings if any
            if duplicate_warnings:
                warning_msg = f"Duplicate eids detected in: {', '.join(duplicate_warnings)}\n\nSystem locks from these files were skipped.\n\nTarget file has unique eids - you can add system locks manually if needed."
                messagebox.showwarning("Duplicate EIDs", warning_msg)
     
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

    # -------------------------------------------------------------------------
    # About dialog
    # -------------------------------------------------------------------------
    def show_about(self):
        about = tk.Toplevel(self.root)
        about.title("About MuseScore Concatenator")
        about.geometry("400x275")
        about.resizable(False, False)

        tk.Label(about, text="MuseScore Concatenator", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(about, text="Version 1.2", font=("Arial", 11)).pack(pady=2)
        tk.Label(about, text="© 2025 Diego Denolf", font=("Arial", 10)).pack(pady=2)
        tk.Label(about, text="Based on the mscore script and library © 2025 Leon Dionne", font=("Arial", 10)).pack(pady=2)

        msg = (
            "Source: https://github.com/diedeno/mscz-concatenator\n" 
            "Original code from https://github.com/Zen-Master-SoSo/mscore\n"
            
            "Licensed under the GNU GPL v3."
        )
        tk.Label(about, text=msg, wraplength=360, justify="left").pack(padx=15, pady=10)

        tk.Button(about, text="Close", command=about.destroy).pack(pady=5)




if __name__ == "__main__":
    root = tk.Tk()
    app = ConcatenateGUI(root)
    root.mainloop()
