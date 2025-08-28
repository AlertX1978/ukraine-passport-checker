import json
import os
import threading
import time
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import webbrowser

# Reuse existing logic from passport_check.py
import passport_check as pc


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
DEFAULT_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'default.json')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'logs')
LAST_LOG_FILE = os.path.join(SCRIPT_DIR, 'last.log')


def load_default_config() -> dict:
    try:
        with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Fallback to hardcoded defaults if default.json doesn't exist
        return {
            "email": {
                "sender": "",
                "recipient": "",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": ""
            },
            "passport_code": "",
            "check_interval_seconds": 1800,
            "timeouts": {
                "search_input_wait": 5,
                "search_button_wait": 5,
                "result_wait": 5
            },
            "translations": {
                "Статус": "Status",
                "Дата": "Date",
                "Заявку подано": "Application submitted",
                "Дані відправлено на перевірку": "Data sent for verification",
                "Дані відправлено на персоналізацію": "Data sent for personalization",
                "Документ готовий": "Document ready",
                "Документ видано": "Document issued"
            }
        }


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            "email": {
                "sender": "",
                "recipient": "",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": ""
            },
            "passport_code": "",
            "check_interval_seconds": 1800,
            "timeouts": {
                "search_input_wait": 5,
                "search_button_wait": 5,
                "result_wait": 5
            },
            "translations": {
                "Статус": "Status",
                "Дата": "Date",
                "Заявку подано": "Application submitted",
                "Дані відправлено на перевірку": "Data sent for verification",
                "Дані відправлено на персоналізацію": "Data sent for personalization",
                "Документ готовий": "Document ready",
                "Документ видано": "Document issued"
            }
        }


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)


def run_single_check(passport_code: str, timeouts: dict, send_email: bool) -> dict:
    """Perform a single passport check and return a result dict.

    Returns: {
      'ok': bool,
      'message': str,            # user-facing status text (english)
      'changed': bool,           # compared to last.log
      'log_file': Optional[str], # path to saved log file
    }
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    driver = None
    result = {
        'ok': False,
        'message': '',
        'changed': False,
        'log_file': None,
    }

    try:
        # Update config.json to keep system consistent with CLI script
        cfg = load_config()
        cfg['passport_code'] = passport_code or cfg.get('passport_code', '')
        cfg.setdefault('timeouts', {})
        cfg['timeouts']['search_input_wait'] = int(timeouts.get('search_input_wait', 5))
        cfg['timeouts']['search_button_wait'] = int(timeouts.get('search_button_wait', 5))
        cfg['timeouts']['result_wait'] = int(timeouts.get('result_wait', 5))
        save_config(cfg)

        driver = pc.setup_driver()
        url = "https://passport.mfa.gov.ua"
        driver.get(url)
        pc.wait_with_random_delay(8, 12)

        if not pc.wait_for_cloudflare(driver, None):
            raise RuntimeError("Could not bypass Cloudflare protection")

        # Find search input
        input_selectors = [
            'input[type="text"]',
            'input[name="passport"]',
            'input[class*="search"]',
            '//input[@type="text"]',
            '//input[contains(@class, "search")]',
            '//input[not(@type="hidden")]',
            'input',
        ]
        search_input = pc.find_element_safely(
            driver,
            input_selectors,
            int(cfg['timeouts'].get('search_input_wait', 5)),
            "search input",
        )
        if not search_input:
            raise RuntimeError("Could not find search input")

        # Type code
        search_input.clear()
        for ch in str(passport_code):
            search_input.send_keys(ch)
            pc.wait_with_random_delay(1, 1)  # Use integer values

        # Find and click search button
        button_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:not([type])',
            '.search-button',
            '//button[@type="submit"]',
            '//input[@type="submit"]',
            '//button[contains(text(), "Search")]',
            '//button[contains(text(), "Пошук")]',
            'button',
        ]
        search_button = pc.find_element_safely(
            driver,
            button_selectors,
            int(cfg['timeouts'].get('search_button_wait', 5)),
            "search button",
        )
        if not search_button:
            raise RuntimeError("Could not find search button")

        search_button.click()
        pc.wait_with_random_delay(3, 7)

        log_text_uk = pc.extract_passport_status(driver, int(cfg['timeouts'].get('result_wait', 5)))
        if not log_text_uk:
            raise RuntimeError("Could not extract passport status")

        log_text_en = pc.translate_ukrainian_status(log_text_uk)

        # change detection and file save similar to CLI flow
        changed = pc.compare_with_last_log(log_text_en, SCRIPT_DIR)
        log_filename = os.path.join(LOGS_DIR, f"passport_log_{time.strftime('%Y%m%d_%H%M%S')}.txt")
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(log_text_en)

        if send_email:
            try:
                pc.send_email(log_text_en, CONFIG_PATH, changed)
            except Exception:
                # Non-fatal for GUI single run
                pass

        result.update({
            'ok': True,
            'message': log_text_en,
            'changed': changed,
            'log_file': log_filename,
        })
        return result

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty()

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text, background="#FFFFE0", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class PassportGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Ukraine Passport Checker GUI')
        self.root.geometry('900x650')

        self.auto_thread = None
        self.stop_event = threading.Event()

        self.cfg = load_config()

        # UI
        self._build_ui()
        self._load_cfg_into_form()

    def _build_ui(self):
        # UI padding settings
        pad_x, pad_y = 8, 6

        # Top form frame
        form = ttk.LabelFrame(self.root, text='Settings')
        form.pack(fill='x', padx=pad_x, pady=pad_y)

        notebook = ttk.Notebook(form)
        notebook.pack(fill='x', expand=True, padx=pad_x, pady=pad_y)

        general_frame = ttk.Frame(notebook)
        email_frame = ttk.Frame(notebook)

        notebook.add(general_frame, text='General')
        notebook.add(email_frame, text='Email')

        # General settings
        row1 = ttk.Frame(general_frame)
        row1.pack(fill='x', padx=pad_x, pady=pad_y)
        
        passport_label = ttk.Label(row1, text='Passport code:')
        passport_label.pack(side='left')
        self.var_passport = tk.StringVar()
        passport_entry = ttk.Entry(row1, textvariable=self.var_passport, width=20)
        passport_entry.pack(side='left', padx=(6, 16))
        Tooltip(passport_entry, "The passport code to check.")

        interval_label = ttk.Label(row1, text='Interval (sec):')
        interval_label.pack(side='left')
        self.var_interval = tk.StringVar()
        interval_entry = ttk.Entry(row1, textvariable=self.var_interval, width=8)
        interval_entry.pack(side='left', padx=(6, 16))
        Tooltip(interval_entry, "The interval in seconds between automatic checks.")

        self.var_send_email = tk.BooleanVar(value=True)
        send_email_check = ttk.Checkbutton(row1, text='Send email', variable=self.var_send_email)
        send_email_check.pack(side='left')
        Tooltip(send_email_check, "Whether to send an email when the passport status changes.")

        row2 = ttk.Frame(general_frame)
        row2.pack(fill='x', padx=pad_x, pady=pad_y)
        
        timeouts_label = ttk.Label(row2, text='Timeouts (s):')
        timeouts_label.pack(side='left')
        Tooltip(timeouts_label, "Timeouts for various stages of the check.")

        input_label = ttk.Label(row2, text='Input')
        input_label.pack(side='left', padx=(10, 2))
        self.var_t_in = tk.StringVar()
        input_entry = ttk.Entry(row2, textvariable=self.var_t_in, width=5)
        input_entry.pack(side='left')
        Tooltip(input_entry, "Timeout for finding the search input field.")

        button_label = ttk.Label(row2, text='Button')
        button_label.pack(side='left', padx=(10, 2))
        self.var_t_btn = tk.StringVar()
        button_entry = ttk.Entry(row2, textvariable=self.var_t_btn, width=5)
        button_entry.pack(side='left')
        Tooltip(button_entry, "Timeout for finding the search button.")

        result_label = ttk.Label(row2, text='Result')
        result_label.pack(side='left', padx=(10, 2))
        self.var_t_res = tk.StringVar()
        result_entry = ttk.Entry(row2, textvariable=self.var_t_res, width=5)
        result_entry.pack(side='left')
        Tooltip(result_entry, "Timeout for waiting for the result.")

        # Email settings
        email_row1 = ttk.Frame(email_frame)
        email_row1.pack(fill='x', padx=pad_x, pady=pad_y)

        sender_label = ttk.Label(email_row1, text='Sender:')
        sender_label.pack(side='left')
        self.var_email_sender = tk.StringVar()
        sender_entry = ttk.Entry(email_row1, textvariable=self.var_email_sender, width=30)
        sender_entry.pack(side='left', padx=(6, 16))
        Tooltip(sender_entry, "The sender's email address.")

        recipient_label = ttk.Label(email_row1, text='Recipient:')
        recipient_label.pack(side='left')
        self.var_email_recipient = tk.StringVar()
        recipient_entry = ttk.Entry(email_row1, textvariable=self.var_email_recipient, width=30)
        recipient_entry.pack(side='left', padx=(6, 16))
        Tooltip(recipient_entry, "The recipient's email address.")

        email_row2 = ttk.Frame(email_frame)
        email_row2.pack(fill='x', padx=pad_x, pady=pad_y)

        smtp_server_label = ttk.Label(email_row2, text='SMTP Server:')
        smtp_server_label.pack(side='left')
        self.var_smtp_server = tk.StringVar()
        smtp_server_entry = ttk.Entry(email_row2, textvariable=self.var_smtp_server, width=30)
        smtp_server_entry.pack(side='left', padx=(6, 16))
        Tooltip(smtp_server_entry, "The SMTP server address.")

        smtp_port_label = ttk.Label(email_row2, text='SMTP Port:')
        smtp_port_label.pack(side='left')
        self.var_smtp_port = tk.StringVar()
        smtp_port_entry = ttk.Entry(email_row2, textvariable=self.var_smtp_port, width=10)
        smtp_port_entry.pack(side='left', padx=(6, 16))
        Tooltip(smtp_port_entry, "The SMTP server port.")

        email_row3 = ttk.Frame(email_frame)
        email_row3.pack(fill='x', padx=pad_x, pady=pad_y)

        username_label = ttk.Label(email_row3, text='Username:')
        username_label.pack(side='left')
        self.var_email_username = tk.StringVar()
        username_entry = ttk.Entry(email_row3, textvariable=self.var_email_username, width=30)
        username_entry.pack(side='left', padx=(6, 16))
        Tooltip(username_entry, "The username for the email account.")

        password_label = ttk.Label(email_row3, text='App Password:')
        password_label.pack(side='left')
        self.var_email_password = tk.StringVar()
        password_entry = ttk.Entry(email_row3, textvariable=self.var_email_password, width=30, show='*')
        password_entry.pack(side='left', padx=(6, 16))
        Tooltip(password_entry, "The app password for the email account. This is not your regular password.")

        email_row4 = ttk.Frame(email_frame)
        email_row4.pack(fill='x', padx=pad_x, pady=pad_y)

        link_label = tk.Label(email_row4, text="How to get a Gmail app password", fg="blue", cursor="hand2")
        link_label.pack(side='left')
        link_label.bind("<Button-1>", lambda e: self.open_link("https://support.google.com/accounts/answer/185833"))
        Tooltip(link_label, "Click to open a guide on how to generate an app password for your Google account.")

        save_button = ttk.Button(form, text='Save Config', command=self.on_save_config)
        save_button.pack(side='left', pady=pad_y, padx=(0, 10))
        Tooltip(save_button, "Save the current settings to config.json.")

        import_button = ttk.Button(form, text='Import Config', command=self.on_import_config)
        import_button.pack(side='left', pady=pad_y, padx=(0, 10))
        Tooltip(import_button, "Import settings from a .json file.")

        reset_button = ttk.Button(form, text='Reset to Default', command=self.on_reset_config)
        reset_button.pack(side='left', pady=pad_y)
        Tooltip(reset_button, "Reset the settings to their default values.")

        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(fill='x', padx=pad_x, pady=pad_y)
        ttk.Button(actions, text='Run One Check', command=self.on_run_once).pack(side='left')
        ttk.Button(actions, text='Start Auto-Check', command=self.on_start_auto).pack(side='left', padx=(10, 0))
        ttk.Button(actions, text='Stop', command=self.on_stop_auto).pack(side='left', padx=(10, 0))
        ttk.Button(actions, text='Open Logs Folder', command=self.on_open_logs).pack(side='left', padx=(10, 0))
        ttk.Button(actions, text='Open last.log', command=self.on_open_last_log).pack(side='left', padx=(10, 0))

        # Output area
        out_frame = ttk.LabelFrame(self.root, text='Output')
        out_frame.pack(fill='both', expand=True, padx=pad_x, pady=pad_y)

        self.txt = tk.Text(out_frame, wrap='word', height=20)
        self.txt.pack(fill='both', expand=True)

        # Status
        self.status = tk.StringVar(value='Ready')
        ttk.Label(self.root, textvariable=self.status).pack(fill='x', padx=8, pady=(0, 8))

    def on_reset_config(self):
        self.cfg = load_default_config()
        self._load_cfg_into_form()
        self.set_status('Settings have been reset to default.')

    def _load_cfg_into_form(self):
        self.var_passport.set(self.cfg.get('passport_code', ''))
        self.var_interval.set(str(self.cfg.get('check_interval_seconds', 1800)))
        to = self.cfg.get('timeouts', {})
        self.var_t_in.set(str(to.get('search_input_wait', 5)))
        self.var_t_btn.set(str(to.get('search_button_wait', 5)))
        self.var_t_res.set(str(to.get('result_wait', 5)))
        email_cfg = self.cfg.get('email', {})
        self.var_email_sender.set(email_cfg.get('sender', ''))
        self.var_email_recipient.set(email_cfg.get('recipient', ''))
        self.var_smtp_server.set(email_cfg.get('smtp_server', 'smtp.gmail.com'))
        self.var_smtp_port.set(str(email_cfg.get('smtp_port', 587)))
        self.var_email_username.set(email_cfg.get('username', ''))
        self.var_email_password.set(email_cfg.get('password', ''))

    def set_status(self, text: str):
        """Thread-safe status setter."""
        def _do():
            self.status.set(text)
        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.root.after(0, _do)

    def _gather_cfg_from_form(self) -> dict:
        # Update only the keys we expose
        cfg = load_config()
        cfg['passport_code'] = self.var_passport.get().strip()
        try:
            cfg['check_interval_seconds'] = max(30, int(self.var_interval.get()))
        except Exception:
            cfg['check_interval_seconds'] = 1800
        cfg.setdefault('timeouts', {})
        try:
            cfg['timeouts']['search_input_wait'] = max(1, int(self.var_t_in.get()))
        except Exception:
            cfg['timeouts']['search_input_wait'] = 5
        try:
            cfg['timeouts']['search_button_wait'] = max(1, int(self.var_t_btn.get()))
        except Exception:
            cfg['timeouts']['search_button_wait'] = 5
        try:
            cfg['timeouts']['result_wait'] = max(1, int(self.var_t_res.get()))
        except Exception:
            cfg['timeouts']['result_wait'] = 5
        cfg.setdefault('email', {})
        cfg['email']['sender'] = self.var_email_sender.get().strip()
        cfg['email']['recipient'] = self.var_email_recipient.get().strip()
        cfg['email']['smtp_server'] = self.var_smtp_server.get().strip()
        try:
            cfg['email']['smtp_port'] = int(self.var_smtp_port.get())
        except Exception:
            cfg['email']['smtp_port'] = 587
        cfg['email']['username'] = self.var_email_username.get().strip()
        cfg['email']['password'] = self.var_email_password.get().strip()
        return cfg

    def append_output(self, text: str):
        """Thread-safe append to output text box."""
        def _do():
            self.txt.insert('end', text + "\n")
            self.txt.see('end')
        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.root.after(0, _do)

    def open_link(self, url):
        webbrowser.open_new(url)

    def on_save_config(self):
        cfg = self._gather_cfg_from_form()
        save_config(cfg)
        self.set_status('Config saved')
        messagebox.showinfo('Saved', 'Configuration saved to config.json')

    def on_import_config(self):
        filepath = filedialog.askopenfilename(
            title="Import Config",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_cfg = json.load(f)
            
            # Basic validation
            if not isinstance(imported_cfg, dict):
                raise ValueError("Invalid config format: not a dictionary")

            self.cfg = imported_cfg
            self._load_cfg_into_form()
            self.set_status(f'Config imported from {os.path.basename(filepath)}')
            messagebox.showinfo('Imported', f'Configuration imported from {os.path.basename(filepath)}')

        except Exception as e:
            self.set_status(f'Import failed: {e}')
            messagebox.showerror('Import Error', f'Failed to import config: {e}')

    def on_run_once(self):
        if self.auto_thread and self.auto_thread.is_alive():
            messagebox.showwarning('Busy', 'Auto-check is running. Stop it before manual run.')
            return

        passport = self.var_passport.get().strip()
        if not passport:
            messagebox.showwarning('Missing', 'Please enter a passport code')
            return

        to = {
            'search_input_wait': self.var_t_in.get(),
            'search_button_wait': self.var_t_btn.get(),
            'result_wait': self.var_t_res.get(),
        }

        self.set_status('Running one check...')
        self.append_output('--- Running one check ---')

        def worker():
            try:
                res = run_single_check(passport, to, self.var_send_email.get())
                if res['ok']:
                    self.append_output(res['message'])
                    suffix = 'CHANGED' if res['changed'] else 'unchanged'
                    self.append_output(f"Saved log: {res['log_file']} (status {suffix})")
                    self.set_status('Done')
                else:
                    self.append_output('Check failed')
                    self.set_status('Failed')
            except Exception as e:
                self.append_output(f"Error: {e}\n{traceback.format_exc()}")
                self.set_status('Error')

        threading.Thread(target=worker, daemon=True).start()

    def on_start_auto(self):
        if self.auto_thread and self.auto_thread.is_alive():
            messagebox.showinfo('Running', 'Auto-check already running')
            return

        passport = self.var_passport.get().strip()
        if not passport:
            messagebox.showwarning('Missing', 'Please enter a passport code')
            return

        try:
            interval = max(30, int(self.var_interval.get()))
        except Exception:
            interval = 1800

        to = {
            'search_input_wait': self.var_t_in.get(),
            'search_button_wait': self.var_t_btn.get(),
            'result_wait': self.var_t_res.get(),
        }

        self.stop_event.clear()

        def loop():
            self.append_output('=== Auto-check started ===')
            while not self.stop_event.is_set():
                self.set_status('Auto-check: running')
                try:
                    res = run_single_check(passport, to, self.var_send_email.get())
                    if res['ok']:
                        self.append_output(res['message'])
                        suffix = 'CHANGED' if res['changed'] else 'unchanged'
                        self.append_output(f"Saved log: {res['log_file']} (status {suffix})")
                    else:
                        self.append_output('Check failed')
                except Exception as e:
                    self.append_output(f"Error: {e}\n{traceback.format_exc()}")

                # wait with small steps to allow responsive stop
                total = interval
                while total > 0 and not self.stop_event.is_set():
                    step = min(5, total)
                    time.sleep(step)
                    total -= step
                    self.set_status(f'Next run in {total}s')

            self.set_status('Stopped')
            self.append_output('=== Auto-check stopped ===')

        self.auto_thread = threading.Thread(target=loop, daemon=True)
        self.auto_thread.start()

    def on_stop_auto(self):
        self.stop_event.set()

    def on_open_logs(self):
        os.makedirs(LOGS_DIR, exist_ok=True)
        try:
            # Windows
            os.startfile(LOGS_DIR)  # type: ignore[attr-defined]
        except Exception:
            messagebox.showinfo('Logs', f'Logs folder: {LOGS_DIR}')

    def on_open_last_log(self):
        try:
            if os.path.exists(LAST_LOG_FILE):
                with open(LAST_LOG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.append_output('--- last.log ---')
                self.append_output(content)
            else:
                messagebox.showinfo('last.log', 'last.log not found yet')
        except Exception as e:
            messagebox.showerror('Error', str(e))


def main():
    try:
        root = tk.Tk()
        # Ensure window is properly displayed
        root.deiconify()  # Make sure window is not minimized
        root.lift()       # Bring to front
        root.focus_force() # Give focus
        
        app = PassportGUI(root)
        
        # Center the window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        print("GUI started successfully. Close the window to exit.")
        root.mainloop()
        print("GUI closed.")
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == '__main__':
    main()
