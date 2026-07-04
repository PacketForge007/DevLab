VERSION = "1.1.5"  # Update this for every new release

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
import threading
import time
import random
import requests
import ctypes


# Network updater info
# NETWORK_PATH = r"\\192.168.7.16\SonicWallTool\\"
UPDATE_BASE_URL = "http://192.168.7.16/SonicWallTool/"

DEFAULT_PASSWORD = "Admin@12345"

def version_tuple(v):
    try:
        return tuple(map(int, v.strip().split(".")))
    except Exception:
        return (0,)

def copy_with_progress(src, dst, progress_window):
    total = os.path.getsize(src)
    copied = 0
    buf_size = 1024 * 1024  # 1MB
    start_time = time.time()

    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        while True:
            if progress_window.cancelled:
                raise Exception("Update cancelled by user")

            buf = fsrc.read(buf_size)
            if not buf:
                break

            fdst.write(buf)
            copied += len(buf)

            elapsed = time.time() - start_time
            speed = (copied / 1024 / 1024) / elapsed if elapsed > 0 else 0
            percent = int((copied / total) * 100)
            remaining = total - copied
            eta = int((remaining / 1024 / 1024) / speed) if speed > 0 else "--"

            progress_window.update_download(percent, speed, eta)


def download_with_progress(url, dst, progress_window):
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    copied = 0
    start_time = time.time()

    with open(dst, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if progress_window.cancelled:
                raise Exception("Update cancelled by user")

            if chunk:
                f.write(chunk)
                copied += len(chunk)

                elapsed = time.time() - start_time
                speed = (copied / 1024 / 1024) / elapsed if elapsed > 0 else 0
                percent = int((copied / total) * 100) if total else 0
                remaining = total - copied
                eta = int((remaining / 1024 / 1024) / speed) if speed > 0 else "--"

                progress_window.update_download(percent, speed, eta)


def launch_updater(latest_version, root):
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    updater_path = os.path.join(base_path, "SonicUpdater.exe")

    version_no_dots = latest_version.replace(".", "")
    download_url = UPDATE_BASE_URL + f"SonicWallTool_v{version_no_dots}.exe"

    if not os.path.exists(updater_path):
        messagebox.showerror("Updater Missing", "Updater program not found.")
        return False

    try:
        response = requests.head(download_url, timeout=10)
        response.raise_for_status()
    except Exception:
        messagebox.showerror(
            "Update Not Found",
            f"Update file not found on server:\n{download_url}"
        )
        return False

    try:
        params = f'"{latest_version}" "{UPDATE_BASE_URL}"'

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            os.path.abspath(updater_path),
            params,
            os.path.dirname(os.path.abspath(updater_path)),
            1
        )

        if result <= 32:
            messagebox.showwarning(
                "Update Cancelled",
                "Update was cancelled or administrator access was denied."
            )
            return False

        root.destroy()
        return True

    except Exception as e:
        messagebox.showerror("Update Failed", str(e))
        return False


def check_for_updates(auto=False):
    latest_version_url = UPDATE_BASE_URL + "latest_version.txt"

    try:
        response = requests.get(latest_version_url, timeout=10)
        response.raise_for_status()
        latest_version = response.text.strip()
    except Exception:
        if not auto:
            messagebox.showerror(
                "Update Check Failed",
                "Could not connect to update server."
            )
        return

    current_version = version_tuple(VERSION)
    new_version = version_tuple(latest_version)

    if new_version > current_version:
        answer = True if auto else messagebox.askyesno(
            "Update Available",
            f"Version {latest_version} is available.\nUpdate now?"
        )

        if answer:
            file_menu.entryconfig(EXIT_MENU_INDEX, state="disabled")

            started = launch_updater(latest_version, root)

            # if started:
                # sys.exit()
            # else:
                # file_menu.entryconfig(EXIT_MENU_INDEX, state="normal")

            if not started:
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

# DHCP template
DHCP_TEMPLATE_COLUMNS = ["Name", "MAC", "IP", "Mask", "GW", "DNS"]
DHCP_TEMPLATE_DATA = [
    ["PC-01", "00:11:22:33:44:55", "192.168.1.10", "255.255.255.0", "192.168.1.1", "8.8.8.8"],
    ["PC-02", "AA:BB:CC:DD:EE:FF", "192.168.1.11", "255.255.255.0", "192.168.1.1", "8.8.8.8, 8.8.4.4"]
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
#    if not is_valid_password(password):
#        logs.append(f"# Skipped {username}: Password does not meet complexity requirements")
#        return [], logs
    quoted_username = f'"{username}"' if needs_quotes(username) else username
    quoted_password = f'"{password}"'
    cmd = f"user {quoted_username} password {quoted_password}"
#    if group_list:
#        quoted_groups = [f'"{grp.strip()}"' for grp in group_list if grp.strip()]
#        if quoted_groups:
#            cmd += f" member-of {','.join(quoted_groups)}"
    return [cmd], logs


# User Full Script
def generate_full_script(user_rows):
    all_cmds = []
    logs = []
    group_map = {}

    for _, row in user_rows.iterrows():
        username = row.get("Username")
        password = row.get("Password")
        raw_groups = row.get("Group", "")

        # ✅ Parse "Grp1, Grp2"
        if isinstance(raw_groups, str):
            group_list = [g.strip() for g in raw_groups.split(",") if g.strip()]
        else:
            group_list = []

        cmds, log = generate_user_command(username, password, group_list)
        logs.extend(log)

        if cmds:
            all_cmds.extend(cmds)

            for grp in group_list:
                group_map.setdefault(grp, []).append(username)

    if all_cmds:
        all_cmds.append("commit")
        all_cmds.append("\n")

    for grp, users in group_map.items():
        unique_users = list(dict.fromkeys(users))
        quoted_grp = f'"{grp}"' if needs_quotes(grp) else grp
        all_cmds.append(f"group {quoted_grp}")
#        all_cmds.append(f"member {', '.join(unique_users)}")
        for user in unique_users:
            quoted_user = f'"{user}"' if needs_quotes(user) else user
            all_cmds.append(f"member {quoted_user}")
        all_cmds.append("exit")

    if group_map:
        all_cmds.append("commit")

    return all_cmds, logs


# Detect Address Type
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

        port_num = int(port)

        if not (1 <= port_num <= 65535):
            logs.append(f"# Skipped {name}: Port out of range '{port}'")
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

# DHCP Static Binding
def normalize_mac(mac):
    if pd.isna(mac):
        return ""
    mac = str(mac).lower()
    mac = re.sub(r'[^a-f0-9]', '', mac)
    if len(mac) != 12:
        return ""
    return ":".join(mac[i:i+2] for i in range(0, 12, 2))


def parse_dns(dns_str):
    return [ip.strip() for ip in str(dns_str).split(",") if ip.strip()]


def format_name(name):
    if re.search(r"[^A-Za-z0-9]", str(name)):
        return f'"{name}"'
    return str(name)


def generate_dhcp_cli_script(df, log_lines):
    cli_lines = ["dhcp-server\n"]
    required_cols = ["Name", "MAC", "IP", "Mask", "GW", "DNS"]

    for index, row in df.iterrows():
        missing = [
            c for c in required_cols
            if c not in row or pd.isna(row[c]) or str(row[c]).strip() == ""
        ]
        if missing:
            log_lines.append(
                f"[Row {index+2}] Skipped: Missing {', '.join(missing)}"
            )
            continue

        mac = normalize_mac(row["MAC"])
        if not mac:
            log_lines.append(
                f"[Row {index+2}] Skipped: Invalid MAC address"
            )
            continue

        cli_lines.extend([
            f"scope static {row['IP']} {mac}",
            f"name {format_name(row['Name'])}",
            f"netmask {row['Mask']}",
            f"default-gateway {row['GW']}",
        ])

        dns = parse_dns(row["DNS"])
        if len(dns) > 0:
            cli_lines.append(f"dns server static primary {dns[0]}")
        if len(dns) > 1:
            cli_lines.append(f"dns server static secondary {dns[1]}")
        if len(dns) > 2:
            cli_lines.append(f"dns server static tertiary {dns[2]}")

        cli_lines.append("enable\nexit\n")

    return "\n".join(cli_lines)


# class UpdateProgressWindow:
    # def __init__(self, parent):
        # self.cancelled = False

        # self.win = tk.Toplevel(parent)
        # self.win.title("Updating SonicWallTool")
        # self.win.geometry("460x240")
        # self.win.resizable(False, False)
        # self.win.grab_set()
        # self.win.protocol("WM_DELETE_WINDOW", self.cancel)

        # ttk.Label(self.win, text="Downloading update...").grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")

        # self.download_bar = ttk.Progressbar(self.win, length=420, mode="determinate")
        # self.download_bar.grid(row=1, column=0, padx=10)

        # self.stats_label = ttk.Label(self.win, text="0% | 0 MB/s | ETA --")
        # self.stats_label.grid(row=2, column=0, pady=(4, 12))

        # ttk.Label(self.win, text="Installing update...").grid(row=3, column=0, padx=10, sticky="w")

        # self.install_bar = ttk.Progressbar(self.win, length=420, mode="determinate")
        # self.install_bar.grid(row=4, column=0, padx=10, pady=(0, 10))

        # self.install_label = ttk.Label(self.win, text="Waiting...")
        # self.install_label.grid(row=5, column=0)

        # self.cancel_btn = ttk.Button(self.win, text="Cancel Update", command=self.cancel)
        # self.cancel_btn.grid(row=6, column=0, pady=10)

    # def cancel(self):
        # self.cancelled = True
        # self.install_label.config(text="Cancelling...")

    # def update_download(self, percent, speed, eta):
        # self.download_bar["value"] = percent
        # self.stats_label.config(
            # text=f"{percent}% | {speed:.2f} MB/s | ETA {eta}s"
        # )
        # self.win.update_idletasks()

    # def update_install(self, percent):
        # self.install_bar["value"] = percent
        # self.install_label.config(text=f"{percent}%")
        # self.win.update_idletasks()

    # def close(self):
        # self.win.destroy()



class SonicToolApp:
    def __init__(self, root):
        root.title(f"SonicWallTool")
        root.geometry("900x650")
        root.resizable(True, True)

        # Get the folder where the script or exe is located
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Build the path to your icon dynamically
        icon_path = os.path.join(base_path, "Sonic.ico")  # Icon must be in the same folder

        # root.iconbitmap(icon_path)
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        style = ttk.Style()
        style.theme_use("default")
        tabs = ttk.Notebook(root)
        self.tab1 = ttk.Frame(tabs)
        self.tab2 = ttk.Frame(tabs)
        self.tab3 = ttk.Frame(tabs)  # New tab for Service Objects
        self.tab4 = ttk.Frame(tabs)  # New tab for Service Objects
        self.tab5 = ttk.Frame(tabs) # New tab for Static DHCP Binding
        tabs.add(self.tab1, text="Local User Generator")
        tabs.add(self.tab2, text="Address Object Generator")
        tabs.add(self.tab3, text="Service Object Generator")
        tabs.add(self.tab4, text="User Group Generator")
        tabs.add(self.tab5, text="DHCP Static Generator")
        tabs.pack(expand=1, fill="both")
        self.build_user_tab(self.tab1)
        self.build_address_tab(self.tab2)
        self.build_service_tab(self.tab3)
        self.build_group_tab(self.tab4)
        self.build_dhcp_tab(self.tab5)

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

    def build_dhcp_tab(self, tab):
        self.dhcp_input, self.dhcp_output, self.dhcp_log, btn_frame = self.build_common_layout(tab, "Select Excel/CSV file for DHCP Static Reservations:")
        ttk.Button(btn_frame, text="Generate Script", command=self.run_dhcp_script).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Copy Logs", command=lambda: self.copy_logs(self.dhcp_log)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Export Logs", command=lambda: self.export_logs(self.dhcp_log)).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Clear Logs", command=lambda: self.clear_logs(self.dhcp_log)).grid(row=0, column=3, padx=5)    
        ttk.Button(btn_frame, text="Export Template", command=lambda: export_template(DHCP_TEMPLATE_COLUMNS, DHCP_TEMPLATE_DATA, "DHCP_Static_Template.xlsx")).grid(row=0, column=4, padx=5)
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(1, weight=1)

    def browse(self, entry, is_folder):
        if is_folder:
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls"),("CSV Files", "*.csv")])
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
            commands, logs = generate_full_script(df)

            # Write logs
            for msg in logs:
                self.log(self.user_log, msg)

            # Write output file
            with open(full_out, 'w', encoding="utf-8") as f:
                if commands:
                    f.write("user local\n")

                    for cmd in commands:
                        f.write(cmd + "\n")

#                    f.write("exit\n")

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
            with open(full_out, 'w', encoding="utf-8") as f:
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
            with open(full_out, 'w', encoding="utf-8") as f:
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
            with open(full_out, 'w', encoding="utf-8") as f:
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

    def run_dhcp_script(self):
        input_path = self.dhcp_input.get().strip()
        output_folder = self.dhcp_output.get().strip()

        if not os.path.isfile(input_path):
            messagebox.showerror("Error", "Please select a valid Excel or CSV file.")
            return

        if not os.path.isdir(output_folder):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return

        try:
            if input_path.lower().endswith((".xls", ".xlsx")):
                df = pd.read_excel(input_path)
            else:
                df = pd.read_csv(input_path)

            df.columns = [c.strip() for c in df.columns]

            ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fname = os.path.splitext(os.path.basename(input_path))[0]

            out_file = os.path.join(
                output_folder,
                f"{fname}_DHCP_Static_{ts_file}.txt"
            )

            self.log(self.dhcp_log, f"\nLogs for {fname} [{ts_log}]")
            self.log(self.dhcp_log, "-" * 70)

            log_lines = []
            script = generate_dhcp_cli_script(df, log_lines)

            with open(out_file, "w") as f:
                f.write(script)

            for line in log_lines:
                self.log(self.dhcp_log, line)

            messagebox.showinfo(
                "Success",
                f"DHCP script saved as:\n{out_file}"
            )

        except Exception as e:
            self.log(self.dhcp_log, f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))

# Confirmation before exit
def confirm_exit():
    if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
        root.quit()

# About Software
def show_about():
    messagebox.showinfo("About", f"SonicWallTool\n\nVersion: {VERSION}\n\nDeveloped for internal use only.")

# Calling
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

