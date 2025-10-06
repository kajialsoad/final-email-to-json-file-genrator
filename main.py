#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail OAuth Client JSON Generator - Playwright Version
Enhanced tkinter GUI for Playwright-based Gmail OAuth automation
"""

import asyncio
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional, Any

# Optional imports with fallbacks
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    # Create a simple CSV reader fallback
    import csv

# Import our modules
from oauth_credentials import OAuthCredentialsManager
from config import get_config, ConfigManager
from error_handler import error_handler, ErrorType, log_error
from email_reporter import email_reporter

class GmailOAuthGUI:
    """Enhanced GUI for Playwright-based Gmail OAuth automation"""
    
    def __init__(self):
        self.root = Tk()
        self.config = get_config()
        self.logger = error_handler.logger
        
        # Initialize variables
        self.setup_variables()
        
        # Setup GUI
        self.setup_main_window()
        self.setup_widgets()
        
        # Initialize statistics
        self.stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'in_progress': 0,
            'start_time': None
        }
        
        # Processing control
        self.is_processing = False
        self.stop_requested = False
        self.current_thread = None
        
        # Results storage
        self.results = []
        
        self.logger.info("Gmail OAuth GUI initialized")
    
    def setup_variables(self):
        """Initialize tkinter variables"""
        # File paths
        self.csv_file_path = StringVar()
        
        # Single account
        self.single_email = StringVar()
        self.single_password = StringVar()
        
        # Settings
        self.headless_mode = BooleanVar(value=self.config.browser.headless)
        self.stealth_mode = BooleanVar(value=self.config.browser.stealth_mode)
        self.retry_attempts = IntVar(value=self.config.automation.max_retries)
        self.concurrent_limit = IntVar(value=self.config.automation.concurrent_limit)
        
        # Progress
        self.progress_var = DoubleVar()
        self.status_text = StringVar(value="Ready")
        self.current_account = StringVar(value="")
        
        # Statistics
        self.total_accounts = IntVar()
        self.successful_accounts = IntVar()
        self.failed_accounts = IntVar()
        self.verification_accounts = IntVar()
        self.success_rate = StringVar(value="0%")
    
    def setup_main_window(self):
        """Setup the main window"""
        self.root.title("Gmail OAuth Client JSON Generator - Playwright Edition")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        style.configure('Success.TLabel', foreground='green', background='#f0f0f0')
        style.configure('Error.TLabel', foreground='red', background='#f0f0f0')
        style.configure('Warning.TLabel', foreground='orange', background='#f0f0f0')
    
    def setup_widgets(self):
        """Setup all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(W, E, N, S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Gmail OAuth Client JSON Generator", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(W, E, N, S), pady=(0, 10))
        main_frame.rowconfigure(1, weight=1)
        
        # Setup tabs
        self.setup_single_account_tab()
        self.setup_batch_processing_tab()
        self.setup_settings_tab()
        
        # Progress section
        self.setup_progress_section(main_frame)
        
        # Action buttons
        self.setup_action_buttons(main_frame)
        
        # Log section
        self.setup_log_section(main_frame)
    
    def setup_single_account_tab(self):
        """Setup single account processing tab"""
        single_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(single_frame, text="Single Account")
        
        # Email input
        ttk.Label(single_frame, text="Email:", style='Header.TLabel').grid(row=0, column=0, sticky=W, pady=(0, 5))
        email_entry = ttk.Entry(single_frame, textvariable=self.single_email, width=40)
        email_entry.grid(row=1, column=0, columnspan=2, sticky=(W, E), pady=(0, 10))
        
        # Password input
        ttk.Label(single_frame, text="Password:", style='Header.TLabel').grid(row=2, column=0, sticky=W, pady=(0, 5))
        password_entry = ttk.Entry(single_frame, textvariable=self.single_password, show="*", width=40)
        password_entry.grid(row=3, column=0, columnspan=2, sticky=(W, E), pady=(0, 10))
        
        # Generate button
        generate_btn = ttk.Button(
            single_frame, 
            text="Generate OAuth JSON", 
            command=self.start_single_generation,
            style='Accent.TButton'
        )
        generate_btn.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Configure column weights
        single_frame.columnconfigure(0, weight=1)
    
    def setup_batch_processing_tab(self):
        """Setup batch processing tab"""
        batch_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(batch_frame, text="Batch Processing")
        
        # File selection
        ttk.Label(batch_frame, text="CSV/Excel File:", style='Header.TLabel').grid(row=0, column=0, sticky=W, pady=(0, 5))
        
        file_frame = ttk.Frame(batch_frame)
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(W, E), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        file_entry = ttk.Entry(file_frame, textvariable=self.csv_file_path, width=50)
        file_entry.grid(row=0, column=0, sticky=(W, E), padx=(0, 5))
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=1)
        
        # File format info
        info_text = "File format: CSV or Excel with columns 'email' and 'password'"
        ttk.Label(batch_frame, text=info_text, foreground='gray').grid(row=2, column=0, columnspan=2, sticky=W, pady=(0, 10))
        
        # Load accounts button
        load_btn = ttk.Button(batch_frame, text="Load Accounts", command=self.load_accounts)
        load_btn.grid(row=3, column=0, pady=(0, 10))
        
        # Accounts preview
        ttk.Label(batch_frame, text="Loaded Accounts:", style='Header.TLabel').grid(row=4, column=0, sticky=W, pady=(10, 5))
        
        # Accounts listbox with scrollbar
        list_frame = ttk.Frame(batch_frame)
        list_frame.grid(row=5, column=0, columnspan=2, sticky=(W, E, N, S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.accounts_listbox = Listbox(list_frame, height=8)
        self.accounts_listbox.grid(row=0, column=0, sticky=(W, E, N, S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.accounts_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(N, S))
        self.accounts_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Start batch processing button
        batch_btn = ttk.Button(
            batch_frame, 
            text="Start Batch Processing", 
            command=self.start_batch_generation,
            style='Accent.TButton'
        )
        batch_btn.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Configure weights
        batch_frame.columnconfigure(0, weight=1)
        batch_frame.rowconfigure(5, weight=1)
        
        # Store loaded accounts
        self.loaded_accounts = []
    
    def setup_settings_tab(self):
        """Setup settings tab"""
        settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_frame, text="Settings")
        
        # Browser settings
        ttk.Label(settings_frame, text="Browser Settings:", style='Header.TLabel').grid(row=0, column=0, sticky=W, pady=(0, 10))
        
        ttk.Checkbutton(settings_frame, text="Headless Mode", variable=self.headless_mode).grid(row=1, column=0, sticky=W, pady=2)
        ttk.Checkbutton(settings_frame, text="Stealth Mode", variable=self.stealth_mode).grid(row=2, column=0, sticky=W, pady=2)
        
        # Automation settings
        ttk.Label(settings_frame, text="Automation Settings:", style='Header.TLabel').grid(row=3, column=0, sticky=W, pady=(20, 10))
        
        ttk.Label(settings_frame, text="Retry Attempts:").grid(row=4, column=0, sticky=W, pady=2)
        retry_spin = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.retry_attempts, width=10)
        retry_spin.grid(row=4, column=1, sticky=W, padx=(10, 0), pady=2)
        
        ttk.Label(settings_frame, text="Concurrent Limit:").grid(row=5, column=0, sticky=W, pady=2)
        concurrent_spin = ttk.Spinbox(settings_frame, from_=1, to=5, textvariable=self.concurrent_limit, width=10)
        concurrent_spin.grid(row=5, column=1, sticky=W, padx=(10, 0), pady=2)
        
        # Save settings button
        save_btn = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings)
        save_btn.grid(row=6, column=0, columnspan=2, pady=20)
    
    def setup_progress_section(self, parent):
        """Setup progress tracking section"""
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=2, column=0, sticky=(W, E), pady=(0, 10))
        progress_frame.columnconfigure(1, weight=1)
        
        # Status
        ttk.Label(progress_frame, text="Status:").grid(row=0, column=0, sticky=W, padx=(0, 10))
        status_label = ttk.Label(progress_frame, textvariable=self.status_text, style='Header.TLabel')
        status_label.grid(row=0, column=1, sticky=W)
        
        # Current account
        ttk.Label(progress_frame, text="Current:").grid(row=1, column=0, sticky=W, padx=(0, 10))
        current_label = ttk.Label(progress_frame, textvariable=self.current_account)
        current_label.grid(row=1, column=1, sticky=W)
        
        # Progress bar
        ttk.Label(progress_frame, text="Progress:").grid(row=2, column=0, sticky=W, padx=(0, 10), pady=(10, 0))
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=1, sticky=(W, E), pady=(10, 0))
        
        # Statistics
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(W, E), pady=(10, 0))
        
        ttk.Label(stats_frame, text="Total:").grid(row=0, column=0, padx=(0, 5))
        ttk.Label(stats_frame, textvariable=self.total_accounts).grid(row=0, column=1, padx=(0, 15))
        
        ttk.Label(stats_frame, text="Success:").grid(row=0, column=2, padx=(0, 5))
        success_label = ttk.Label(stats_frame, textvariable=self.successful_accounts, style='Success.TLabel')
        success_label.grid(row=0, column=3, padx=(0, 15))
        
        ttk.Label(stats_frame, text="Failed:").grid(row=0, column=4, padx=(0, 5))
        failed_label = ttk.Label(stats_frame, textvariable=self.failed_accounts, style='Error.TLabel')
        failed_label.grid(row=0, column=5, padx=(0, 15))
        
        ttk.Label(stats_frame, text="Verification:").grid(row=0, column=6, padx=(0, 5))
        verification_label = ttk.Label(stats_frame, textvariable=self.verification_accounts, style='Warning.TLabel')
        verification_label.grid(row=0, column=7, padx=(0, 15))
        
        ttk.Label(stats_frame, text="Rate:").grid(row=0, column=8, padx=(0, 5))
        ttk.Label(stats_frame, textvariable=self.success_rate).grid(row=0, column=9)
    
    def setup_action_buttons(self, parent):
        """Setup action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, pady=(0, 10))
        
        # Stop button
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state=DISABLED)
        self.stop_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Open output folder
        output_btn = ttk.Button(button_frame, text="Open Output Folder", command=self.open_output_folder)
        output_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Open reports folder
        reports_btn = ttk.Button(button_frame, text="Open Reports", command=self.open_reports_folder)
        reports_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Export report
        export_btn = ttk.Button(button_frame, text="Export Report", command=self.export_report)
        export_btn.grid(row=0, column=3)
    
    def setup_log_section(self, parent):
        """Setup logging section"""
        log_frame = ttk.LabelFrame(parent, text="Log", padding="10")
        log_frame.grid(row=4, column=0, sticky=(W, E, N, S), pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(4, weight=1)
        
        # Log text widget with scrollbar
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=0, column=0, sticky=(W, E, N, S))
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)
        
        self.log_text = Text(log_text_frame, height=10, wrap=WORD)
        self.log_text.grid(row=0, column=0, sticky=(W, E, N, S))
        
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=VERTICAL, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(N, S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Configure text tags for colored logging
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        
        # Clear log button
        clear_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_btn.grid(row=1, column=0, pady=(10, 0))
    
    def browse_file(self):
        """Browse for CSV/Excel file"""
        file_path = filedialog.askopenfilename(
            title="Select CSV or Excel file",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.csv_file_path.set(file_path)
            self.log_message(f"📁 Selected file: {file_path}")
    
    def load_accounts(self):
        """Load accounts from CSV/Excel file"""
        file_path = self.csv_file_path.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        try:
            # Read file based on extension and available libraries
            if file_path.endswith('.csv'):
                if HAS_PANDAS:
                    df = pd.read_csv(file_path)
                    accounts_data = df.to_dict('records')
                else:
                    # Fallback CSV reader
                    accounts_data = []
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        accounts_data = list(reader)
            else:
                if HAS_PANDAS:
                    df = pd.read_excel(file_path)
                    accounts_data = df.to_dict('records')
                else:
                    messagebox.showerror("Error", "Excel files require pandas. Please install pandas or use CSV format.")
                    return
            
            # Validate columns
            required_columns = ['email', 'password']
            if accounts_data:
                missing_columns = [col for col in required_columns if col not in accounts_data[0].keys()]
                if missing_columns:
                    messagebox.showerror("Error", f"File must contain columns: {', '.join(required_columns)}")
                    return
            
            # Load accounts
            self.loaded_accounts = []
            self.accounts_listbox.delete(0, END)
            
            for account in accounts_data:
                email = str(account['email']).strip()
                password = str(account['password']).strip()
                
                if email and password:
                    self.loaded_accounts.append({'email': email, 'password': password})
                    self.accounts_listbox.insert(END, email)
            
            self.log_message(f"✅ Loaded {len(self.loaded_accounts)} accounts", "SUCCESS")
            
        except Exception as e:
            error_msg = f"Error loading file: {str(e)}"
            self.log_message(error_msg, "ERROR")
            messagebox.showerror("Error", error_msg)
    
    def start_single_generation(self):
        """Start single account OAuth generation"""
        email = self.single_email.get().strip()
        password = self.single_password.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already in progress")
            return
        
        # Start processing in separate thread
        self.current_thread = threading.Thread(
            target=self._run_single_generation,
            args=(email, password),
            daemon=True
        )
        self.current_thread.start()
    
    def start_batch_generation(self):
        """Start batch OAuth generation"""
        if not self.loaded_accounts:
            messagebox.showerror("Error", "Please load accounts first")
            return
        
        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already in progress")
            return
        
        # Start processing in separate thread
        self.current_thread = threading.Thread(
            target=self._run_batch_generation,
            daemon=True
        )
        self.current_thread.start()
    
    def _run_single_generation(self, email: str, password: str):
        """Run single account generation in thread"""
        try:
            # Setup processing state
            self.root.after(0, self._start_processing, 1)
            
            # Run async processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self._process_single_account(email, password))
            self.results = [result]
            
            # Update UI
            self.root.after(0, self._finish_processing)
            
        except Exception as e:
            self.root.after(0, self._handle_processing_error, str(e))
        finally:
            if 'loop' in locals():
                loop.close()
    
    def _run_batch_generation(self):
        """Run batch generation in thread"""
        try:
            # Setup processing state
            self.root.after(0, self._start_processing, len(self.loaded_accounts))
            
            # Run async processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.results = loop.run_until_complete(self._process_batch_accounts())
            
            # Update UI
            self.root.after(0, self._finish_processing)
            
        except Exception as e:
            self.root.after(0, self._handle_processing_error, str(e))
        finally:
            if 'loop' in locals():
                loop.close()
    
    async def _process_single_account(self, email: str, password: str) -> Dict[str, Any]:
        """Process a single account"""
        try:
            self.root.after(0, self._update_current_account, email)
            
            # Update configuration with current settings
            self._update_config_from_gui()
            
            # Create OAuth manager
            oauth_manager = OAuthCredentialsManager()
            
            # Process account
            result = await oauth_manager.complete_oauth_setup(email, password)
            
            # Handle different result types
            if result.get('verification_required', False):
                # Email verification required - this is handled gracefully
                self.root.after(0, self._increment_verification)
                self.root.after(0, self.log_message, f"📧 Verification required: {email} - Report saved", "WARNING")
                return result
            elif result['success']:
                self.root.after(0, self._increment_success)
                self.root.after(0, self.log_message, f"✅ Success: {email}", "SUCCESS")
            else:
                self.root.after(0, self._increment_failed)
                self.root.after(0, self.log_message, f"❌ Failed: {email}", "ERROR")
            
            return result
            
        except Exception as e:
            log_error(e, "single_account_processing", additional_data={'email': email})
            self.root.after(0, self._increment_failed)
            self.root.after(0, self.log_message, f"❌ Error processing {email}: {str(e)}", "ERROR")
            
            return {
                'success': False,
                'email': email,
                'errors': [str(e)],
                'steps_completed': [],
                'files_created': []
            }
    
    async def _process_batch_accounts(self) -> List[Dict[str, Any]]:
        """Process batch accounts with concurrency control"""
        results = []
        semaphore = asyncio.Semaphore(self.concurrent_limit.get())
        
        async def process_account_with_semaphore(account):
            async with semaphore:
                if self.stop_requested:
                    return None
                return await self._process_single_account(account['email'], account['password'])
        
        # Create tasks
        tasks = [
            process_account_with_semaphore(account) 
            for account in self.loaded_accounts
        ]
        
        # Process with progress updates
        completed = 0
        for task in asyncio.as_completed(tasks):
            if self.stop_requested:
                break
                
            result = await task
            if result:
                results.append(result)
            
            completed += 1
            progress = (completed / len(self.loaded_accounts)) * 100
            self.root.after(0, self._update_progress, progress)
        
        return results
    
    def _start_processing(self, total_count: int):
        """Start processing state"""
        self.is_processing = True
        self.stop_requested = False
        self.stop_btn.config(state=NORMAL)
        
        # Reset statistics
        self.stats = {
            'total': total_count,
            'successful': 0,
            'failed': 0,
            'in_progress': 0,
            'start_time': datetime.now()
        }
        
        self.total_accounts.set(total_count)
        self.successful_accounts.set(0)
        self.failed_accounts.set(0)
        self.verification_accounts.set(0)
        self.success_rate.set("0%")
        self.progress_var.set(0)
        self.status_text.set("Processing...")
        
        self.log_message(f"Started processing {total_count} account(s)")
    
    def _finish_processing(self):
        """Finish processing state"""
        self.is_processing = False
        self.stop_btn.config(state=DISABLED)
        self.status_text.set("Completed")
        self.current_account.set("")
        self.progress_var.set(100)
        
        # Calculate final statistics
        total = len(self.results)
        successful = len([r for r in self.results if r.get('success', False)])
        failed = total - successful
        rate = (successful / total * 100) if total > 0 else 0
        
        self.success_rate.set(f"{rate:.1f}%")
        
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        self.log_message(f"🎉 Processing completed in {duration:.1f}s. Success rate: {rate:.1f}%", "SUCCESS")
    
    def _handle_processing_error(self, error_msg: str):
        """Handle processing error"""
        self.is_processing = False
        self.stop_btn.config(state=DISABLED)
        self.status_text.set("Error")
        self.log_message(f"❌ Processing error: {error_msg}", "ERROR")
        messagebox.showerror("Processing Error", error_msg)
    
    def _update_current_account(self, email: str):
        """Update current account display"""
        self.current_account.set(email)
    
    def _update_progress(self, progress: float):
        """Update progress bar"""
        self.progress_var.set(progress)
    
    def _increment_success(self):
        """Increment success counter"""
        current = self.successful_accounts.get()
        self.successful_accounts.set(current + 1)
        self._update_success_rate()
    
    def _increment_failed(self):
        """Increment failed counter"""
        current = self.failed_accounts.get()
        self.failed_accounts.set(current + 1)
        self._update_success_rate()
    
    def _increment_verification(self):
        """Increment verification counter"""
        current = self.verification_accounts.get()
        self.verification_accounts.set(current + 1)
        self._update_success_rate()
    
    def _update_success_rate(self):
        """Update success rate display"""
        total = self.successful_accounts.get() + self.failed_accounts.get() + self.verification_accounts.get()
        if total > 0:
            rate = (self.successful_accounts.get() / total) * 100
            self.success_rate.set(f"{rate:.1f}%")
    
    def _update_config_from_gui(self):
        """Update configuration from GUI settings"""
        self.config.browser.headless = self.headless_mode.get()
        self.config.automation.stealth_mode = self.stealth_mode.get()
        self.config.automation.max_retries = self.retry_attempts.get()
        self.config.automation.concurrent_limit = self.concurrent_limit.get()
    
    def stop_processing(self):
        """Stop current processing"""
        self.stop_requested = True
        self.status_text.set("Stopping...")
        self.log_message("⏹️ Stop requested", "WARNING")
    
    def save_settings(self):
        """Save current settings"""
        try:
            self._update_config_from_gui()
            config_manager = ConfigManager()
            config_manager.save_config(self.config)
            self.log_message("✅ Settings saved", "SUCCESS")
            messagebox.showinfo("Success", "Settings saved successfully")
        except Exception as e:
            error_msg = f"Error saving settings: {str(e)}"
            self.log_message(error_msg, "ERROR")
            messagebox.showerror("Error", error_msg)
    
    def open_output_folder(self):
        """Open output folder"""
        try:
            output_dir = Path(self.config.paths.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(output_dir))
        except Exception as e:
            self.log_message(f"Error opening output folder: {str(e)}", "ERROR")
    
    def open_reports_folder(self):
        """Open reports folder"""
        try:
            # Use the email reporter's base directory
            reports_dir = email_reporter.base_reports_dir
            reports_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(reports_dir))
            self.log_message(f"📁 Opened reports folder: {reports_dir}", "INFO")
        except Exception as e:
            self.log_message(f"Error opening reports folder: {str(e)}", "ERROR")
    
    def export_report(self):
        """Export processing report"""
        if not self.results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        try:
            # Generate report
            oauth_manager = OAuthCredentialsManager()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            report = loop.run_until_complete(oauth_manager.generate_report(self.results))
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = Path(self.config.paths.reports_dir) / f"oauth_report_{timestamp}.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.log_message(f"📊 Report exported: {report_file}", "SUCCESS")
            messagebox.showinfo("Success", f"Report exported to:\n{report_file}")
            
        except Exception as e:
            error_msg = f"Error exporting report: {str(e)}"
            self.log_message(error_msg, "ERROR")
            messagebox.showerror("Error", error_msg)
        finally:
            if 'loop' in locals():
                loop.close()
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(END, formatted_message, level)
        self.log_text.see(END)
        
        # Also log to file
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "SUCCESS":
            self.logger.info(message)
        else:
            self.logger.info(message)
    
    def clear_log(self):
        """Clear log display"""
        self.log_text.delete(1.0, END)
    
    def run(self):
        """Start the GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
            messagebox.showerror("Application Error", str(e))

def main():
    """Main entry point"""
    try:
        # Initialize error handler
        error_handler.setup_logging()
        
        # Create and run GUI
        app = GmailOAuthGUI()
        app.run()
        
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()