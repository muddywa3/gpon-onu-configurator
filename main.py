import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

from olt_command import execute_gpon_config, build_gpon_commands

COLORS = {
    "bg":        "#f4f7fb",
    "card":      "#ffffff",
    "header":    "#1e3c72",
    "primary":   "#2a5299",
    "primary_h": "#1e3c72",
    "text":      "#2d3748",
    "muted":     "#718096",
    "log_bg":    "#0f2027",
    "log_fg":    "#7cf5a0",
    "success":   "#38a169",
    "error":     "#e53e3e",
}


class GPONConfigurator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GPON ONU Configurator")
        self.geometry("940x880")
        self.minsize(840, 720)
        self.configure(bg=COLORS["bg"])

        self.vars = {}
        self.checks = {}
        self._build_style()
        self._build_ui()

    def _build_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame", background=COLORS["bg"])
        s.configure("Card.TFrame", background=COLORS["card"])
        s.configure("TLabel", background=COLORS["card"], foreground=COLORS["text"], font=("Segoe UI", 10))
        s.configure("CardTitle.TLabel", background=COLORS["card"], foreground=COLORS["header"], font=("Segoe UI", 11, "bold"))
        s.configure("Hint.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=("Segoe UI", 8, "italic"))
        s.configure("Sub.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=("Segoe UI", 9, "bold"))
        s.configure("TEntry", padding=6, fieldbackground="white")
        s.configure("TCombobox", padding=6)
        s.configure("TCheckbutton", background=COLORS["card"], foreground=COLORS["text"], font=("Segoe UI", 10))
        s.map("TCheckbutton", background=[("active", COLORS["card"])])
        s.configure("Primary.TButton", background=COLORS["primary"], foreground="white", font=("Segoe UI", 10, "bold"), padding=(16, 10), borderwidth=0)
        s.map("Primary.TButton", background=[("active", COLORS["primary_h"])])
        s.configure("Secondary.TButton", padding=(16, 10), font=("Segoe UI", 10))

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["header"], height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📡", bg=COLORS["header"], fg="white", font=("Segoe UI", 22)).pack(side="left", padx=(20, 10))
        txt = tk.Frame(header, bg=COLORS["header"])
        txt.pack(side="left", pady=12)
        tk.Label(txt, text="GPON ONU Configurator", bg=COLORS["header"], fg="white", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        """tk.Label(txt, text="Automation ya ku-config ONU kwenye OLT", bg=COLORS["header"], fg="#cbd5e0", font=("Segoe UI", 9)).pack(anchor="w")"""

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        canvas = tk.Canvas(body, bg=COLORS["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        self.form = ttk.Frame(canvas)

        self.form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.form, anchor="nw", width=900)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        sb.pack(side="right", fill="y")

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._section_olt()
        self._section_position()
        self._section_pppoe()
        self._section_vlan()
        self._section_wifi()

        btns = ttk.Frame(self.form)
        btns.pack(fill="x", pady=(5, 12))
        
        # Save/Load buttons
        ttk.Button(btns, text="Save Config", style="Secondary.TButton", command=self._save_config).pack(side="left", padx=5)
        ttk.Button(btns, text="Load Config", style="Secondary.TButton", command=self._load_config).pack(side="left", padx=5)
        
        ttk.Button(btns, text="Safisha", style="Secondary.TButton", command=self._reset).pack(side="right", padx=5)
        self.btn_submit = ttk.Button(btns, text="generate command", style="Primary.TButton", command=self._on_submit)
        self.btn_submit.pack(side="right", padx=5)

        log_card = ttk.Frame(self.form, style="Card.TFrame", padding=12)
        log_card.pack(fill="both", expand=True, pady=(0, 15))
        ttk.Label(log_card, text="● Execution Log / Telnet Streams", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        self.log = scrolledtext.ScrolledText(
            log_card, height=11, bg=COLORS["log_bg"], fg=COLORS["log_fg"],
            font=("Consolas", 9), insertbackground="white", wrap="word", borderwidth=0, padx=10, pady=8
        )
        self.log.pack(fill="both", expand=True)
        self._log("Tayari. Jaza fields kisha bonyeza 'Anza Configuration'.\n")

        self.status = tk.Label(self, text=" Tayari", anchor="w", bg="#e2e8f0", fg=COLORS["text"], font=("Segoe UI", 9), padx=10, pady=4)
        self.status.pack(fill="x", side="bottom")

    def _card(self, title):
        card = ttk.Frame(self.form, style="Card.TFrame", padding=15)
        card.pack(fill="x", pady=6)
        ttk.Label(card, text="● " + title, style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))
        grid = ttk.Frame(card, style="Card.TFrame")
        grid.pack(fill="x")
        return grid

    def _field(self, parent, key, label, row, col, width=24, show=None, values=None, default="", hint=None):
        ttk.Label(parent, text=label).grid(row=row, column=col * 2, sticky="w", padx=(0, 8), pady=6)
        var = tk.StringVar(value=default)
        self.vars[key] = var
        w = ttk.Combobox(parent, textvariable=var, values=values, width=width - 2, state="readonly") if values else ttk.Entry(parent, textvariable=var, width=width, show=show)
        w.grid(row=row, column=col * 2 + 1, sticky="ew", padx=(0, 20), pady=6)
        parent.columnconfigure(col * 2 + 1, weight=1)
        if hint:
            ttk.Label(parent, text=hint, style="Hint.TLabel").grid(row=row + 1, column=col * 2 + 1, sticky="w", pady=(0, 4))
        return w

    def _checkbox(self, parent, key, label, row, col, default=False):
        var = tk.BooleanVar(value=default)
        self.checks[key] = var
        cb = ttk.Checkbutton(parent, text=label, variable=var)
        cb.grid(row=row, column=col, sticky="w", padx=(0, 20), pady=4)
        return cb

    def _section_olt(self):
        g = self._card("OLT Connection")
        self._field(g, "olt_ip", "OLT IP *", 0, 0, default="10.22.105.2")
        self._field(g, "olt_username", "Username *", 0, 1, default="admin")
        self._field(g, "olt_password", "Password *", 1, 0, show="•")
        
        # Add Test Mode checkbox
        test_frame = ttk.Frame(g, style="Card.TFrame")
        test_frame.grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))
        self._checkbox(test_frame, "test_mode", "Test Mode (Messagebox tu, haitaunganisha OLT ya kweli)", 0, 0, default=False)

    def _section_position(self):
        g = self._card("ONU Position")
        self._field(g, "slot", "Slot *", 0, 0, width=10, default="0")
        self._field(g, "port", "Port *", 0, 1, width=10, default="1")
        self._field(g, "onu_id", "ONU ID *", 0, 2, width=10, default="1")
        self._field(g, "gpon_sn", "GPON S/N *", 1, 0, width=30, hint="Mfano: GPON00663G65")
        self._field(g, "onu_description", "ONU Description", 1, 1, width=40)

    def _section_pppoe(self):
        g = self._card("PPPoE")
        self._field(g, "pppoe_username", "Username *", 0, 0, default="262757575@ttclpoa")
        self._field(g, "pppoe_password", "Password *", 0, 1, show="•", default="eECDWlC+pJkla+WG")

    def _section_vlan(self):
        g = self._card("VLAN")
        self._field(g, "vlan_mode", "VLAN Mode", 0, 0, values=["tag", "transparent", "translate"], default="tag")
        self._field(g, "vlan_port", "VLAN Port (ID) *", 0, 1, width=15, default="150")

    def _section_wifi(self):
        g = self._card("WiFi")
        ttk.Label(g, text="SSID", style="Sub.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))
        self._checkbox(g, "enable_ssid1", "SSID 2.4GHz", 1, 0, default=True)
        self._checkbox(g, "enable_ssid5", "SSID 5GHz", 1, 1, default=True)

        ttk.Label(g, text="LAN Port Binding", style="Sub.TLabel").grid(row=2, column=0, columnspan=4, sticky="w", pady=(14, 4))
        lan_row = ttk.Frame(g, style="Card.TFrame")
        lan_row.grid(row=3, column=0, columnspan=4, sticky="w")
        for i in range(1, 5):
            self._checkbox(lan_row, f"lan{i}", f"LAN{i}", 0, i - 1, default=True)

        ttk.Label(g, text="WiFi Credentials", style="Sub.TLabel").grid(row=4, column=0, columnspan=4, sticky="w", pady=(14, 4))
        self._field(g, "wifi_username", "WiFi SSID Name", 5, 0, default="kinuju")
        self._field(g, "wifi_shared_key", "WiFi Shared Key *", 5, 1, show="•", default="kwandu1978")

    def _log(self, text, clear=False):
        def append():
            if clear:
                self.log.delete("1.0", "end")
            self.log.insert("end", text)
            self.log.see("end")
        self.after(0, append)

    def _set_status(self, text, color=COLORS["text"]):
        self.after(0, lambda: self.status.config(text=" " + text, fg=color))

    def _reset(self):
        for v in self.vars.values():
            v.set("")
        for c in self.checks.values():
            c.set(False)
        self._log("", clear=True)
        self._log("Fomu imesafishwa.\n")
        self._set_status("Tayari")

    def _save_config(self):
        """Save current configuration to JSON file"""
        try:
            data = self._collect()
            # Remove sensitive data from save
            save_data = {k: v for k, v in data.items() if k not in ['olt_password', 'pppoe_password', 'wifi_shared_key']}
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Configuration"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(save_data, f, indent=2)
                self._log(f"Configuration saved to: {filename}\n")
                self._set_status("Configuration saved successfully", COLORS["success"])
        except Exception as e:
            self._log(f"Error saving configuration: {str(e)}\n")
            self._set_status("Failed to save configuration", COLORS["error"])

    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Configuration"
            )
            
            if filename:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Load data into form fields
                for key, value in data.items():
                    if key in self.vars:
                        self.vars[key].set(str(value))
                    elif key in self.checks:
                        self.checks[key].set(bool(value))
                
                self._log(f"Configuration loaded from: {filename}\n")
                self._log("Note: Passwords were not loaded for security reasons.\n")
                self._set_status("Configuration loaded successfully", COLORS["success"])
        except Exception as e:
            self._log(f"Error loading configuration: {str(e)}\n")
            self._set_status("Failed to load configuration", COLORS["error"])

    def _validate(self):
        required = [
            ("slot", "Slot"), ("port", "Port"), ("onu_id", "ONU ID"), ("gpon_sn", "GPON S/N"),
            ("pppoe_username", "Username"), ("pppoe_password", "Password"),
            ("vlan_port", "VLAN Port"), ("wifi_shared_key", "WiFi Shared Key")
        ]
        
        # If not in test mode, OLT connection fields are required
        if not self.checks.get("test_mode", tk.BooleanVar()).get():
            required = [
                ("olt_ip", "OLT IP"), ("olt_username", "Username"), ("olt_password", "Password")
            ] + required
        
        missing = [name for key, name in required if not self.vars[key].get().strip()]
        if missing:
            return missing

        if len(self.vars["wifi_shared_key"].get()) < 8:
            return ["WiFi Shared Key (lazima iwe herufi 8 au zaidi)"]

        gpon_sn = self.vars["gpon_sn"].get().strip()
        if not (8 <= len(gpon_sn) <= 20):
            return ["GPON S/N (lazima iwe herufi 8 hadi 20)"]
        
        # Check if GPON S/N contains valid characters (alphanumeric)
        if not all(c.isalnum() for c in gpon_sn):
            return ["GPON S/N (lazima iwe herufi na namba tu, hakuna special characters)"]

        try:
            v = int(self.vars["vlan_port"].get())
            if not (1 <= v <= 4094):
                return ["VLAN Port (1 - 4094)"]
        except ValueError:
            return ["VLAN Port (lazima iwe namba)"]

        if not any(self.checks[f"lan{i}"].get() for i in range(1, 5)):
            return ["LAN Port Binding (chagua angalau LAN moja)"]

        if not (self.checks["enable_ssid1"].get() or self.checks["enable_ssid5"].get()):
            return ["SSID (chagua angalau moja — 2.4GHz au 5GHz)"]

        return []

    def _collect(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        data.update({k: bool(v.get()) for k, v in self.checks.items()})
        return data

    def _on_submit(self):
        missing = self._validate()
        if missing:
            self._log("\n⚠ Fields zifuatazo zinahitajika:\n", clear=True)
            for m in missing:
                self._log(f"   • {m}\n")
            self._set_status("Kuna fields ambazo hazijajazwa", COLORS["error"])
            return

        data = self._collect()
        
        # Check if Test Mode is enabled
        if data.get("test_mode", False):
            self._show_test_mode_result(data)
            return
        
        self.btn_submit.config(state="disabled")
        self._set_status("Inaconfigure ONU kwenye OLT...", COLORS["primary"])
        self._log("", clear=True)

        def re_enable():
            self.after(0, lambda: self.btn_submit.config(state="normal"))

        threading.Thread(
            target=execute_gpon_config,
            args=(data, self._log, self._set_status, re_enable),
            daemon=True
        ).start()

    def _show_test_mode_result(self, data):
        """Show the generated commands in a messagebox for test mode"""
        try:
            commands = build_gpon_commands(data)
            
            # Join all commands with newlines
            command_text = "\n".join(commands)
            
            # Show in messagebox
            messagebox.showinfo(
                "Test Mode - Generated Commands",
                f"Haya ndiyo macommands yanayotakiwa kwenye OLT:\n\n{command_text}",
                parent=self
            )
            
            # Also log to the text area
            self._log("TEST MODE - Commands zilizotayarishwa:\n", clear=True)
            self._log("=" * 60 + "\n")
            for cmd in commands:
                self._log(f"> {cmd}\n")
            self._log("=" * 60 + "\n")
            self._log("✔ Test completed! Commands zimeonyeshwa kwenye messagebox.\n")
            self._set_status("Test Mode - Commands zimeonyeshwa", COLORS["success"])
            
        except Exception as e:
            messagebox.showerror(
                "Test Mode Error", 
                f"Kuna tatizo limetokea wakati wa kutengeneza commands:\n{str(e)}", 
                parent=self
            )
            self._log(f"❌ Test Mode Error: {str(e)}\n")
            self._set_status("Test Mode - Kuna tatizo limetokea", COLORS["error"])


if __name__ == "__main__":
    app = GPONConfigurator()
    app.mainloop()