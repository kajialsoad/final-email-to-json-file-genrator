#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail OAuth Client JSON Generator
স্বয়ংক্রিয় জিমেইল OAuth ক্লায়েন্ট জেনারেটর

এই অ্যাপ্লিকেশনটি ব্যবহারকারীর কাছ থেকে ইমেল এবং পাসওয়ার্ড নিয়ে
স্বয়ংক্রিয়ভাবে Google Cloud Console এ OAuth ক্লায়েন্ট তৈরি করে
এবং JSON ফাইল হিসেবে আউটপুট দেয়।
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import threading
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class GmailOAuthGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Gmail OAuth Client JSON Generator")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Variables
        self.selected_file = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready to start...")
        
        # Create output directory
        self.output_dir = "output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Log display variables
        self.log_text = None
            
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.root.title("Gmail OAuth Client JSON Generator")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        self.root.configure(bg='#f8f9fa')
        
        # Set minimum window size
        self.root.minsize(800, 700)
        
        # Create main canvas and scrollbar for scrollable content
        canvas = tk.Canvas(self.root, bg='#f8f9fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f8f9fa')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=2)
        scrollbar.pack(side="right", fill="y")
        
        # Add mouse wheel scrolling support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Use scrollable_frame as main container instead of self.root
        main_container = scrollable_frame
        
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles with professional colors
        style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'), 
                       foreground='#1a365d', background='#f8f9fa')
        style.configure('Heading.TLabel', font=('Segoe UI', 13, 'bold'), 
                       foreground='#2d3748', background='#ffffff')
        style.configure('Modern.TButton', font=('Segoe UI', 11, 'bold'),
                       padding=(25, 12))
        style.configure('Browse.TButton', font=('Segoe UI', 10),
                       padding=(12, 8))
        
        # Configure progress bar style
        style.configure('Professional.Horizontal.TProgressbar',
                       background='#4299e1',
                       troughcolor='#e2e8f0',
                       borderwidth=0,
                       lightcolor='#4299e1',
                       darkcolor='#4299e1')
        
        # Main container with modern styling (now using scrollable_frame)
        main_container.configure(bg='#f8f9fa')
        
        # Create content frame with enhanced padding
        content_frame = tk.Frame(main_container, bg='#f8f9fa')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=35)
        
        # Header section with professional gradient-like effect
        header_frame = tk.Frame(content_frame, bg='#ffffff', relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Add subtle shadow effect with multiple frames
        shadow_frame = tk.Frame(content_frame, bg='#e2e8f0', height=2)
        shadow_frame.pack(fill=tk.X, pady=(0, 28))
        
        # Professional title with enhanced styling
        title_label = tk.Label(header_frame, text="Gmail OAuth Client JSON Generator", 
                              font=('Segoe UI', 22, 'bold'), fg='#1a365d', bg='#ffffff')
        title_label.pack(pady=25)
        
        # Subtitle for better hierarchy
        subtitle_label = tk.Label(header_frame, text="Automated OAuth Client JSON File Generator", 
                                 font=('Segoe UI', 11), fg='#4a5568', bg='#ffffff')
        subtitle_label.pack(pady=(0, 20))
        
        # File selection section with enhanced card design
        file_section = tk.LabelFrame(content_frame, text="📁 File Selection", 
                                   font=('Segoe UI', 13, 'bold'), fg='#2d3748',
                                   bg='#ffffff', relief=tk.FLAT, bd=0, padx=25, pady=20)
        file_section.pack(fill=tk.X, pady=(0, 25))
        
        # Add card shadow effect
        file_section.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        accounts_label = tk.Label(file_section, text="Select Account File:", 
                                 font=('Segoe UI', 11, 'bold'), fg='#2d3748', bg='#ffffff')
        accounts_label.grid(row=0, column=0, sticky=tk.W, pady=(8, 15))
        
        file_frame = tk.Frame(file_section, bg='#ffffff')
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        file_section.columnconfigure(0, weight=1)
        
        # Enhanced file entry with better styling
        file_entry = tk.Entry(file_frame, textvariable=self.selected_file, 
                             font=('Segoe UI', 11), width=55, relief=tk.FLAT, bd=0, 
                             state="readonly", bg='#f7fafc', fg='#2d3748',
                             highlightbackground='#cbd5e0', highlightthickness=1)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15), ipady=8)
        
        # Enhanced browse button
        browse_button = tk.Button(file_frame, text="📂 Browse", command=self.browse_file,
                                 font=('Segoe UI', 10, 'bold'), bg='#4299e1', fg='white',
                                 relief=tk.FLAT, padx=20, pady=10, cursor='hand2',
                                 activebackground='#3182ce', activeforeground='white')
        browse_button.pack(side=tk.RIGHT)
        
        # Single Account section with enhanced card design
        single_section = tk.LabelFrame(content_frame, text="👤 Single Account Generator", 
                                     font=('Segoe UI', 13, 'bold'), fg='#2d3748',
                                     bg='#ffffff', relief=tk.FLAT, bd=0, padx=25, pady=20)
        single_section.pack(fill=tk.X, pady=(0, 25))
        
        # Add card shadow effect
        single_section.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        # Variables for single account inputs
        self.single_email = tk.StringVar()
        self.single_password = tk.StringVar()
        
        # Email input
        email_label = tk.Label(single_section, text="Email Address:", 
                              font=('Segoe UI', 11, 'bold'), fg='#2d3748', bg='#ffffff')
        email_label.grid(row=0, column=0, sticky=tk.W, pady=(8, 5), padx=(0, 10))
        
        email_entry = tk.Entry(single_section, textvariable=self.single_email, 
                              font=('Segoe UI', 11), width=40, relief=tk.FLAT, bd=0, 
                              bg='#f7fafc', fg='#2d3748',
                              highlightbackground='#cbd5e0', highlightthickness=1)
        email_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(8, 5), padx=(0, 15), ipady=8)
        
        # Password input
        password_label = tk.Label(single_section, text="Password:", 
                                 font=('Segoe UI', 11, 'bold'), fg='#2d3748', bg='#ffffff')
        password_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 15), padx=(0, 10))
        
        password_entry = tk.Entry(single_section, textvariable=self.single_password, 
                                 font=('Segoe UI', 11), width=40, relief=tk.FLAT, bd=0, 
                                 bg='#f7fafc', fg='#2d3748', show='*',
                                 highlightbackground='#cbd5e0', highlightthickness=1)
        password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 15), padx=(0, 15), ipady=8)
        
        # Configure grid weights
        single_section.columnconfigure(1, weight=1)
        
        # Generate button for single account
        single_generate_btn = tk.Button(single_section, text="🚀 Generate Single JSON", 
                                       command=self.start_single_generation,
                                       font=('Segoe UI', 11, 'bold'), bg='#9f7aea', fg='white',
                                       relief=tk.FLAT, bd=0, padx=25, pady=12, cursor='hand2',
                                       activebackground='#805ad5', activeforeground='white')
        single_generate_btn.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Store reference to single generate button
        self.single_generate_btn = single_generate_btn
        
        # Instructions section with enhanced card design
        instructions_section = tk.LabelFrame(content_frame, text="📋 Instructions", 
                                           font=('Segoe UI', 13, 'bold'), fg='#2d3748',
                                           bg='#ffffff', relief=tk.FLAT, bd=0, padx=25, pady=20)
        instructions_section.pack(fill=tk.X, pady=(0, 25))
        
        # Add card shadow effect
        instructions_section.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        instructions_text = (
            "1. Add accounts in email:password format (one per line) in the selected file\n"
            "2. Click the 'Generate OAuth Credentials' button to start the process\n"
            "3. Complete 2FA verification when prompted during automation\n"
            "4. Generated JSON files will be saved in the output folder"
        )
        
        # Enhanced instructions display with better styling
        instructions_display = tk.Text(instructions_section, height=4, width=75, wrap=tk.WORD,
                                     font=('Segoe UI', 10), bg='#f7fafc', relief=tk.FLAT, bd=0,
                                     fg='#4a5568', highlightbackground='#cbd5e0', highlightthickness=1,
                                     padx=15, pady=10, selectbackground='#bee3f8')
        instructions_display.insert(tk.END, instructions_text)
        instructions_display.config(state=tk.DISABLED)
        instructions_display.pack(fill=tk.X, pady=(10, 5))
        
        # Progress section with enhanced card design
        progress_section = tk.LabelFrame(content_frame, text="⚡ Progress Status", 
                                       font=('Segoe UI', 13, 'bold'), fg='#2d3748',
                                       bg='#ffffff', relief=tk.FLAT, bd=0, padx=25, pady=20)
        progress_section.pack(fill=tk.X, pady=(0, 25))
        
        # Add card shadow effect
        progress_section.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        # Enhanced status display with better styling
        status_display = tk.Label(progress_section, textvariable=self.status_var,
                                   font=('Segoe UI', 11), fg='#2d3748', bg='#ffffff',
                                   wraplength=600, justify=tk.LEFT)
        status_display.pack(pady=(10, 15))
        
        # Professional progress bar with custom styling
        self.progress_bar = ttk.Progressbar(progress_section, variable=self.progress_var,
                                          maximum=100, length=600, 
                                          style='Professional.Horizontal.TProgressbar')
        self.progress_bar.pack(pady=(0, 15))
        
        # Actions section with professional card design
        actions_section = tk.LabelFrame(content_frame, text="🎯 Actions", 
                                       font=('Segoe UI', 13, 'bold'), fg='#2d3748',
                                       bg='#ffffff', relief=tk.FLAT, bd=0, padx=25, pady=25)
        actions_section.pack(fill=tk.X, pady=(0, 30))
        
        # Add card shadow effect
        actions_section.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        # Create a centered container for buttons with professional spacing
        button_container = tk.Frame(actions_section, bg='#ffffff')
        button_container.pack(pady=(15, 20))
        
        # Generate JSON Files button with professional styling
        self.generate_btn = tk.Button(button_container, text="🚀 Generate JSON Files", 
                                        command=self.start_generation,
                                        font=('Segoe UI', 12, 'bold'), bg='#48bb78', fg='white',
                                        relief=tk.FLAT, bd=0, padx=35, pady=15, cursor='hand2',
                                        activebackground='#38a169', activeforeground='white')
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 25))
        
        # Open Output Folder button with professional styling
        open_output_btn = tk.Button(button_container, text="📁 Open Output Folder", 
                                 command=self.open_output_folder,
                                 font=('Segoe UI', 12, 'bold'), bg='#ed8936', fg='white',
                                 relief=tk.FLAT, bd=0, padx=30, pady=15, cursor='hand2',
                                 activebackground='#dd6b20', activeforeground='white')
        open_output_btn.pack(side=tk.LEFT, padx=(0, 25))
        
        # Open Report Folder button with professional styling
        open_report_btn = tk.Button(button_container, text="📊 Open Report Folder", 
                                   command=self.open_report_folder,
                                   font=('Segoe UI', 12, 'bold'), bg='#667eea', fg='white',
                                   relief=tk.FLAT, bd=0, padx=30, pady=15, cursor='hand2',
                                   activebackground='#5a67d8', activeforeground='white')
        open_report_btn.pack(side=tk.LEFT)
        
        # Add professional hover effects with smooth transitions
        self.add_hover_effects(browse_button, '#3182ce', '#4299e1')
        self.add_hover_effects(self.generate_btn, '#38a169', '#48bb78')
        self.add_hover_effects(open_output_btn, '#dd6b20', '#ed8936')
        self.add_hover_effects(open_report_btn, '#5a67d8', '#667eea')
        self.add_hover_effects(self.single_generate_btn, '#805ad5', '#9f7aea')
        
        # Report Options section with enhanced card design
        report_section = tk.LabelFrame(content_frame, text="📊 Report Options", 
                                      font=('Segoe UI', 13, 'bold'), fg='#2d3748',
                                      bg='#ffffff', relief=tk.FLAT, bd=0, padx=25, pady=20)
        report_section.pack(fill=tk.X, pady=(0, 15))
        
        # Add card shadow effect
        report_section.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        # Create report buttons frame
        report_buttons_frame = tk.Frame(report_section, bg='#ffffff')
        report_buttons_frame.pack(pady=(10, 15))
        
        # Report buttons with professional styling
        self.captcha_btn = tk.Button(report_buttons_frame, text="🤖 I am not robot", 
                                    command=lambda: self.show_report_dialog("captcha"),
                                    font=('Segoe UI', 10, 'bold'), bg='#f56565', fg='white',
                                    relief=tk.FLAT, bd=0, padx=15, pady=8, cursor='hand2',
                                    activebackground='#e53e3e', activeforeground='white')
        self.captcha_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.error_btn = tk.Button(report_buttons_frame, text="❌ General Error", 
                                  command=lambda: self.show_report_dialog("error"),
                                  font=('Segoe UI', 10, 'bold'), bg='#ed8936', fg='white',
                                  relief=tk.FLAT, bd=0, padx=15, pady=8, cursor='hand2',
                                  activebackground='#dd6b20', activeforeground='white')
        self.error_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.password_btn = tk.Button(report_buttons_frame, text="🔐 Wrong Password", 
                                     command=lambda: self.show_report_dialog("password"),
                                     font=('Segoe UI', 10, 'bold'), bg='#9f7aea', fg='white',
                                     relief=tk.FLAT, bd=0, padx=15, pady=8, cursor='hand2',
                                     activebackground='#805ad5', activeforeground='white')
        self.password_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.verification_btn = tk.Button(report_buttons_frame, text="📧 Verification Email", 
                                         command=lambda: self.show_report_dialog("verification"),
                                         font=('Segoe UI', 10, 'bold'), bg='#38b2ac', fg='white',
                                         relief=tk.FLAT, bd=0, padx=15, pady=8, cursor='hand2',
                                         activebackground='#319795', activeforeground='white')
        self.verification_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_btn = tk.Button(report_buttons_frame, text="📋 Export Report", 
                                   command=self.export_report,
                                   font=('Segoe UI', 10, 'bold'), bg='#4299e1', fg='white',
                                   relief=tk.FLAT, bd=0, padx=15, pady=8, cursor='hand2',
                                   activebackground='#3182ce', activeforeground='white')
        self.export_btn.pack(side=tk.LEFT)
        
        # Add hover effects to report buttons
        self.add_hover_effects(self.captcha_btn, '#e53e3e', '#f56565')
        self.add_hover_effects(self.error_btn, '#dd6b20', '#ed8936')
        self.add_hover_effects(self.password_btn, '#805ad5', '#9f7aea')
        self.add_hover_effects(self.verification_btn, '#319795', '#38b2ac')
        self.add_hover_effects(self.export_btn, '#3182ce', '#4299e1')
        
        # Status indicators frame
        status_indicators_frame = tk.Frame(report_section, bg='#ffffff')
        status_indicators_frame.pack(pady=(0, 10))
        
        # Status indicators
        self.captcha_status = tk.Label(status_indicators_frame, text="🤖 Captcha: Not Detected", 
                                      font=('Segoe UI', 9), fg='#48bb78', bg='#ffffff')
        self.captcha_status.pack(side=tk.LEFT, padx=(0, 20))
        
        self.error_status = tk.Label(status_indicators_frame, text="❌ Errors: 0", 
                                    font=('Segoe UI', 9), fg='#48bb78', bg='#ffffff')
        self.error_status.pack(side=tk.LEFT, padx=(0, 20))
        
        self.verification_status = tk.Label(status_indicators_frame, text="📧 Verification: Not Required", 
                                           font=('Segoe UI', 9), fg='#48bb78', bg='#ffffff')
        self.verification_status.pack(side=tk.LEFT)
        
        # Initialize report counters
        self.report_data = {
            'captcha_count': 0,
            'error_count': 0,
            'password_error_count': 0,
            'verification_count': 0,
            'reports': []
        }
        
        # Log Display section with enhanced card design
        log_section = tk.LabelFrame(content_frame, text="📋 Process Log", 
                                   font=('Segoe UI', 13, 'bold'), fg='#2d3748',
                                   bg='#ffffff', relief=tk.FLAT, bd=0, padx=25, pady=20)
        log_section.pack(fill=tk.BOTH, expand=True, pady=(0, 25))
        
        # Add card shadow effect
        log_section.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        # Create frame for log text and scrollbar
        log_frame = tk.Frame(log_section, bg='#ffffff')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 15))
        
        # Create scrollable text widget for logs
        self.log_text = tk.Text(log_frame, height=12, wrap=tk.WORD,
                               font=('Consolas', 10), bg='#1a202c', fg='#e2e8f0',
                               relief=tk.FLAT, bd=0, padx=15, pady=10,
                               selectbackground='#4a5568', insertbackground='#e2e8f0')
        
        # Create scrollbar for log text
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Pack log text and scrollbar
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # Clear log button
        clear_log_btn = tk.Button(log_section, text="🗑️ Clear Log", 
                                 command=self.clear_log,
                                 font=('Segoe UI', 10, 'bold'), bg='#e53e3e', fg='white',
                                 relief=tk.FLAT, bd=0, padx=20, pady=8, cursor='hand2',
                                 activebackground='#c53030', activeforeground='white')
        clear_log_btn.pack(pady=(0, 10))
        
        # Add hover effect to clear button
        self.add_hover_effects(clear_log_btn, '#c53030', '#e53e3e')
        
        # Initialize log with welcome message
        self.log_message("📋 Gmail OAuth Client JSON Generator - Ready to start!", "INFO")
        self.log_message("💡 Select a file or enter single account details to begin.", "INFO")
        
        # Add bottom spacing for better visual balance
        bottom_spacer = tk.Frame(content_frame, bg='#f8f9fa', height=30)
        bottom_spacer.pack(fill=tk.X)
        
    def add_hover_effects(self, button, hover_color, normal_color):
        """Add hover effects to buttons"""
        def on_enter(e):
            button.config(bg=hover_color)
            
        def on_leave(e):
            button.config(bg=normal_color)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
    def log_message(self, message, level="INFO"):
        """Add a message to the log display with timestamp"""
        if self.log_text is None:
            return
            
        timestamp = time.strftime("%H:%M:%S")
        
        # Color coding for different log levels
        colors = {
            "INFO": "#4299e1",    # Blue
            "SUCCESS": "#48bb78",  # Green
            "WARNING": "#ed8936",  # Orange
            "ERROR": "#e53e3e",    # Red
            "STEP": "#9f7aea"      # Purple
        }
        
        color = colors.get(level, "#e2e8f0")  # Default white
        
        # Configure text tags for colors
        self.log_text.tag_configure(level, foreground=color)
        
        # Insert the log message
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        self.log_text.insert(tk.END, log_entry, level)
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)
        
        # Update the UI
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log display"""
        if self.log_text is not None:
            self.log_text.delete(1.0, tk.END)
            self.log_message("📋 Log cleared - Ready for new operations!", "INFO")
    
    def show_report_dialog(self, report_type):
        """Show report dialog for different types of issues"""
        import tkinter.simpledialog as simpledialog
        import tkinter.messagebox as msgbox
        
        # Define report types and their details
        report_types = {
            "captcha": {
                "title": "🤖 Captcha Detection Report",
                "message": "Please describe the captcha challenge you encountered:",
                "status_text": "🤖 Captcha: Detected",
                "status_color": "#f56565"
            },
            "error": {
                "title": "❌ General Error Report",
                "message": "Please describe the error you encountered:",
                "status_text": "❌ Errors: {}",
                "status_color": "#ed8936"
            },
            "password": {
                "title": "🔐 Wrong Password Report",
                "message": "Please provide details about the password issue:",
                "status_text": "🔐 Password Errors: {}",
                "status_color": "#9f7aea"
            },
            "verification": {
                "title": "📧 Verification Email Report",
                "message": "Please describe the verification email issue:",
                "status_text": "📧 Verification: Required",
                "status_color": "#38b2ac"
            }
        }
        
        if report_type not in report_types:
            return
            
        report_info = report_types[report_type]
        
        # Show input dialog
        description = simpledialog.askstring(
            report_info["title"],
            report_info["message"],
            parent=self.root
        )
        
        if description:
            # Add to report data
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            report_entry = {
                "type": report_type,
                "description": description,
                "timestamp": timestamp,
                "email": getattr(self, 'current_processing_email', 'Unknown')
            }
            
            self.report_data['reports'].append(report_entry)
            
            # Update counters
            if report_type == "captcha":
                self.report_data['captcha_count'] += 1
                self.captcha_status.config(text=report_info["status_text"], fg=report_info["status_color"])
            elif report_type == "error":
                self.report_data['error_count'] += 1
                self.error_status.config(text=report_info["status_text"].format(self.report_data['error_count']), 
                                       fg=report_info["status_color"])
            elif report_type == "password":
                self.report_data['password_error_count'] += 1
                self.password_btn.config(text=f"🔐 Wrong Password ({self.report_data['password_error_count']})")
            elif report_type == "verification":
                self.report_data['verification_count'] += 1
                self.verification_status.config(text=report_info["status_text"], fg=report_info["status_color"])
            
            # Log the report
            self.log_message(f"📊 {report_info['title']}: {description}", "WARNING")
            
            # Show confirmation
            msgbox.showinfo("Report Saved", f"Your {report_type} report has been saved successfully!")
    
    def export_report(self):
        """Export comprehensive report to file"""
        import tkinter.filedialog as filedialog
        import json
        
        if not self.report_data['reports']:
            messagebox.showinfo("No Reports", "No reports to export. Please create some reports first.")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Prepare comprehensive report data
                export_data = {
                    "export_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": {
                        "total_reports": len(self.report_data['reports']),
                        "captcha_detections": self.report_data['captcha_count'],
                        "general_errors": self.report_data['error_count'],
                        "password_errors": self.report_data['password_error_count'],
                        "verification_requests": self.report_data['verification_count']
                    },
                    "detailed_reports": self.report_data['reports']
                }
                
                # Save to file
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    # Save as text file
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write("Gmail OAuth Automation Report\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Export Date: {export_data['export_timestamp']}\n\n")
                        
                        f.write("SUMMARY:\n")
                        f.write("-" * 20 + "\n")
                        for key, value in export_data['summary'].items():
                            f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                        
                        f.write("\n\nDETAILED REPORTS:\n")
                        f.write("-" * 30 + "\n")
                        for i, report in enumerate(export_data['detailed_reports'], 1):
                            f.write(f"\n{i}. {report['type'].upper()} REPORT\n")
                            f.write(f"   Email: {report['email']}\n")
                            f.write(f"   Time: {report['timestamp']}\n")
                            f.write(f"   Description: {report['description']}\n")
                
                self.log_message(f"📋 Report exported successfully to: {filename}", "SUCCESS")
                messagebox.showinfo("Export Successful", f"Report exported successfully to:\n{filename}")
                
            except Exception as e:
                self.log_message(f"❌ Failed to export report: {str(e)}", "ERROR")
                messagebox.showerror("Export Failed", f"Failed to export report:\n{str(e)}")
    
    def update_report_status(self, report_type, message=None):
        """Update report status indicators programmatically"""
        if report_type == "captcha_detected":
            self.report_data['captcha_count'] += 1
            self.captcha_status.config(text="🤖 Captcha: Detected", fg="#f56565")
            if message:
                self.log_message(f"🤖 Captcha detected: {message}", "WARNING")
        elif report_type == "error_occurred":
            self.report_data['error_count'] += 1
            self.error_status.config(text=f"❌ Errors: {self.report_data['error_count']}", fg="#ed8936")
            if message:
                self.log_message(f"❌ Error occurred: {message}", "ERROR")
        elif report_type == "password_failed":
            self.report_data['password_error_count'] += 1
            self.password_btn.config(text=f"🔐 Wrong Password ({self.report_data['password_error_count']})")
            if message:
                self.log_message(f"🔐 Password failed: {message}", "ERROR")
        elif report_type == "verification_required":
            self.report_data['verification_count'] += 1
            self.verification_status.config(text="📧 Verification: Required", fg="#38b2ac")
            if message:
                self.log_message(f"📧 Verification required: {message}", "WARNING")
        
    def browse_file(self):
        """Browse and select account file"""
        self.log_message("📂 Opening file browser...", "STEP")
        filename = filedialog.askopenfilename(
            title="Select Account File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.selected_file.set(filename)
            self.log_message(f"✅ File selected: {os.path.basename(filename)}", "SUCCESS")
        else:
            self.log_message("❌ No file selected", "WARNING")
            
    def open_output_folder(self):
        """Open output folder"""
        if os.path.exists(self.output_dir):
            os.startfile(self.output_dir)
        else:
            messagebox.showwarning("Warning", "Output folder not found!")
            
    def open_report_folder(self):
        """Open report folder to view all JSON files and automation reports"""
        try:
            if os.path.exists(self.output_dir):
                # Count JSON files
                json_files = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]
                txt_files = [f for f in os.listdir(self.output_dir) if f.endswith('.txt')]
                
                self.log_message(f"📁 Opening report folder: {self.output_dir}", "INFO")
                self.log_message(f"📊 Found {len(json_files)} JSON files and {len(txt_files)} report files", "INFO")
                
                # Open the folder
                os.startfile(self.output_dir)
                
                # Show summary dialog
                import tkinter.messagebox as msgbox
                summary_msg = f"Report Folder Contents:\n\n"
                summary_msg += f"📁 Location: {self.output_dir}\n\n"
                summary_msg += f"📄 JSON Files: {len(json_files)}\n"
                summary_msg += f"📋 Report Files: {len(txt_files)}\n\n"
                
                if json_files:
                    summary_msg += "Recent JSON Files:\n"
                    for i, file in enumerate(json_files[:5]):  # Show first 5 files
                        summary_msg += f"  • {file}\n"
                    if len(json_files) > 5:
                        summary_msg += f"  ... and {len(json_files) - 5} more files\n"
                        
                msgbox.showinfo("Report Folder", summary_msg)
                
            else:
                self.log_message("❌ Report folder not found! Creating output directory...", "WARNING")
                os.makedirs(self.output_dir, exist_ok=True)
                self.log_message(f"✅ Created output directory: {self.output_dir}", "SUCCESS")
                os.startfile(self.output_dir)
                messagebox.showinfo("Report Folder", f"Report folder created at:\n{self.output_dir}\n\nGenerate some OAuth files to see reports here!")
                
        except Exception as e:
            self.log_message(f"❌ Error opening report folder: {e}", "ERROR")
            messagebox.showerror("Error", f"Could not open report folder:\n{str(e)}")
            
    def start_generation(self):
        """Start OAuth client generation process"""
        if not self.selected_file.get():
            self.log_message("❌ No file selected! Please select a file first.", "ERROR")
            messagebox.showerror("Error", "Please select a file first!")
            return
            
        self.log_message("🚀 Starting batch OAuth client generation...", "STEP")
        self.log_message(f"📄 Processing file: {os.path.basename(self.selected_file.get())}", "INFO")
        
        # Disable generate button
        self.generate_btn.config(state="disabled")
        
        # Start generation in separate thread
        thread = threading.Thread(target=self.generate_oauth_clients)
        thread.daemon = True
        thread.start()
        
    def start_single_generation(self):
        """Start single account OAuth client generation process"""
        email = self.single_email.get().strip()
        password = self.single_password.get().strip()
        
        self.log_message("🔍 Validating single account input...", "STEP")
        
        # Validation
        if not email:
            self.log_message("❌ Email address is required!", "ERROR")
            messagebox.showerror("Error", "Please enter an email address!")
            return
            
        if not password:
            self.log_message("❌ Password is required!", "ERROR")
            messagebox.showerror("Error", "Please enter a password!")
            return
            
        if '@' not in email or '.' not in email.split('@')[1]:
            self.log_message(f"❌ Invalid email format: {email}", "ERROR")
            messagebox.showerror("Error", "Please enter a valid email address!")
            return
            
        self.log_message(f"✅ Validation passed for: {email}", "SUCCESS")
        self.log_message("🚀 Starting single account OAuth client generation...", "STEP")
        
        # Disable single generate button
        self.single_generate_btn.config(state="disabled")
        
        # Start generation in separate thread
        thread = threading.Thread(target=self.generate_single_oauth_client)
        thread.daemon = True
        thread.start()
        
    def read_accounts_file(self):
        """Read account information from file"""
        accounts = []
        self.log_message(f"📖 Reading accounts from file: {os.path.basename(self.selected_file.get())}", "STEP")
        try:
            with open(self.selected_file.get(), 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if line and ':' in line:
                        email, password = line.split(':', 1)
                        accounts.append({
                            'email': email.strip(),
                            'password': password.strip(),
                            'line_num': line_num
                        })
                    elif line:  # Non-empty line without colon
                        self.log_message(f"⚠️ Invalid format on line {line_num}: {line}", "WARNING")
                        self.status_var.set(f"Line {line_num}: Invalid format (email:password required)")
            self.log_message(f"✅ Successfully read {len(accounts)} accounts from file", "SUCCESS")        
        except Exception as e:
            self.log_message(f"❌ Error reading file: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error reading file: {str(e)}")
            return []
            
        return accounts
        
    def generate_oauth_clients(self):
        """Generate OAuth clients for each account"""
        accounts = self.read_accounts_file()
        
        if not accounts:
            self.log_message("❌ No valid accounts found in the file!", "ERROR")
            self.status_var.set("No valid accounts found!")
            self.generate_btn.config(state="normal")
            return
            
        total_accounts = len(accounts)
        successful = 0
        failed = 0
        
        self.log_message(f"🔄 Starting batch processing of {total_accounts} accounts...", "STEP")
        
        for i, account in enumerate(accounts):
            try:
                self.status_var.set(f"Processing: {account['email']} ({i+1}/{total_accounts})")
                self.log_message(f"🔄 Processing account {i+1}/{total_accounts}: {account['email']}", "STEP")
                
                # Generate OAuth client for this account
                success = self.create_oauth_client(account)
                
                if success:
                    successful += 1
                    self.status_var.set(f"Success: {account['email']}")
                    self.log_message(f"✅ Successfully processed: {account['email']}", "SUCCESS")
                else:
                    failed += 1
                    self.status_var.set(f"Failed: {account['email']}")
                    self.log_message(f"❌ Failed to process: {account['email']}", "ERROR")
                    
                # Update progress
                progress = ((i + 1) / total_accounts) * 100
                self.progress_var.set(progress)
                
                # Small delay between accounts
                time.sleep(1)
                
            except Exception as e:
                failed += 1
                self.status_var.set(f"Error: {account['email']} - {str(e)}")
                self.log_message(f"❌ Error processing {account['email']}: {str(e)}", "ERROR")
                
        # Final status
        self.status_var.set(f"Completed! Success: {successful}, Failed: {failed}")
        self.log_message(f"🎉 Batch processing completed! Success: {successful}, Failed: {failed}", "SUCCESS")
        self.generate_btn.config(state="normal")
        
        if successful > 0:
            messagebox.showinfo("Completed", 
                              f"JSON file generation completed!\n"
                              f"Success: {successful}\n"
                              f"Failed: {failed}\n\n"
                              f"Files saved in '{self.output_dir}' folder.")
                              
    def generate_single_oauth_client(self):
        """Generate OAuth client for single account"""
        try:
            # Create account object
            account = {
                'email': self.single_email.get().strip(),
                'password': self.single_password.get().strip(),
                'line_num': 1
            }
            
            self.status_var.set(f"Processing single account: {account['email']}")
            self.progress_var.set(0)
            
            # Generate OAuth client for this account
            success = self.create_oauth_client(account)
            
            if success:
                self.status_var.set(f"Success: Single JSON generated for {account['email']}")
                self.progress_var.set(100)
                messagebox.showinfo("Success", 
                                  f"JSON file generated successfully!\n"
                                  f"Email: {account['email']}\n\n"
                                  f"File saved in '{self.output_dir}' folder.")
                # Clear input fields after successful generation
                self.single_email.set("")
                self.single_password.set("")
            else:
                self.status_var.set(f"Failed: Single JSON generation failed for {account['email']}")
                messagebox.showerror("Error", 
                                   f"Failed to generate JSON file for {account['email']}\n"
                                   f"Please check the credentials and try again.")
                
        except Exception as e:
            self.status_var.set(f"Error: Single account generation - {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Re-enable single generate button
            self.single_generate_btn.config(state="normal")
            
    def create_oauth_client(self, account):
        """Create OAuth client for a single account"""
        try:
            # Set current processing email for report tracking
            self.current_processing_email = account['email']
            
            self.log_message(f"🔄 Starting OAuth client creation for: {account['email']}", "STEP")
            result = self.setup_selenium_automation(account)
            if result:
                self.log_message(f"✅ OAuth client created successfully for: {account['email']}", "SUCCESS")
            else:
                self.log_message(f"❌ OAuth client creation failed for: {account['email']}", "ERROR")
                # Update error status
                self.update_report_status("error_occurred", f"OAuth client creation failed for {account['email']}")
            return result
            
        except Exception as e:
            error_msg = f"Error creating OAuth client for {account['email']}: {str(e)}"
            print(error_msg)
            self.log_message(f"❌ {error_msg}", "ERROR")
            # Update error status
            self.update_report_status("error_occurred", error_msg)
            return False
            
    def setup_selenium_automation(self, account):
        """Selenium automation for Google Cloud Console"""
        driver = None
        try:
            # Chrome options setup with anti-detection measures
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            # chrome_options.add_argument('--headless')  # Uncomment for headless mode
            
            # Initialize WebDriver
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            self.log_message("🚀 Initializing Chrome WebDriver...", "STEP")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to hide WebDriver detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.implicitly_wait(10)
            self.log_message("✅ Chrome WebDriver initialized successfully", "SUCCESS")
            
            # Step 1: Login to Google Cloud Console
            self.log_message("🔑 Starting Step 1: Login to Google Cloud Console", "STEP")
            self.status_var.set(f"Logging into Google Cloud Console: {account['email']}")
            login_result = self.login_to_google_cloud(driver, account)
            self.log_message(f"🔍 Login result: {login_result}", "DEBUG")
            if not login_result:
                self.log_message("❌ Step 1 failed: Login to Google Cloud Console", "ERROR")
                return False
            self.log_message("✅ Step 1 completed: Login to Google Cloud Console", "SUCCESS")
                
            # Step 2: Create or select project
            self.log_message("🏗️ Starting Step 2: Create or select project", "STEP")
            self.status_var.set(f"Creating/selecting project: {account['email']}")
            project_id = self.create_or_select_project(driver, account)
            self.log_message(f"🔍 Project ID result: {project_id}", "DEBUG")
            if not project_id:
                self.log_message("❌ Step 2 failed: Create or select project", "ERROR")
                return False
            self.log_message(f"✅ Step 2 completed: Project created/selected with ID: {project_id}", "SUCCESS")
                
            # Step 3: Enable Gmail API
            self.log_message("🔌 Starting Step 3: Enable Gmail API", "STEP")
            self.status_var.set(f"Enabling Gmail API: {account['email']}")
            api_result = self.enable_gmail_api(driver)
            self.log_message(f"🔍 Gmail API enable result: {api_result}", "DEBUG")
            if not api_result:
                self.log_message("❌ Step 3 failed: Enable Gmail API", "ERROR")
                return False
            self.log_message("✅ Step 3 completed: Gmail API enabled", "SUCCESS")
                
            # Step 4: Create OAuth credentials
            self.log_message("🔑 Starting Step 4: Create OAuth credentials", "STEP")
            self.status_var.set(f"Creating OAuth credentials: {account['email']}")
            credentials_data = self.create_oauth_credentials(driver, account)
            self.log_message(f"🔍 OAuth credentials result: {credentials_data}", "DEBUG")
            if not credentials_data:
                self.log_message("❌ Step 4 failed: Create OAuth credentials", "ERROR")
                return False
            self.log_message("✅ Step 4 completed: OAuth credentials created", "SUCCESS")
                
            # Step 5: Save JSON file
            self.log_message("💾 Starting Step 5: Save JSON file", "STEP")
            self.status_var.set(f"Saving JSON file: {account['email']}")
            save_result = self.save_oauth_json(account, credentials_data, project_id)
            self.log_message(f"🔍 JSON save result: {save_result}", "DEBUG")
            if not save_result:
                self.log_message("❌ Step 5 failed: Save JSON file", "ERROR")
                return False
            self.log_message("✅ Step 5 completed: JSON file saved", "SUCCESS")
            
            self.log_message("🎉 All steps completed successfully!", "SUCCESS")
            return True
            
        except Exception as e:
            error_msg = f"Selenium automation error for {account['email']}: {str(e)}"
            self.status_var.set(f"Error: {account['email']} - {str(e)}")
            print(error_msg)
            self.log_message(f"❌ {error_msg}", "ERROR")
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()
            return False
        finally:
            if driver:
                driver.quit()
                
    def login_to_google_cloud(self, driver, account):
        """Login to Google Cloud Console"""
        print(f"🚀 LOGIN METHOD CALLED with email: {account['email']}")
        print(f"🔐 Password length: {len(account['password'])}")
        try:
            # Navigate to Google Cloud Console
            self.log_message("🌐 Navigating to Google Cloud Console...", "STEP")
            print("🌐 Navigating to Google Cloud Console...")
            driver.get("https://console.cloud.google.com/")
            
            # Wait for login page or dashboard with longer timeout
            print("⏳ Waiting for page to load...")
            WebDriverWait(driver, 30).until(
                lambda d: "accounts.google.com" in d.current_url or "console.cloud.google.com" in d.current_url
            )
            
            print(f"📍 Current URL: {driver.current_url}")
            self.log_message(f"📍 Current URL: {driver.current_url}", "INFO")
            
            # If redirected to login page
            if "accounts.google.com" in driver.current_url:
                print("🔐 Login page detected, entering credentials...")
                self.log_message("🔐 Login page detected, entering credentials...", "STEP")
                # Enter email
                print(f"📧 Entering email: {account['email']}")
                self.log_message(f"📧 Entering email: {account['email']}", "STEP")
                try:
                    email_input = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.ID, "identifierId"))
                    )
                    email_input.clear()
                    email_input.send_keys(account['email'])
                    
                    # Click Next
                    next_button = driver.find_element(By.ID, "identifierNext")
                    next_button.click()
                    print("✅ Email entered successfully")
                    self.log_message("✅ Email entered successfully", "SUCCESS")
                except Exception as e:
                    print(f"❌ Failed to enter email: {str(e)}")
                    self.log_message(f"❌ Failed to enter email: {str(e)}", "ERROR")
                    return False
                
                # Wait for password field with longer timeout
                print("🔐 Waiting for password field...")
                self.log_message("🔐 Waiting for password field...", "STEP")
                try:
                    # Try multiple selectors for password field (including div elements)
                    password_input = None
                    selectors = [
                        (By.CSS_SELECTOR, "#password input"),  # Google's actual structure: div#password > input
                        (By.XPATH, "//div[@id='password']//input"),  # Alternative xpath for div structure
                        (By.CSS_SELECTOR, "div[data-initial-value] input"),  # Google's password div structure
                        (By.NAME, "password"),
                        (By.ID, "password"),
                        (By.CSS_SELECTOR, "input[type='password']"),
                        (By.CSS_SELECTOR, "input[name='Passwd']"),
                        (By.XPATH, "//input[@type='password']"),
                        (By.XPATH, "//input[@name='password']"),
                        (By.XPATH, "//input[@name='Passwd']"),
                        (By.XPATH, "//input[@aria-label='Enter your password']"),
                        (By.XPATH, "//input[@placeholder='Enter your password']"),
                        (By.CSS_SELECTOR, "input[aria-label*='password']"),
                        (By.CSS_SELECTOR, "input[placeholder*='password']"),
                        (By.XPATH, "//div[contains(@class, 'password')]//input"),
                        (By.CSS_SELECTOR, "div[jsname] input[type='password']"),
                        (By.XPATH, "//input[@autocomplete='current-password']"),
                        (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
                        (By.XPATH, "//div[@data-initial-value]//input"),
                        (By.CSS_SELECTOR, "[data-initial-value] input")
                    ]
                    
                    for selector_type, selector_value in selectors:
                        try:
                            self.log_message(f"🔍 Trying password selector: {selector_type} = {selector_value}", "DEBUG")
                            password_input = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((selector_type, selector_value))
                            )
                            self.log_message(f"✅ Password field found with selector: {selector_type} = {selector_value}", "SUCCESS")
                            break
                        except Exception as sel_e:
                            self.log_message(f"❌ Selector failed: {selector_type} = {selector_value}, Error: {sel_e}", "WARNING")
                            continue
                    
                    if password_input is None:
                        # Check for captcha or verification challenges
                        try:
                            # Check for captcha elements
                            captcha_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha')] | //iframe[contains(@src, 'recaptcha')] | //div[contains(text(), 'verify')] | //div[contains(text(), 'robot')]")
                            if captcha_elements:
                                self.log_message("🤖 Captcha detected during login process", "WARNING")
                                self.update_report_status("captcha_detected", "Captcha challenge appeared during password entry")
                                
                            # Check for verification email requirement
                            verification_elements = driver.find_elements(By.XPATH, "//div[contains(text(), 'verification')] | //div[contains(text(), 'verify your identity')] | //div[contains(text(), 'check your email')]")
                            if verification_elements:
                                self.log_message("📧 Email verification required", "WARNING")
                                self.update_report_status("verification_required", "Email verification required during login")
                                
                        except Exception as check_error:
                            self.log_message(f"⚠️ Error checking for challenges: {check_error}", "WARNING")
                        
                        # Wait longer and try again
                        print("⏳ Password field not found, waiting longer...")
                        self.log_message("⏳ Password field not found, waiting longer...", "WARNING")
                        time.sleep(3)
                        try:
                            password_input = WebDriverWait(driver, 15).until(
                                EC.element_to_be_clickable((By.NAME, "password"))
                            )
                        except Exception as session_error:
                            print(f"❌ Session error during password field wait: {session_error}")
                            self.log_message(f"❌ Session error during password field wait: {session_error}", "ERROR")
                            self.update_report_status("error_occurred", f"Password field not found: {session_error}")
                            return False
                    
                    self.log_message("🔐 Entering password...", "STEP")
                    self.log_message(f"🔍 Password field element: {password_input}", "DEBUG")
                    self.log_message(f"🔍 Password field tag: {password_input.tag_name}", "DEBUG")
                    self.log_message(f"🔍 Password field enabled: {password_input.is_enabled()}", "DEBUG")
                    self.log_message(f"🔍 Password field displayed: {password_input.is_displayed()}", "DEBUG")
                    
                    # Add try-catch around the entire password entry process
                    try:
                        self.log_message("🚀 Starting password entry process...", "DEBUG")
                        # Wait for element to be fully interactive
                        self.log_message("⏳ Waiting 2 seconds for element to be interactive...", "DEBUG")
                        time.sleep(2)
                        self.log_message("✅ Wait completed, proceeding with password entry", "DEBUG")
                        
                        # Try to click first to focus
                        self.log_message("🖱️ Attempting to click password field for focus...", "DEBUG")
                        try:
                            password_input.click()
                            self.log_message("✅ Password field clicked for focus", "SUCCESS")
                            time.sleep(1)
                        except Exception as e:
                            self.log_message(f"⚠️ Failed to click password field: {e}", "WARNING")
                        
                        # Clear and enter password
                        try:
                            password_input.clear()
                            self.log_message("✅ Password field cleared", "SUCCESS")
                        except Exception as e:
                            self.log_message(f"⚠️ Failed to clear password field: {e}", "WARNING")
                        
                        # Enhanced password filling with multiple methods (based on successful test results)
                        password_filled = False
                        
                        # Method 1: Standard Selenium approach
                        try:
                            self.log_message("🔧 Method 1: Standard Selenium input...", "DEBUG")
                            password_input.send_keys(account['password'])
                            
                            # Verify
                            password_value = password_input.get_attribute("value")
                            if len(password_value) == len(account['password']):
                                self.log_message(f"✅ Method 1 successful - Password length: {len(password_value)}", "SUCCESS")
                                password_filled = True
                            else:
                                self.log_message(f"⚠️ Method 1 partial - Expected: {len(account['password'])}, Got: {len(password_value)}", "WARNING")
                                
                        except Exception as e:
                            self.log_message(f"❌ Method 1 failed: {e}", "WARNING")
                         
                        # Method 2: JavaScript approach (proven to work from tests)
                        if not password_filled:
                            try:
                                self.log_message("🔧 Method 2: JavaScript input...", "DEBUG")
                                
                                # Focus the element first
                                driver.execute_script("arguments[0].focus();", password_input)
                                time.sleep(0.5)
                                
                                # Clear and set value
                                driver.execute_script("arguments[0].value = '';", password_input)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].value = arguments[1];", password_input, account['password'])
                                
                                # Trigger events
                                driver.execute_script("""
                                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                                """, password_input)
                                
                                time.sleep(1)
                                
                                # Verify
                                password_value = password_input.get_attribute("value")
                                if len(password_value) == len(account['password']):
                                    self.log_message(f"✅ Method 2 successful - Password length: {len(password_value)}", "SUCCESS")
                                    password_filled = True
                                else:
                                    self.log_message(f"⚠️ Method 2 partial - Expected: {len(account['password'])}, Got: {len(password_value)}", "WARNING")
                                    
                            except Exception as e:
                                self.log_message(f"❌ Method 2 failed: {e}", "WARNING")
                         
                        # Method 3: Character-by-character input as final fallback
                        if not password_filled:
                            try:
                                self.log_message("🔧 Method 3: Character-by-character input...", "DEBUG")
                                
                                # Clear field first
                                password_input.clear()
                                time.sleep(0.5)
                                
                                # Send each character individually
                                for char in account['password']:
                                    password_input.send_keys(char)
                                    time.sleep(0.1)
                                
                                time.sleep(1)
                                
                                # Verify
                                password_value = password_input.get_attribute("value")
                                if len(password_value) == len(account['password']):
                                    self.log_message(f"✅ Method 3 successful - Password length: {len(password_value)}", "SUCCESS")
                                    password_filled = True
                                else:
                                    self.log_message(f"⚠️ Method 3 partial - Expected: {len(account['password'])}, Got: {len(password_value)}", "WARNING")
                                    
                            except Exception as e:
                                self.log_message(f"❌ Method 3 failed: {e}", "WARNING")
                        
                        if not password_filled:
                            self.log_message("❌ All password filling methods failed", "ERROR")
                            self.update_report_status("password_failed", "All password filling methods failed")
                            raise Exception("All password filling methods failed")
                            
                        self.log_message(f"🔍 Final password field value length: {len(password_input.get_attribute('value'))}", "DEBUG")
                    
                        # Try multiple selectors for password next button
                        self.log_message("🔍 Looking for Next button...", "STEP")
                        next_button = None
                        next_selectors = [
                            (By.ID, "passwordNext"),
                            (By.CSS_SELECTOR, "#passwordNext"),
                            (By.XPATH, "//button[@id='passwordNext']"),
                            (By.XPATH, "//span[contains(text(), 'Next')]/parent::button"),
                            (By.CSS_SELECTOR, "button[type='submit']"),
                            (By.XPATH, "//div[@id='passwordNext']")
                        ]
                        
                        for selector_type, selector_value in next_selectors:
                            try:
                                next_button = driver.find_element(selector_type, selector_value)
                                self.log_message(f"✅ Next button found with selector: {selector_type} = {selector_value}", "SUCCESS")
                                break
                            except Exception as e:
                                self.log_message(f"❌ Next button selector failed: {selector_type} = {selector_value}", "WARNING")
                                continue
                        
                        if next_button:
                            try:
                                next_button.click()
                                self.log_message("✅ Next button clicked successfully", "SUCCESS")
                            except Exception as e:
                                self.log_message(f"❌ Failed to click Next button: {e}", "ERROR")
                                raise e
                        else:
                            self.log_message("❌ Password Next button not found with any selector", "ERROR")
                            raise Exception("Password Next button not found")
                            
                    except Exception as password_error:
                        self.log_message(f"❌ Password entry process failed: {str(password_error)}", "ERROR")
                        self.update_report_status("password_failed", f"Password entry failed: {str(password_error)}")
                        import traceback
                        self.log_message(f"📋 Full traceback: {traceback.format_exc()}", "ERROR")
                        self.log_message(f"📍 Current URL: {driver.current_url}", "INFO")
                        return False
                        
                except Exception as e:
                    self.log_message(f"❌ Failed to enter password: {str(e)}", "ERROR")
                    self.log_message(f"📍 Current URL: {driver.current_url}", "INFO")
                    
                    # Check for error messages on email step
                    try:
                        error_elements = driver.find_elements(By.CSS_SELECTOR, "[role='alert'], .LXRPh, .dEOOab, .Ekjuhf")
                        for error in error_elements:
                            if error.text.strip():
                                self.log_message(f"❌ Error message: {error.text}", "ERROR")
                    except:
                        pass
                    return False
                
                # Wait for result with much longer timeout
                self.log_message("⏳ Waiting for login result...", "STEP")
                time.sleep(5)  # Give more time for page to process
                
                # Handle post-login prompts (recovery, address, country, terms)
                self.handle_post_login_prompts(driver)
                
                # Check current URL after login attempt
                current_url = driver.current_url
                self.log_message(f"📍 After login URL: {current_url}", "INFO")
                
                # Check for different scenarios
                if "challenge/pwd" in current_url:
                    self.log_message("❌ Password challenge detected - incorrect password", "ERROR")
                    self.update_report_status("password_failed", "Incorrect password - password challenge detected")
                    return False
                elif "console.cloud.google.com" in current_url:
                    self.log_message("✅ Login successful - reached Google Cloud Console", "SUCCESS")
                    return True
                elif "challenge" in current_url or "signin/v2/challenge" in current_url:
                    self.log_message("🔐 2FA verification required. Please complete manually...", "WARNING")
                    self.status_var.set(f"2FA required: {account['email']} - Complete manual verification")
                    
                    # Show message to user
                    import tkinter.messagebox as msgbox
                    msgbox.showwarning("2FA Required", 
                                     f"Two-factor authentication is required for {account['email']}\n\n"
                                     "Please complete the verification in the browser window and then click OK.")
                    
                    # Wait for user to complete 2FA manually
                    try:
                        WebDriverWait(driver, 300).until(  # 5 minutes timeout
                            lambda d: "console.cloud.google.com" in d.current_url
                        )
                        self.log_message("✅ 2FA verification completed", "SUCCESS")
                        return True
                    except TimeoutException:
                        self.log_message("❌ 2FA verification timeout", "ERROR")
                        return False
                        
                elif "signin" in current_url:
                    self.log_message("❌ Login failed - still on signin page", "ERROR")
                    
                    # Check for error messages
                    error_found = False
                    try:
                        error_elements = driver.find_elements(By.CSS_SELECTOR, "[role='alert'], .LXRPh, .dEOOab")
                        for error in error_elements:
                            if error.text.strip():
                                error_text = error.text.strip()
                                self.log_message(f"❌ Error message: {error_text}", "ERROR")
                                
                                # Check for specific error types
                                if "password" in error_text.lower() or "incorrect" in error_text.lower():
                                    self.update_report_status("password_failed", f"Login error: {error_text}")
                                elif "captcha" in error_text.lower() or "verify" in error_text.lower():
                                    self.update_report_status("captcha_detected", f"Captcha required: {error_text}")
                                else:
                                    self.update_report_status("error_occurred", f"Login error: {error_text}")
                                error_found = True
                    except:
                        pass
                    
                    if not error_found:
                        self.update_report_status("error_occurred", "Login failed - still on signin page")
                        
                    return False
                elif "myaccount.google.com" in current_url or "accounts.google.com" in current_url:
                    self.log_message("⚠️ Redirected to Google account page - trying to navigate to Cloud Console", "WARNING")
                    try:
                        driver.get("https://console.cloud.google.com/")
                        time.sleep(3)
                        if "console.cloud.google.com" in driver.current_url:
                            self.log_message("✅ Successfully navigated to Google Cloud Console", "SUCCESS")
                            return True
                        else:
                            self.log_message(f"❌ Failed to reach Cloud Console, current URL: {driver.current_url}", "ERROR")
                            return False
                    except Exception as nav_e:
                        self.log_message(f"❌ Navigation error: {nav_e}", "ERROR")
                        return False
                else:
                    self.log_message(f"⚠️ Unexpected URL after login: {current_url}", "WARNING")
                    # Try to navigate to Cloud Console
                    try:
                        driver.get("https://console.cloud.google.com/")
                        time.sleep(3)
                        if "console.cloud.google.com" in driver.current_url:
                            self.log_message("✅ Successfully navigated to Google Cloud Console", "SUCCESS")
                            return True
                        else:
                            self.log_message(f"❌ Failed to reach Cloud Console after redirect, current URL: {driver.current_url}", "ERROR")
                            return False
                    except Exception as nav_e:
                        self.log_message(f"❌ Navigation error after unexpected URL: {nav_e}", "ERROR")
                        return False
            else:
                self.log_message("✅ Already logged in - reached Google Cloud Console directly", "SUCCESS")
                return True
            
        except TimeoutException as e:
            self.log_message(f"⏰ Login timeout: {str(e)}", "ERROR")
            self.log_message(f"📍 Current URL: {driver.current_url}", "INFO")
            self.status_var.set(f"Login timeout: {account['email']}")
            return False
        except Exception as e:
            self.log_message(f"❌ Login error: {str(e)}", "ERROR")
            self.log_message(f"📍 Current URL: {driver.current_url}", "INFO")
            self.status_var.set(f"Login error: {account['email']} - {str(e)}")
            return False
    
    def handle_post_login_prompts(self, driver):
        """Handle post-login prompts: recovery options, address, country, terms of service"""
        try:
            self.log_message("🔧 Handling post-login prompts...", "STEP")
            
            # Wait a bit for any prompts to appear
            time.sleep(3)
            
            # Handle Recovery Option - Cancel
            self.log_message("🔍 Checking for recovery option prompt...", "DEBUG")
            recovery_selectors = [
                "//button[contains(text(), 'Cancel')]",
                "//button[contains(text(), 'Skip')]",
                "//button[contains(text(), 'Not now')]",
                "//span[contains(text(), 'Cancel')]/parent::button",
                "//span[contains(text(), 'Skip')]/parent::button",
                "//a[contains(text(), 'Cancel')]",
                "//a[contains(text(), 'Skip')]",
                "//div[contains(text(), 'recovery')]//following::button[contains(text(), 'Cancel')]",
                "//div[contains(text(), 'recovery')]//following::button[contains(text(), 'Skip')]"
            ]
            
            for selector in recovery_selectors:
                try:
                    recovery_btn = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    recovery_btn.click()
                    self.log_message(f"✅ Cancelled recovery option with: {selector}", "SUCCESS")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Handle Add Home Address - Skip
            self.log_message("🔍 Checking for address prompt...", "DEBUG")
            address_selectors = [
                "//button[contains(text(), 'Skip')]",
                "//button[contains(text(), 'Not now')]",
                "//span[contains(text(), 'Skip')]/parent::button",
                "//a[contains(text(), 'Skip')]",
                "//div[contains(text(), 'address')]//following::button[contains(text(), 'Skip')]",
                "//div[contains(text(), 'Address')]//following::button[contains(text(), 'Skip')]",
                "//button[@aria-label='Skip']",
                "//button[contains(@class, 'skip')]"
            ]
            
            for selector in address_selectors:
                try:
                    address_btn = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    address_btn.click()
                    self.log_message(f"✅ Skipped address with: {selector}", "SUCCESS")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Handle Country Selection - United States
            self.log_message("🔍 Checking for country selection...", "DEBUG")
            try:
                # Look for country dropdown or selection
                country_selectors = [
                    "//select[contains(@name, 'country')]",
                    "//select[contains(@id, 'country')]",
                    "//div[contains(text(), 'Country')]//following::select",
                    "//label[contains(text(), 'Country')]//following::select"
                ]
                
                for selector in country_selectors:
                    try:
                        country_select = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        
                        # Select United States
                        from selenium.webdriver.support.ui import Select
                        select = Select(country_select)
                        
                        # Try different variations of United States
                        us_options = ['United States', 'US', 'USA', 'United States of America']
                        for option in us_options:
                            try:
                                select.select_by_visible_text(option)
                                self.log_message(f"✅ Selected country: {option}", "SUCCESS")
                                time.sleep(2)
                                break
                            except:
                                continue
                        break
                    except:
                        continue
                        
                # Also try clicking on United States option directly
                us_option_selectors = [
                    "//option[contains(text(), 'United States')]",
                    "//li[contains(text(), 'United States')]",
                    "//div[contains(text(), 'United States')]"
                ]
                
                for selector in us_option_selectors:
                    try:
                        us_option = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        us_option.click()
                        self.log_message(f"✅ Selected United States with: {selector}", "SUCCESS")
                        time.sleep(2)
                        break
                    except:
                        continue
                        
            except Exception as e:
                self.log_message(f"⚠️ Country selection not found or failed: {e}", "WARNING")
            
            # Handle Terms of Service - Agree & Continue
            self.log_message("🔍 Checking for terms of service...", "DEBUG")
            terms_selectors = [
                "//button[contains(text(), 'Agree & Continue')]",
                "//button[contains(text(), 'Agree and Continue')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Continue')]",
                "//span[contains(text(), 'Agree & Continue')]/parent::button",
                "//span[contains(text(), 'Agree and Continue')]/parent::button",
                "//span[contains(text(), 'Accept')]/parent::button",
                "//a[contains(text(), 'Agree & Continue')]",
                "//div[contains(text(), 'Terms')]//following::button[contains(text(), 'Agree')]",
                "//div[contains(text(), 'terms')]//following::button[contains(text(), 'Continue')]"
            ]
            
            for selector in terms_selectors:
                try:
                    terms_btn = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    terms_btn.click()
                    self.log_message(f"✅ Agreed to terms with: {selector}", "SUCCESS")
                    time.sleep(3)
                    break
                except:
                    continue
            
            self.log_message("✅ Post-login prompts handling completed", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"⚠️ Error handling post-login prompts: {e}", "WARNING")
            # Don't fail the entire process for prompt handling issues
            pass
            
    def create_or_select_project(self, driver, account):
        """Create or select project with comprehensive fallback methods for Google Cloud Console"""
        try:
            self.log_message("🏗️ Creating new Google Cloud project...", "STEP")
            # Generate project ID
            project_id = f"gmail-oauth-{account['email'].split('@')[0]}-{int(time.time())}"
            project_name = f"Gmail OAuth {account['email'].split('@')[0]}"
            
            # Update status for project creation start
            self.update_report_status("project_creation", f"Starting project creation for {account['email']}")
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Method 1: Try direct navigation first (most reliable)
            self.log_message("🔄 Using direct navigation to project creation", "STEP")
            driver.get("https://console.cloud.google.com/projectcreate")
            time.sleep(8)  # Longer wait for page load
            
            # Check if we're redirected to login or if page loaded properly
            current_url = driver.current_url
            if "signin" in current_url or "accounts.google.com" in current_url:
                self.log_message("⚠️ Redirected to login, waiting for authentication...", "DEBUG")
                time.sleep(10)
                # Try navigation again after login
                driver.get("https://console.cloud.google.com/projectcreate")
                time.sleep(8)
            
            # Method 2: If direct navigation fails, try dropdown method
            if "projectcreate" not in driver.current_url:
                self.log_message("🔄 Direct navigation failed, trying dropdown method", "STEP")
                driver.get("https://console.cloud.google.com/")
                time.sleep(5)
                
                # Try to find and click project selector dropdown
                project_selector_found = False
                project_selectors = [
                    "[data-testid='project-switcher-button']",
                    "[aria-label*='Select a project']", 
                    "[aria-label*='project']",
                    ".p6n-project-switcher-button",
                    ".cfc-project-switcher-button",
                    "button[aria-haspopup='listbox']",
                    "//button[contains(@aria-label, 'project')]",
                    "//button[contains(@aria-label, 'Project')]",
                    "//div[contains(@class, 'project')]//button",
                    "//span[contains(text(), 'Select a project')]"
                ]
                
                for selector in project_selectors:
                    try:
                        if selector.startswith("//"):
                            element = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            element = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        element.click()
                        self.log_message(f"✅ Found project selector with: {selector}", "DEBUG")
                        project_selector_found = True
                        time.sleep(3)
                        break
                    except:
                        continue
                
                if project_selector_found:
                    # Look for "New Project" button
                    new_project_selectors = [
                        "//span[contains(text(), 'New Project')]",
                        "//button[contains(text(), 'New Project')]", 
                        "//a[contains(text(), 'New Project')]",
                        "//span[contains(text(), 'NEW PROJECT')]",
                        "//button[contains(text(), 'Create Project')]",
                        "//span[contains(text(), 'Create Project')]",
                        "//div[contains(text(), 'New Project')]",
                        "//li[contains(text(), 'New Project')]"
                    ]
                    
                    new_project_clicked = False
                    for selector in new_project_selectors:
                        try:
                            new_project_btn = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            new_project_btn.click()
                            self.log_message(f"✅ Clicked New Project with: {selector}", "DEBUG")
                            new_project_clicked = True
                            time.sleep(5)
                            break
                        except:
                            continue
                    
                    if not new_project_clicked:
                        self.log_message("⚠️ Could not find New Project button, trying direct URL again", "DEBUG")
                        driver.get("https://console.cloud.google.com/projectcreate")
                        time.sleep(8)
            
            # Enter project name with comprehensive selector attempts
            self.log_message(f"📝 Creating project with name: {project_name}", "STEP")
            
            # Wait for form to load
            time.sleep(3)
            
            # More comprehensive name input selectors
            name_selectors = [
                "p6ntest-project-name-input",
                "projectId", 
                "p6n-kp-name-input",
                "project-name",
                "projectName",
                "name",
                "//input[@placeholder='My Project']",
                "//input[@placeholder='Project name']",
                "//input[@placeholder='Enter project name']",
                "//input[@aria-label='Project name']",
                "//input[@aria-label='Name']",
                "//input[contains(@placeholder, 'project')]",
                "//input[contains(@placeholder, 'Project')]",
                "//input[contains(@aria-label, 'name')]",
                "//input[contains(@aria-label, 'Name')]",
                "//input[@type='text'][1]",
                "//form//input[@type='text']",
                "//div[contains(@class, 'project')]//input",
                "//label[contains(text(), 'Project name')]//following::input",
                "//label[contains(text(), 'Name')]//following::input"
            ]
            
            name_input_found = False
            for i, selector in enumerate(name_selectors):
                try:
                    self.log_message(f"🔍 Trying selector {i+1}/{len(name_selectors)}: {selector}", "DEBUG")
                    
                    if selector.startswith("//"):
                        project_name_input = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        project_name_input = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.ID, selector))
                        )
                    
                    # Scroll to element if needed
                    driver.execute_script("arguments[0].scrollIntoView(true);", project_name_input)
                    time.sleep(1)
                    
                    # Clear and enter project name
                    project_name_input.clear()
                    project_name_input.send_keys(project_name)
                    
                    # Verify text was entered
                    if project_name_input.get_attribute('value') == project_name:
                        self.log_message(f"✅ Successfully entered project name with: {selector}", "DEBUG")
                        name_input_found = True
                        time.sleep(2)
                        break
                    else:
                        self.log_message(f"⚠️ Text not entered properly with: {selector}", "DEBUG")
                        
                except Exception as e:
                    self.log_message(f"❌ Failed with selector {selector}: {str(e)}", "DEBUG")
                    continue
            
            if not name_input_found:
                # Try to find any input field and use it
                self.log_message("🔍 Trying to find any input field on the page", "DEBUG")
                try:
                    all_inputs = driver.find_elements(By.TAG_NAME, "input")
                    for input_elem in all_inputs:
                        if input_elem.is_displayed() and input_elem.is_enabled():
                            input_type = input_elem.get_attribute('type')
                            if input_type in ['text', 'search', None]:
                                input_elem.clear()
                                input_elem.send_keys(project_name)
                                if input_elem.get_attribute('value') == project_name:
                                    self.log_message("✅ Found working input field", "DEBUG")
                                    name_input_found = True
                                    break
                except:
                    pass
            
            if not name_input_found:
                # Take a screenshot for debugging
                screenshot_path = f"debug_project_creation_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                self.log_message(f"📸 Screenshot saved: {screenshot_path}", "DEBUG")
                raise Exception("Could not find project name input field after trying all selectors")
            
            # Click Create button with comprehensive selector attempts
            self.log_message("🔘 Looking for Create button...", "STEP")
            create_selectors = [
                "//span[contains(text(), 'Create')]/parent::button",
                "//button[contains(text(), 'Create')]",
                "//button[contains(text(), 'CREATE')]",
                "//input[@value='Create']",
                "//button[@type='submit']",
                "//span[contains(text(), 'Create')]",
                "button[aria-label='Create']",
                "//button[contains(@class, 'create')]",
                "//button[contains(@class, 'Create')]",
                "//div[contains(text(), 'Create')]//parent::button",
                "//form//button[last()]",
                "//button[contains(@aria-label, 'Create')]"
            ]
            
            create_clicked = False
            for i, selector in enumerate(create_selectors):
                try:
                    self.log_message(f"🔍 Trying Create button selector {i+1}/{len(create_selectors)}: {selector}", "DEBUG")
                    
                    if selector.startswith("//"):
                        create_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        create_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Scroll to button
                    driver.execute_script("arguments[0].scrollIntoView(true);", create_btn)
                    time.sleep(1)
                    
                    create_btn.click()
                    self.log_message(f"✅ Successfully clicked Create button with: {selector}", "DEBUG")
                    create_clicked = True
                    break
                except Exception as e:
                    self.log_message(f"❌ Failed with Create selector {selector}: {str(e)}", "DEBUG")
                    continue
            
            if not create_clicked:
                # Try to find any button and click it
                self.log_message("🔍 Trying to find any clickable button", "DEBUG")
                try:
                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in all_buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.lower()
                            if 'create' in button_text or 'submit' in button_text:
                                button.click()
                                self.log_message(f"✅ Clicked button with text: {button.text}", "DEBUG")
                                create_clicked = True
                                break
                except:
                    pass
            
            if not create_clicked:
                self.update_report_status("error_occurred", "Could not find or click Create button")
                raise Exception("Could not find or click Create button")
            
            self.log_message("⏳ Waiting for project creation to complete...", "STEP")
            # Wait for project creation with multiple success indicators
            try:
                WebDriverWait(driver, 60).until(  # Increased timeout
                    lambda d: any([
                        "Project created" in d.page_source,
                        "dashboard" in d.current_url.lower(),
                        "getting-started" in d.current_url.lower(),
                        "console.cloud.google.com/home" in d.current_url,
                        "apis/dashboard" in d.current_url,
                        "welcome" in d.current_url.lower(),
                        "project" in d.current_url and "create" not in d.current_url
                    ])
                )
            except:
                # Additional wait and check
                time.sleep(15)
                current_url = driver.current_url
                if "console.cloud.google.com" in current_url and "create" not in current_url:
                    self.log_message("✅ Project creation appears successful (URL check)", "DEBUG")
                else:
                    # Take screenshot for debugging
                    screenshot_path = f"debug_project_timeout_{int(time.time())}.png"
                    driver.save_screenshot(screenshot_path)
                    self.log_message(f"📸 Timeout screenshot saved: {screenshot_path}", "DEBUG")
                    self.update_report_status("error_occurred", "Project creation timeout - no success indicators found")
                    raise Exception("Project creation timeout - no success indicators found")
            
            self.log_message(f"✅ Project created successfully: {project_name}", "SUCCESS")
            self.update_report_status("project_creation", f"Project created successfully: {project_name}")
            self.log_message(f"📍 Project ID result: {project_id}", "DEBUG")
            return project_id
            
        except Exception as e:
            self.log_message(f"❌ Error creating project: {e}", "ERROR")
            self.update_report_status("error_occurred", f"Project creation failed: {str(e)}")
            self.log_message(f"📍 Project ID result: None", "DEBUG")
            self.status_var.set(f"Project creation error: {str(e)}")
            return None
            
    def enable_gmail_api(self, driver):
        """Enable Gmail API"""
        try:
            self.log_message("🔌 Enabling Gmail API...", "STEP")
            self.update_report_status("api_enabling", "Starting Gmail API enablement")
            # Navigate to APIs & Services > Library
            driver.get("https://console.cloud.google.com/apis/library")
            
            self.log_message("🔍 Searching for Gmail API...", "STEP")
            # Search for Gmail API
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']"))
            )
            search_box.clear()
            search_box.send_keys("Gmail API")
            search_box.submit()
            
            # Click on Gmail API
            gmail_api_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'gmail')]//div[contains(text(), 'Gmail API')]"))
            )
            gmail_api_link.click()
            
            self.log_message("⚡ Enabling Gmail API for the project...", "STEP")
            # Click Enable
            try:
                enable_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Enable')]/parent::button"))
                )
                enable_btn.click()
                
                # Wait for API to be enabled
                WebDriverWait(driver, 20).until(
                    lambda d: "API enabled" in d.page_source or "Manage" in d.page_source
                )
            except:
                # API might already be enabled
                if "Manage" in driver.page_source:
                    pass  # Already enabled
                else:
                    raise
            
            self.log_message("✅ Gmail API enabled successfully", "SUCCESS")
            self.update_report_status("api_enabling", "Gmail API enabled successfully")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error enabling Gmail API: {e}", "ERROR")
            self.update_report_status("error_occurred", f"Gmail API enablement failed: {str(e)}")
            self.status_var.set(f"Gmail API enable error: {str(e)}")
            return False
            
    def create_oauth_credentials(self, driver, account):
        """Create OAuth credentials"""
        try:
            self.log_message("🔑 Creating OAuth 2.0 Client ID...", "STEP")
            self.update_report_status("oauth_creation", "Starting OAuth credentials creation")
            # Navigate to Credentials page
            driver.get("https://console.cloud.google.com/apis/credentials")
            
            # Click "Create Credentials"
            create_credentials_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Create Credentials')]/parent::button"))
            )
            create_credentials_btn.click()
            
            # Select "OAuth client ID"
            oauth_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'OAuth client ID')]"))
            )
            oauth_option.click()
            
            # Configure OAuth consent screen if needed
            try:
                configure_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Configure Consent Screen')]/parent::button")
                configure_btn.click()
                
                self.log_message("🔐 Setting up OAuth consent screen...", "STEP")
                self.update_report_status("oauth_creation", "Setting up OAuth consent screen")
                
                # Select External
                external_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@value='EXTERNAL']"))
                )
                external_radio.click()
                
                # Click Create
                create_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Create')]/parent::button")
                create_btn.click()
                
                self.log_message("📋 Filling OAuth consent screen details...", "STEP")
                
                # Step 1: Click Get started
                try:
                    get_started_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Get started')]/parent::button"))
                    )
                    get_started_btn.click()
                    time.sleep(2)
                except:
                    pass  # Might already be on the form
                
                # Step 2: Fill App information
                self.log_message("📝 Filling app information with login email...", "STEP")
                
                # App name - use login email
                app_name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='App name']"))
                )
                app_name_input.clear()
                app_name_input.send_keys(account['email'])
                
                # User support email - use login email
                support_email_selectors = [
                    "input[aria-label*='User support email']",
                    "input[aria-label*='support email']",
                    "//input[contains(@aria-label, 'support')]",
                    "//input[contains(@placeholder, 'support')]"
                ]
                
                support_email_found = False
                for selector in support_email_selectors:
                    try:
                        if selector.startswith("//"):
                            support_email = driver.find_element(By.XPATH, selector)
                        else:
                            support_email = driver.find_element(By.CSS_SELECTOR, selector)
                        support_email.clear()
                        support_email.send_keys(account['email'])
                        support_email_found = True
                        break
                    except:
                        continue
                
                # Step 3: Select External audience
                self.log_message("👥 Selecting external audience...", "STEP")
                try:
                    external_radio = driver.find_element(By.XPATH, "//input[@value='EXTERNAL']")
                    if not external_radio.is_selected():
                        external_radio.click()
                except:
                    pass  # Might already be selected
                
                # Step 4: Fill Contact information - use login email
                self.log_message("📧 Filling contact information with login email...", "STEP")
                contact_email_selectors = [
                    "input[aria-label*='Developer contact information']",
                    "input[aria-label*='contact information']",
                    "input[aria-label*='Email addresses']",
                    "//input[contains(@aria-label, 'contact')]",
                    "//input[contains(@aria-label, 'Email')]",
                    "//textarea[contains(@aria-label, 'contact')]"
                ]
                
                for selector in contact_email_selectors:
                    try:
                        if selector.startswith("//"):
                            contact_email = driver.find_element(By.XPATH, selector)
                        else:
                            contact_email = driver.find_element(By.CSS_SELECTOR, selector)
                        contact_email.clear()
                        contact_email.send_keys(account['email'])
                        break
                    except:
                        continue
                
                # Step 5: Agree & Continue
                self.log_message("✅ Clicking Agree & Continue...", "STEP")
                agree_continue_selectors = [
                    "//span[contains(text(), 'Agree & Continue')]/parent::button",
                    "//button[contains(text(), 'Agree & Continue')]",
                    "//span[contains(text(), 'Save and Continue')]/parent::button",
                    "//button[contains(text(), 'Save and Continue')]",
                    "//span[contains(text(), 'Continue')]/parent::button",
                    "//button[contains(text(), 'Continue')]"
                ]
                
                for selector in agree_continue_selectors:
                    try:
                        agree_btn = driver.find_element(By.XPATH, selector)
                        agree_btn.click()
                        self.log_message(f"✅ Clicked button with selector: {selector}", "DEBUG")
                        break
                    except:
                        continue
                
                time.sleep(3)
                
                # Step 6: Click Continue - Create
                self.log_message("🔄 Clicking Continue - Create...", "STEP")
                create_selectors = [
                    "//span[contains(text(), 'Create')]/parent::button",
                    "//button[contains(text(), 'Create')]",
                    "//span[contains(text(), 'Continue')]/parent::button",
                    "//button[contains(text(), 'Continue')]",
                    "//span[contains(text(), 'Save and Continue')]/parent::button"
                ]
                
                for selector in create_selectors:
                    try:
                        create_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        create_btn.click()
                        self.log_message(f"✅ Clicked Create/Continue button with: {selector}", "DEBUG")
                        break
                    except:
                        continue
                
                self.log_message("⏭️ Scopes step: Saving and continuing...", "STEP")
                # Scopes step: Save and continue
                try:
                    save_continue_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Save and Continue')]/parent::button"))
                    )
                    save_continue_btn.click()
                    self.log_message("✅ Scopes saved and continued", "SUCCESS")
                except Exception as e:
                    self.log_message(f"⚠️ Could not click Save and Continue on scopes: {e}", "WARNING")
                
                # Test users step: add the login email as a test user
                self.log_message("👤 Adding test user to consent screen...", "STEP")
                try:
                    add_users_selectors = [
                        "//span[contains(text(), 'Add users')]/parent::button",
                        "//button[contains(text(), 'Add users')]",
                        "//span[contains(text(), 'ADD USERS')]/parent::button",
                        "//button[contains(text(), 'ADD USERS')]",
                        "//span[contains(text(), 'Add user')]/parent::button",
                        "//button[contains(text(), 'Add user')]",
                    ]
                    add_btn = None
                    for sel in add_users_selectors:
                        try:
                            add_btn = WebDriverWait(driver, 8).until(
                                EC.element_to_be_clickable((By.XPATH, sel))
                            )
                            if add_btn:
                                add_btn.click()
                                self.log_message(f"✅ Opened Add users dialog: {sel}", "DEBUG")
                                break
                        except:
                            continue
                    
                    # Enter email in the dialog
                    email_input_selectors = [
                        (By.XPATH, "//input[@type='email']"),
                        (By.XPATH, "//input[contains(@aria-label, 'Email')]"),
                        (By.CSS_SELECTOR, "input[type='email']"),
                        (By.CSS_SELECTOR, "input[aria-label*='Email']"),
                        (By.XPATH, "//textarea[contains(@aria-label, 'Email')]"),
                    ]
                    email_input = None
                    for by, sel in email_input_selectors:
                        try:
                            email_input = WebDriverWait(driver, 8).until(
                                EC.visibility_of_element_located((by, sel))
                            )
                            break
                        except:
                            continue
                    
                    if email_input:
                        email_input.clear()
                        email_input.send_keys(account['email'])
                        time.sleep(0.5)
                        # Click Add/Save in dialog
                        confirm_selectors = [
                            "//span[contains(text(), 'Add')]/parent::button",
                            "//button[contains(text(), 'Add')]",
                            "//span[contains(text(), 'Save')]/parent::button",
                            "//button[contains(text(), 'Save')]",
                            "//span[contains(text(), 'Done')]/parent::button",
                            "//button[contains(text(), 'Done')]",
                        ]
                        for sel in confirm_selectors:
                            try:
                                confirm_btn = WebDriverWait(driver, 8).until(
                                    EC.element_to_be_clickable((By.XPATH, sel))
                                )
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", confirm_btn)
                                confirm_btn.click()
                                self.log_message(f"✅ Confirmed test user with: {sel}", "DEBUG")
                                break
                            except:
                                continue
                    else:
                        self.log_message("⚠️ Could not locate email input for Add users", "WARNING")
                    
                    # Save and continue from test users step
                    try:
                        save_continue_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Save and Continue')]/parent::button"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_continue_btn)
                        save_continue_btn.click()
                        self.log_message("✅ Test users saved and continued", "SUCCESS")
                    except Exception as e:
                        self.log_message(f"⚠️ Could not click Save and Continue on test users: {e}", "WARNING")
                    
                    # Back to dashboard (kept in Testing status)
                    back_dashboard_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Back to Dashboard')]/parent::button"))
                    )
                    back_dashboard_btn.click()
                    self.log_message("ℹ️ Consent screen kept in Testing with test user added", "INFO")
                except Exception as e:
                    self.log_message(f"⚠️ Test users configuration step encountered an issue: {e}", "WARNING")
                
                self.log_message("✅ OAuth consent screen configured successfully", "SUCCESS")
                self.update_report_status("oauth_creation", "OAuth consent screen configured successfully")
                
                # Go back to credentials
                driver.get("https://console.cloud.google.com/apis/credentials")
                
                # Try creating credentials again
                create_credentials_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Create Credentials')]/parent::button"))
                )
                create_credentials_btn.click()
                
                oauth_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'OAuth client ID')]"))
                )
                oauth_option.click()
                
            except:
                pass  # Consent screen might already be configured
            
            self.log_message("🖥️ Configuring OAuth client for desktop application...", "STEP")
            self.update_report_status("oauth_creation", "Configuring OAuth client for desktop application")
            # Select application type (Desktop application)
            app_type_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label*='Application type']"))
            )
            app_type_dropdown.click()
            
            desktop_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Desktop application')]"))
            )
            desktop_option.click()
            
            # Enter name using login email as specified in requirements
            self.log_message(f"📝 Setting client name to login email: {account['email']}", "STEP")
            name_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label*='Name']")
            name_input.clear()
            name_input.send_keys(account['email'])
            
            # Click Create
            create_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Create')]/parent::button")
            create_btn.click()
            
            self.log_message("⏳ Waiting for OAuth client creation...", "STEP")
            # Wait for credentials to be created and get the data
            WebDriverWait(driver, 15).until(
                lambda d: "Client ID" in d.page_source and "Client secret" in d.page_source
            )
            
            # Download JSON file first
            self.log_message("📥 Downloading OAuth JSON file...", "STEP")
            try:
                download_selectors = [
                    "//span[contains(text(), 'Download JSON')]/parent::button",
                    "//button[contains(text(), 'Download JSON')]",
                    "//span[contains(text(), 'DOWNLOAD JSON')]/parent::button",
                    "//button[contains(text(), 'DOWNLOAD JSON')]",
                    "//span[contains(text(), 'Download')]/parent::button",
                    "//button[contains(text(), 'Download')]"
                ]
                
                download_clicked = False
                for selector in download_selectors:
                    try:
                        download_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        download_btn.click()
                        self.log_message(f"✅ Clicked Download JSON button with: {selector}", "DEBUG")
                        download_clicked = True
                        break
                    except:
                        continue
                
                if download_clicked:
                    self.log_message("⏳ Waiting for file download...", "STEP")
                    time.sleep(5)  # Wait for download to complete
                    
                    # Rename downloaded file
                    self.rename_downloaded_json(account['email'])
                else:
                    self.log_message("⚠️ Could not find Download JSON button", "WARNING")
                    
            except Exception as e:
                self.log_message(f"⚠️ JSON download failed: {e}", "WARNING")
            
            # Extract client ID and secret for backup
            try:
                client_id_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Client ID')]/following-sibling::span")
                client_secret_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Client secret')]/following-sibling::span")
                
                credentials_data = {
                    'client_id': client_id_element.text,
                    'client_secret': client_secret_element.text
                }
            except:
                credentials_data = {'client_id': 'extracted_from_download', 'client_secret': 'extracted_from_download'}
            
            # Close the dialog
            try:
                close_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'OK')]/parent::button")
                close_btn.click()
            except:
                try:
                    close_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Done')]/parent::button")
                    close_btn.click()
                except:
                    pass
            
            self.log_message("✅ OAuth credentials created successfully", "SUCCESS")
            self.update_report_status("oauth_creation", "OAuth credentials created successfully")
            return credentials_data
            
        except Exception as e:
            self.log_message(f"❌ OAuth credentials creation error: {e}", "ERROR")
            self.status_var.set(f"OAuth credentials creation error: {str(e)}")
            self.update_report_status("error_occurred", f"OAuth credentials creation failed: {str(e)}")
            return None
            
    def rename_downloaded_json(self, email):
        """Rename downloaded JSON file to login email"""
        try:
            self.log_message("📂 Looking for downloaded JSON file...", "STEP")
            
            # Common download directories
            download_dirs = [
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.join(os.path.expanduser("~"), "Desktop"),
                self.output_dir
            ]
            
            # Look for recently downloaded JSON files
            json_files = []
            for download_dir in download_dirs:
                if os.path.exists(download_dir):
                    for file in os.listdir(download_dir):
                        if file.endswith('.json') and ('client_secret' in file.lower() or 'oauth' in file.lower()):
                            file_path = os.path.join(download_dir, file)
                            # Check if file was created recently (within last 2 minutes)
                            if time.time() - os.path.getctime(file_path) < 120:
                                json_files.append(file_path)
            
            if json_files:
                # Get the most recent file
                latest_file = max(json_files, key=os.path.getctime)
                
                # Create new filename with email
                email_safe = email.replace('@', '_').replace('.', '_')
                new_filename = f"{email_safe}.json"
                new_filepath = os.path.join(self.output_dir, new_filename)
                
                # Move and rename file
                import shutil
                shutil.move(latest_file, new_filepath)
                
                self.log_message(f"✅ JSON file renamed to: {new_filename}", "SUCCESS")
                self.log_message(f"📁 File saved to: {new_filepath}", "INFO")
                return True
            else:
                self.log_message("⚠️ No recent JSON files found in download directories", "WARNING")
                return False
                
        except Exception as e:
            self.log_message(f"❌ File rename error: {e}", "ERROR")
            return False
    
    def save_oauth_json(self, account, credentials_data, project_id):
        """Save OAuth JSON file"""
        try:
            self.log_message("💾 Preparing OAuth JSON data...", "STEP")
            oauth_data = {
                "installed": {
                    "client_id": credentials_data['client_id'],
                    "client_secret": credentials_data['client_secret'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                },
                "account_info": {
                    "email": account['email'],
                    "project_id": project_id,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            # Save JSON file
            filename = f"{account['email'].replace('@', '_').replace('.', '_')}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            self.log_message(f"📁 Saving OAuth JSON as: {filename}", "STEP")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(oauth_data, f, indent=2, ensure_ascii=False)
                
            self.log_message(f"✅ OAuth JSON saved successfully: {filename}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log_message(f"❌ JSON save error: {e}", "ERROR")
            self.status_var.set(f"JSON save error: {str(e)}")
            return False

def main():
    """Main function"""
    root = tk.Tk()
    app = GmailOAuthGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()