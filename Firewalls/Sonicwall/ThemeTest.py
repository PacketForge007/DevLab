VERSION = "1.1.0"  # Update this for every new release

import pandas as pd
import re
import os
import tkinter as tk
from tkinter import Tk, Text, Scrollbar, END, filedialog, messagebox, ttk
from datetime import datetime
import ipaddress
import sys
import subprocess
import shutil

# Network updater info
NETWORK_PATH = r"\\192.168.7.16\SonicWallTool\\"

DEFAULT_PASSWORD = "Admin@12345"

def version_tuple(v):
    return tuple(int(x) for x in v.split('.'))


def launch_updater(latest_version):
    updater_path = os.path.join(os.getcwd(), "SonicWallToolUpdater.exe")
    current_exe = os.path.join(os.getcwd(), "SonicWallTool.exe")
    old_exe = os.path.join(os.getcwd(), "SonicWallTool_Old.exe")

    # Remove dots from version
    version_no_dots = latest_version.replace(".", "")
    network_exe = os.path.join(NETWORK_PATH, f"SonicWallTool_v{version_no_dots}.exe")

    if not os.path.exists(updater_path):
        messagebox.showerror("Updater Missing", "Updater program not found.")
        return False

    if not os.path.exists(network_exe):
        messagebox.showerror("Update Not Found",f"Update file not found on server:\n{os.path.basename(network_exe)}")
        return False

    try:
        # Backup current exe if it exists
        if os.path.exists(current_exe):
            if os.path.exists(old_exe):
                os.remove(old_exe) # remove old backup

            os.rename(current_exe, old_exe)

        #Launch updater
        subprocess.Popen([updater_path, latest_version, NETWORK_PATH])
        return True
    except Exception as e:
        messagebox.showerror("Update Failed", str(e))
        return False


def check_for_updates(auto=False):
    latest_version_file = os.path.join(NETWORK_PATH, "latest_version.txt")

    try:
        with open(latest_version_file, "r") as f:
            latest_version = f.read().strip()
    except Exception:
        if not auto:
            messagebox.showerror(
                "Update Check Failed",
                "Could not connect to update server."
            )
        return  # Keep app running

    current_version = version_tuple(VERSION)
    new_version = version_tuple(latest_version)

    # Only continue if latest_version is greater than current_version
    if new_version > current_version:
        answer = True if auto else messagebox.askyesno(
            "Update Available",
            f"Version {latest_version} is available.\nUpdate now?"
        )

        if answer:
            # Disable Exit menu while updating
            file_menu.entryconfig(EXIT_MENU_INDEX, state="disabled")

            started = launch_updater(latest_version)

            if started:
                sys.exit()
            else:
                # Re-enable Exit if updater failed
                file_menu.entryconfig(EXIT_MENU_INDEX, state="normal")

    else:
        if not auto:
            messagebox.showinfo(
                "No Update",
                "You already have the latest version."
            )


# User template
USER_TEMPLATE_COLUMNS = ["Username", "Password", "Group"]
USER_TEMPLATE_DATA = [
    ["User1", "Admin@1234", ""],
    ["User2", "Admin@1234", "Group1"],
    ["User3", "Admin@1234", "Group1, Group2"]
]

# Address Object template
ADDRESS_TEMPLATE_COLUMNS = ["Name", "Address", "Zone", "Group"]
ADDRESS_TEMPLATE_DATA = [
    ["Abc", "172.16.1.0/24", "LAN", "Group1"],
    ["Def", "192.168.10.1", "LAN", "Group1, Group2"],
    ["Ghi", "100.100.100.100", "WAN", "Telnet Grp"],
    ["Jkl_FQDN", "google.com", "WAN", "FQDN_Grp1"],
    ["Mno", "*.facebook.com", "WAN", "FQDN_Grp2"],
    ["Pqr", "00:11:22:aa:bb:cc", "LAN", "Group2"],
    ["Stu", "10.10.1.1-10.10.1.10", "LAN", ""]
]

# Service Object template
SERVICE_TEMPLATE_COLUMNS = ["Name", "Protocol", "Port", "Group"]
SERVICE_TEMPLATE_DATA = [
    ["Abc", "tcp", 22, "SSH_Grp"],
    ["Def", "udp", 22, "SSH_Grp, SSH_Grp2"],
    ["Ghi", "tcp", 23, "Telnet_Grp"],
    ["Yz", "tcp", "25-26", ""]
]

# Group template
GROUP_TEMPLATE_COLUMNS = ["Group", "Member"]
GROUP_TEMPLATE_DATA = [
    ["Group1", ""],
    ["Group2", "User1"],
    ["Group3", "User2, User3"]
]


def export_template(columns, data, default_filename):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")],
        initialfile=default_filename
    )
    if file_path:
        try:
            df = pd.DataFrame(data, columns=columns)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Template Exported", f"Template saved as:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


def is_valid_password(pwd):
    return (
        len(pwd) >= 8 and
        re.search(r'[A-Z]', pwd) and
        re.search(r'[a-z]', pwd) and
        re.search(r'[0-9]', pwd) and
        re.search(r'[^A-Za-z0-9]', pwd)
    )

def needs_quotes(s):
    return bool(re.search(r'[\s_\-\W]', s))

def generate_user_command(username, password, group_list):
    logs = []
    if not username:
        logs.append("# Skipped: Empty username")
        return [], logs
    if not password or pd.isna(password):
        password = DEFAULT_PASSWORD
    if not is_valid_password(password):
        logs.append(f"# Skipped {username}: Password does not meet complexity requirements")
        return [], logs
    quoted_username = f'"{username}"' if needs_quotes(username) else username
    quoted_password = f'"{password}"'
    cmd = f"user {quoted_username} password {quoted_password}"
    if group_list:
        quoted_groups = [f'"{grp.strip()}"' for grp in group_list if grp.strip()]
        if quoted_groups:
            cmd += f" member-of {','.join(quoted_groups)}"
    return [cmd], logs

def detect_type(address):
    try:
        if '/' in address:
            ip_part, mask_part = address.split("/", 1)
            if (re.match(r'^\d+\.\d+\.\d+\.\d+$', mask_part) and mask_part == "255.255.255.255") or mask_part == "32":
                return 'host'
            ipaddress.IPv4Network(address, strict=False)
            return 'network'
        ipaddress.IPv4Address(address)
        return 'host'
    except:
        pass
    if re.match(r'^\d+\.\d+\.\d+\.\d+\s*-\s*\d+\.\d+\.\d+\.\d+$', address.strip()):
        return 'range'
    if re.match(r'^(\*\.)?([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$', address.strip()):
        return 'fqdn'
    if re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', address.strip()):
        return 'mac'
    return 'unknown'

def generate_address_command(name, address, zone):
    if not address or pd.isna(address) or str(address).strip().lower() == "nan":
        return [], [f"# Skipped {name or 'Unnamed'}: Address is missing"]
    
    if not zone or pd.isna(zone) or str(zone).strip().lower() == "nan":
        return [], [f"# Skipped {name or address or 'Unnamed'}: Zone is missing"]

    name = name if pd.notna(name) and str(name).strip().lower() != "nan" and str(name).strip() else address
    quoted_name = f'"{name}"' if needs_quotes(name) else name
    quoted_zone = f'"{zone}"'
    
    addr_type = detect_type(address)

    if addr_type == 'host':
        if '/' in address:
            ip_part, mask_part = address.split("/", 1)
            ip_part.strip()
            return [f"address-object ipv4 {quoted_name} host {ip_part} zone {quoted_zone}"], []
        return [f"address-object ipv4 {quoted_name} host {address} zone {quoted_zone}"], []
    elif addr_type == 'network':
        net = ipaddress.IPv4Network(address, strict=False)
        return [f"address-object ipv4 {quoted_name} network {net.network_address} /{net.prefixlen} zone {quoted_zone}"], []
    elif addr_type == 'range':
        ip1, ip2 = [ip.strip() for ip in address.split('-')]
        return [f"address-object ipv4 {quoted_name} range {ip1} {ip2} zone {quoted_zone}"], []
    elif addr_type == 'fqdn':
        return [f"address-object fqdn {quoted_name} domain {address.strip()} zone {quoted_zone}", "exit"], []
    elif addr_type == 'mac':
        return [f"address-object mac {quoted_name} address {address.strip()} zone {quoted_zone}", "exit"], []
    else:
        return [], [f"# Skipped {name}: Unknown address format '{address}'"]

# New function to generate service-object command
def generate_service_command(name, protocol, port):
    logs = []
    if not name or pd.isna(name) or str(name).strip().lower() == "nan" or not str(name).strip():
        logs.append("# Skipped: Empty service name")
        return [], logs
    if not protocol or pd.isna(protocol) or str(protocol).strip().lower() == "nan" or not str(protocol).strip():
        logs.append(f"# Skipped {name}: Protocol missing")
        return [], logs
    if not port or pd.isna(port) or str(port).strip().lower() == "nan" or not str(port).strip():
        logs.append(f"# Skipped {name}: Port missing")
        return [], logs

    name = str(name).strip()
    protocol = str(protocol).strip().lower()
    port = str(port).strip()

    valid_protocols = {
        "6over4", "ah", "eigrp", "esp", "gre", "icmp", "icmpv6", "icmpv6-custom",
        "igmp", "l2tp", "ospf", "pim", "tcp", "udp"
    }
    if protocol not in valid_protocols:
        logs.append(f"# Skipped {name}: Invalid protocol '{protocol}'")
        return [], logs

    # Check port format
    if '-' in port:
        parts = port.split('-')
        if len(parts) != 2:
            logs.append(f"# Skipped {name}: Invalid port range '{port}'")
            return [], logs
        p_start, p_end = parts[0].strip(), parts[1].strip()
        if not p_start.isdigit() or not p_end.isdigit():
            logs.append(f"# Skipped {name}: Port range contains non-numeric values '{port}'")
            return [], logs
        quoted_names= f'"{name}"' if needs_quotes(name) else name
        cmd = f'service-object {quoted_names} {protocol} {p_start} {p_end}'
    else:
        if not port.isdigit():
            logs.append(f"# Skipped {name}: Invalid port '{port}'")
            return [], logs
        quoted_names= f'"{name}"' if needs_quotes(name) else name
        cmd = f'service-object {quoted_names} {protocol} {port} {port}'

    return [cmd], logs

def generate_group_command(group_name, members, row_number=None):
    logs = []

    def quote_name(name):
        """
        Wrap name in double quotes if it contains spaces, hyphens, underscores, or other non-alphanumeric characters.
        """
        if not name:
            return ""
        name = str(name).strip()
        if any(c in name for c in " -_") or not name.isalnum():
            return f'"{name}"'
        return name

    if not group_name or pd.isna(group_name) or not str(group_name).strip() or str(group_name).strip().lower() == "nan":
        row_info = f"row {row_number}" if row_number is not None else ""
        logs.append(f"# Skipped {row_info}: Empty group name")
        return [], logs

    group_name = quote_name(group_name)
    cmds = [f"group {group_name}"]

    if members and pd.notna(members):
        member_list = [m.strip() for m in str(members).split(',') if m.strip()]
        for m in member_list:
            m_quoted = quote_name(m)
            cmds.append(f"member {m_quoted}")

    cmds.append("exit")
    return cmds, logs


class DarkModeToggle(tk.Frame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.is_dark = False

        self.config(width=120, height=50, bg=master.cget("bg"))
        self.canvas = tk.Canvas(self, width=120, height=50, bg=master.cget("bg"), highlightthickness=0)
        self.canvas.pack()

        # Draw background rounded rectangle
        self.bg_rect = self.canvas.create_rectangle(10, 15, 110, 35, fill='#ddd', outline='#ccc', width=2, tags="bg")

        # Draw the circle (knob)
        self.circle = self.canvas.create_oval(12, 12, 48, 48, fill='white', outline='#bbb', width=2, tags="circle")

        # Text labels
        self.text_light = self.canvas.create_text(30, 25, text="Light Mode", fill="#333", font=('Arial', 10, 'bold'))
        self.text_dark = self.canvas.create_text(90, 25, text="Dark Mode", fill="#aaa", font=('Arial', 10))

        # Bind click
        self.canvas.tag_bind("circle", "<Button-1>", self.toggle)
        self.canvas.tag_bind("bg", "<Button-1>", self.toggle)
        self.canvas.tag_bind(self.text_light, "<Button-1>", self.toggle)
        self.canvas.tag_bind(self.text_dark, "<Button-1>", self.toggle)

    def toggle(self, event=None):
        if self.is_dark:
            # Switch to light
            self.canvas.move(self.circle, -60, 0)
            self.canvas.itemconfig(self.bg_rect, fill="#ddd")
            self.canvas.itemconfig(self.text_light, fill="#333", font=('Arial', 10, 'bold'))
            self.canvas.itemconfig(self.text_dark, fill="#aaa", font=('Arial', 10))
            self.is_dark = False
        else:
            # Switch to dark
            self.canvas.move(self.circle, 60, 0)
            self.canvas.itemconfig(self.bg_rect, fill="#444")
            self.canvas.itemconfig(self.text_light, fill="#aaa", font=('Arial', 10))
            self.canvas.itemconfig(self.text_dark, fill="#eee", font=('Arial', 10, 'bold'))
            self.is_dark = True

        if self.command:
            self.command(self.is_dark)


class SonicToolApp:
    def __init__(self, root):
        root.title(f"SonicWallTool_v{VERSION.replace(".", "")}")
        root.geometry("900x650")
        root.resizable(True, True)
        self.root = root

        # Get the folder where the script or exe is located
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Build the path to your icon dynamically
        icon_path = os.path.join(base_path, "Sonic.ico")  # Icon must be in the same folder

        root.iconbitmap(icon_path)
        style = ttk.Style()
        style.theme_use("default")

        # Create toggle and place it top-right above tabs
        self.dark_mode_toggle = DarkModeToggle(root, command=self.switch_theme)
        self.dark_mode_toggle.grid(row=0, column=1, sticky="ne", padx=10, pady=10)  # Adjust position as needed

        # Create Notebook
        self.tabs = ttk.Notebook(root)
        self.tabs.grid(row=1, column=0, columnspan=2, sticky="nsew")
        # Make the grid expandable
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=0)  # Toggle column stays minimal
        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)
        self.tab3 = ttk.Frame(self.tabs)
        self.tab4 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab1, text="Local User Generator")
        self.tabs.add(self.tab2, text="Address Object Generator")
        self.tabs.add(self.tab3, text="Service Object Generator")
        self.tabs.add(self.tab4, text="User Group Generator")
        self.tabs.grid(row=1, column=0, columnspan=2, sticky="nsew")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self.build_user_tab(self.tab1)
        self.build_address_tab(self.tab2)
        self.build_service_tab(self.tab3)
        self.build_group_tab(self.tab4)

    def build_common_layout(self, tab, title1):
        ttk.Label(tab, text=title1).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        entry_input = ttk.Entry(tab, width=60)
        entry_input.grid(row=0, column=1, padx=5, pady=5)
        btn_input = ttk.Button(tab, text="Browse", command=lambda: self.browse(entry_input, False))
        btn_input.grid(row=0, column=2, padx=5)

        ttk.Label(tab, text="Select output folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        entry_output = ttk.Entry(tab, width=60)
        entry_output.grid(row=1, column=1, padx=5, pady=5)
        btn_output = ttk.Button(tab, text="Browse", command=lambda: self.browse(entry_output, True))
        btn_output.grid(row=1, column=2, padx=5)

        lbl_log = ttk.Label(tab, text="Logs:")
        lbl_log.grid(row=2, column=0, sticky="nw", padx=5)
        txt_log = Text(tab, height=18, wrap="word")
        txt_log.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)
        sbar = Scrollbar(tab, command=txt_log.yview)
        sbar.grid(row=2, column=3, sticky="ns")
        txt_log.config(yscrollcommand=sbar.set)
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=3, column=1, columnspan=2, pady=10)
        return entry_input, entry_output, txt_log, btn_frame

    def build_user_tab(self, tab):
        self.user_input, self.user_output, self.user_log, btn_frame = self.build_common_layout(tab, "Select Excel file for User Generation:")
        ttk.Button(btn_frame, text="Generate Script", command=self.run_user_script).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Copy Logs", command=lambda: self.copy_logs(self.user_log)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Export Logs", command=lambda: self.export_logs(self.user_log)).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Clear Logs", command=lambda: self.clear_logs(self.user_log)).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Export Template", command=lambda: export_template(USER_TEMPLATE_COLUMNS,USER_TEMPLATE_DATA, "UserTemplate.xlsx")).grid(row=0, column=4, padx=5)
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(1, weight=1)

    def build_address_tab(self, tab):
        self.addr_input, self.addr_output, self.addr_log, btn_frame = self.build_common_layout(tab, "Select Excel file for Address Objects:")
        ttk.Button(btn_frame, text="Generate Script", command=self.run_address_script).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Copy Logs", command=lambda: self.copy_logs(self.addr_log)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Export Logs", command=lambda: self.export_logs(self.addr_log)).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Clear Logs", command=lambda: self.clear_logs(self.addr_log)).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Export Template", command=lambda: export_template(ADDRESS_TEMPLATE_COLUMNS,ADDRESS_TEMPLATE_DATA, "AddressObjectTemplate.xlsx")).grid(row=0, column=4, padx=5)
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(1, weight=1)

    def build_service_tab(self, tab):
        self.svc_input, self.svc_output, self.svc_log, btn_frame = self.build_common_layout(tab, "Select Excel file for Service Objects:")
        ttk.Button(btn_frame, text="Generate Script", command=self.run_service_script).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Copy Logs", command=lambda: self.copy_logs(self.svc_log)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Export Logs", command=lambda: self.export_logs(self.svc_log)).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Clear Logs", command=lambda: self.clear_logs(self.svc_log)).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Export Template", command=lambda: export_template(SERVICE_TEMPLATE_COLUMNS,SERVICE_TEMPLATE_DATA, "ServiceObjectTemplate.xlsx")).grid(row=0, column=4, padx=5)
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(1, weight=1)

    def build_group_tab(self, tab):
        self.grp_input, self.grp_output, self.grp_log, btn_frame = self.build_common_layout(tab, "Select Excel file for Group Generation:")
        ttk.Button(btn_frame, text="Generate Script", command=self.run_group_script).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Copy Logs", command=lambda: self.copy_logs(self.grp_log)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Export Logs", command=lambda: self.export_logs(self.grp_log)).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Clear Logs", command=lambda: self.clear_logs(self.grp_log)).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Export Template", command=lambda: export_template(GROUP_TEMPLATE_COLUMNS,GROUP_TEMPLATE_DATA, "UserGroupTemplate.xlsx")).grid(row=0, column=4, padx=5)
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(1, weight=1)

    def browse(self, entry, is_folder):
        if is_folder:
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if path:
            entry.delete(0, END)
            entry.insert(0, path)

    def log(self, text_area, message):
        text_area.insert(END, message + "\n")
        text_area.see(END)

    def clear_logs(self, text_area):
        text_area.delete(1.0, END)

    def copy_logs(self, text_area):
        logs = text_area.get("1.0", END).strip()
        if logs:
            text_area.clipboard_clear()
            text_area.clipboard_append(logs)
            text_area.update()
            messagebox.showinfo("Copied", "Logs copied to clipboard.")

    def export_logs(self, text_area):
        logs = text_area.get("1.0", END).strip()
        if not logs:
            messagebox.showinfo("No Logs", "There are no logs to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(logs)
                messagebox.showinfo("Success", f"Logs saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error saving logs", str(e))

    def run_user_script(self):
        input_path = self.user_input.get().strip()
        output_folder = self.user_output.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid Excel input file.")
            return
        if not output_folder or not os.path.isdir(output_folder):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return
        try:
            df = pd.read_excel(input_path)
            df.columns = [c.strip() for c in df.columns]
            if 'Username' not in df.columns:
                messagebox.showerror("Error", "Excel file must contain 'Username'")
                return
            ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            in_fname = os.path.basename(input_path)
            fname = os.path.splitext(in_fname)[0]
            out_fname = f"{fname}_LocalUsers_Script_{ts_file}.txt"
            full_out = os.path.join(output_folder, out_fname)
            self.log(self.user_log, f"\nLogs for {in_fname} [{ts_log}]")
            self.log(self.user_log, "-" * 70)
            with open(full_out, 'w') as f:
                for i, row in df.iterrows():
                    uname = str(row['Username']).strip() if pd.notna(row['Username']) else ''
                    if not uname:
                        self.log(self.user_log, f"# Skipped row {i+2}: Empty username")
                        continue
                    pwd = str(row['Password']).strip() if 'Password' in row and pd.notna(row['Password']) else DEFAULT_PASSWORD
                    groups = str(row['Group']).strip() if 'Group' in row and pd.notna(row['Group']) else ''
                    grp_list = [g.strip() for g in groups.split(',')] if groups else []
                    cmds, logs = generate_user_command(uname, pwd, grp_list)
                    for msg in logs: self.log(self.user_log, msg)
                    for cmd in cmds:
                        f.write(cmd + "\n")
                    if cmds: f.write("\n")
            messagebox.showinfo("Success", f"User script saved as:\n{full_out}")
        except Exception as e:
            self.log(self.user_log, f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))

    def run_address_script(self):
        input_path = self.addr_input.get().strip()
        output_folder = self.addr_output.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid Excel input file.")
            return
        if not output_folder or not os.path.isdir(output_folder):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return
        try:
            df = pd.read_excel(input_path)
            df.columns = [c.strip() for c in df.columns]
            if not {'Name', 'Address', 'Zone'}.issubset(df.columns):
                messagebox.showerror("Error", "Excel file must contain 'Name', 'Address', 'Zone'")
                return
            ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            in_fname = os.path.basename(input_path)
            fname = os.path.splitext(in_fname)[0]
            out_fname = f"{fname}_AddressObjects_{ts_file}.txt"
            full_out = os.path.join(output_folder, out_fname)
            self.log(self.addr_log, f"\nLogs for {in_fname} [{ts_log}]")
            self.log(self.addr_log, "-"*70)
            address_groups = {}  # {group_name: set((object_name, object_type))}
            with open(full_out, 'w') as f:
                for i, row in df.iterrows():
                    name = str(row['Name']).strip() if pd.notna(row['Name']) else ''
                    addr = str(row['Address']).strip() if pd.notna(row['Address']) else ''
                    zone = str(row['Zone']).strip() if pd.notna(row['Zone']) else ''
                    grp_raw = str(row['Group']).strip() if 'Group' in row and pd.notna(row['Group']) else ''
                    groups = [g.strip() for g in grp_raw.split(',') if g.strip()]
                    cmds, logs = generate_address_command(name, addr, zone)
                    for msg in logs: self.log(self.addr_log, msg)
                    for cmd in cmds:
                        f.write(cmd + "\n")
                    if cmds: 
                        f.write("\n")
                        addr_type = detect_type(addr)
                        obj_type = 'ipv4' if addr_type in ('host', 'network', 'range') else addr_type
                        obj_name = name or addr

                        for grp in groups:
                            address_groups.setdefault(grp, set()).add((obj_name, obj_type))

                for grp, members in address_groups.items():
                    first_obj_type = next(iter(members))[1]
                    grp_type = 'ipv4' if all(obj_type == 'ipv4' for _, obj_type in members) else 'ipv6'
                    quoted_grp = f'"{grp}"' if needs_quotes(grp) else grp

                    f.write(f'address-group {grp_type} {quoted_grp}\n')

                    for obj_name, obj_type in sorted(members):
                        quoted_obj = f'"{obj_name}"' if needs_quotes(obj_name) else obj_name
                        f.write(f'address-object {obj_type} {quoted_obj}\n')
                    f.write("exit\n\n")

            messagebox.showinfo("Success", f"Address object script saved as:\n{full_out}")
        except Exception as e:
            self.log(self.addr_log, f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))

    def run_service_script(self):
        input_path = self.svc_input.get().strip()
        output_folder = self.svc_output.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid Excel input file.")
            return
        if not output_folder or not os.path.isdir(output_folder):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return
        try:
            df = pd.read_excel(input_path)
            df.columns = [c.strip() for c in df.columns]
            required_cols = {'Name', 'Protocol', 'Port'}
            if not required_cols.issubset(df.columns):
                messagebox.showerror("Error", f"Excel file must contain columns: {', '.join(required_cols)}")
                return
            ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            in_fname = os.path.basename(input_path)
            fname = os.path.splitext(in_fname)[0]
            out_fname = f"{fname}_ServiceObjects_{ts_file}.txt"
            full_out = os.path.join(output_folder, out_fname)
            self.log(self.svc_log, f"\nLogs for {in_fname} [{ts_log}]")
            self.log(self.svc_log, "-"*70)
            service_groups = {}
            with open(full_out, 'w') as f:
                for i, row in df.iterrows():
                    name = str(row['Name']).strip() if pd.notna(row['Name']) else ''
                    protocol = str(row['Protocol']).strip() if pd.notna(row['Protocol']) else ''
                    port = str(row['Port']).strip() if pd.notna(row['Port']) else ''
                    grp_raw = str(row['Group']).strip() if 'Group' in row and pd.notna(row['Group']) else ''
                    groups = [g.strip() for g in grp_raw.split(',') if g.strip()]
                    cmds, logs = generate_service_command(name, protocol, port)
                    for msg in logs: self.log(self.svc_log, msg)
                    for cmd in cmds:
                        f.write(cmd + "\n")
                    if cmds:
                        f.write("\n")
                        for grp in groups:
                            service_groups.setdefault(grp, set()).add(name)
                for grp, members in service_groups.items():
                    quoted_grp = f'"{grp}"' if needs_quotes(grp) else grp
                    f.write(f'service-group {quoted_grp}\n')

                    for svc in sorted(members):
                        quoted_svc = f'"{svc}"' if needs_quotes(svc) else svc
                        f.write(f'service-object {quoted_svc}\n')
                    f.write("exit\n\n")

            messagebox.showinfo("Success", f"Service object script saved as:\n{full_out}")
        except Exception as e:
            self.log(self.svc_log, f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))

    def run_group_script(self):
        input_path = self.grp_input.get().strip()
        output_folder = self.grp_output.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid Excel input file.")
            return
        if not output_folder or not os.path.isdir(output_folder):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return
        try:
            df = pd.read_excel(input_path)
            df.columns = [c.strip() for c in df.columns]
            if 'Group' not in df.columns:
                messagebox.showerror("Error", "Excel file must contain 'Group' column")
                return
            ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            in_fname = os.path.basename(input_path)
            fname = os.path.splitext(in_fname)[0]
            out_fname = f"{fname}_LocalGroups_{ts_file}.txt"
            full_out = os.path.join(output_folder, out_fname)
            self.log(self.grp_log, f"\nLogs for {in_fname} [{ts_log}]")
            self.log(self.grp_log, "-" * 70)
            with open(full_out, 'w') as f:
                for i, row in df.iterrows():
                    group_name = str(row['Group']).strip() if pd.notna(row['Group']) else ''
                    members = str(row['Member']).strip() if 'Member' in row and pd.notna(row['Member']) else ''
                    cmds, logs = generate_group_command(group_name, members, row_number=i+2)
                    for msg in logs: self.log(self.grp_log, msg)
                    for cmd in cmds:
                        f.write(cmd + "\n")
                    if cmds: f.write("\n")
            messagebox.showinfo("Success", f"Local Group script saved as:\n{full_out}")
        except Exception as e:
            self.log(self.grp_log, f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))

    def switch_theme(self, is_dark):
        style = ttk.Style()
        if is_dark:
            # Change to a dark theme or simulate dark mode
            style.theme_use("clam")  # or "alt" or "vista" - test which looks better for dark
            # You can add manual color changes if needed:
            self.set_background_colors(dark=True)
        else:
            style.theme_use("default")
            self.set_background_colors(dark=False)

    def set_background_colors(self, dark=False):
        bg_color = "#2e2e2e" if dark else "white"
        fg_color = "white" if dark else "black"
        # Change main window bg
        self.root.config(bg=bg_color)

        # Change tabs bg - ttk tabs are tricky, so customize frames inside tabs
        for tab in [self.tab1, self.tab2, self.tab3, self.tab4]:
            tab.config(bg=bg_color)
            # Change all labels, buttons, entries, text background inside tabs
            for widget in tab.winfo_children():
                cls_name = widget.winfo_class()
                try:
                    if cls_name == "TLabel" or cls_name == "Label":
                        widget.config(background=bg_color, foreground=fg_color)
                    elif cls_name == "TEntry" or cls_name == "Entry":
                        widget.config(background="white" if not dark else "#555555", foreground=fg_color)
                    elif cls_name == "Text":
                        widget.config(background="#333333" if dark else "white", foreground=fg_color)
                    elif cls_name == "TButton" or cls_name == "Button":
                        widget.config(background=bg_color, foreground=fg_color)
                except:
                    pass

def confirm_exit():
    if messagebox.askyesno("Exit", "Are you sure you want to exit SonicWallTool?"):
        root.quit()

def show_about():
    messagebox.showinfo(
        "About SonicWall Tool",
        f"SonicWall Tool\n\nVersion: {VERSION}\n\nDeveloped for internal use only."
    )

if __name__ == "__main__":
    root = tk.Tk()

    # Create menu bar
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=confirm_exit)

    # Make it accessible in other functions
    EXIT_MENU_INDEX = 0

    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Check for Updates", command=lambda: check_for_updates(auto=False))
    help_menu.add_separator()
    help_menu.add_command(label="About", command=show_about)

    # Launch main app
    app = SonicToolApp(root)

    # Automatically check updates at startup
    # root.after(1000, lambda: check_for_updates(auto=True))

    root.mainloop()



