import sys
import os
import time
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

UPDATE_LOG_FILE = "update.log"
APP_NAME = "SonicWallTool.exe"
BACKUP_NAME = "SonicWallTool_Old.exe"
latest_version = sys.argv[1]
UPDATE_BASE_URL = "http://192.168.7.16/SonicWallTool/"

def log_update(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(UPDATE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


class UpdateProgressWindow:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Updating SonicWallTool")
        self.win.geometry("460x200")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)

        ttk.Label(
            self.win,
            text="Updating SonicWallTool...",
            font=("Segoe UI", 10)
        ).pack(pady=(15, 8))

        self.progress_bar = ttk.Progressbar(
            self.win,
            length=420,
            mode="determinate",
            maximum=100
        )
        self.progress_bar.pack(pady=5)

        self.status_label = ttk.Label(
            self.win,
            text="Preparing update..."
        )
        self.status_label.pack(pady=10)

        self.win.update_idletasks()
        self.win.update()

    def update_progress(self, percent, status):
        self.progress_bar["value"] = percent
        self.status_label.config(text=status)
        self.win.update_idletasks()

    def close(self):
        try:
            self.win.destroy()
        except:
            pass


def download_file_with_retry(url, destination, progress, retries=3):
    for attempt in range(1, retries + 1):
        try:
            log_update(f"Download attempt {attempt}: {url}")

            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = int((downloaded / total_size) * 50)
                            progress.update_progress(
                                10 + percent,
                                f"Downloading... {10 + percent}%"
                            )

            log_update("Download completed successfully")
            return True

        except Exception as e:
            log_update(f"Download attempt {attempt} failed: {e}")

            if attempt < retries:
                time.sleep(2)
            else:
                raise Exception("Download failed after multiple attempts")


def rollback(backup_exe, local_exe):
    try:
        if os.path.exists(backup_exe):
            if os.path.exists(local_exe):
                try:
                    os.remove(local_exe)
                except:
                    pass

            os.replace(backup_exe, local_exe)
            log_update("Rollback completed successfully")

    except Exception as e:
        log_update(f"Rollback failed: {e}")


def main():
    if len(sys.argv) < 3:
        log_update("ERROR: Missing arguments")
        sys.exit(1)

    latest_version = sys.argv[1]
    base_url = sys.argv[2]

    version_no_dots = latest_version.replace(".", "")
    download_url = base_url + f"SonicWallTool_v{version_no_dots}.exe"

    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    local_exe = os.path.join(current_dir, APP_NAME)
    temp_exe = local_exe + ".new"
    backup_exe = os.path.join(current_dir, BACKUP_NAME)

    time.sleep(2)

    progress = None

    try:
        progress = UpdateProgressWindow()

        log_update("=" * 60)
        log_update(f"Starting update to version {latest_version}")
        log_update(f"Download URL: {download_url}")

        progress.update_progress(5, "Preparing update...")

        if os.path.exists(temp_exe):
            os.remove(temp_exe)
            log_update("Removed old temp file")

        download_file_with_retry(download_url, temp_exe, progress)

        progress.update_progress(70, "Creating backup...")

        if os.path.exists(local_exe):
            if os.path.exists(backup_exe):
                os.remove(backup_exe)

            for _ in range(5):
                try:
                    os.replace(local_exe, backup_exe)
                    break
                except PermissionError:
                    time.sleep(1)
            else:
                raise Exception("Application is still running. Please close it and retry.")
            log_update("Current version backed up successfully")

        progress.update_progress(85, "Installing update...")

        os.replace(temp_exe, local_exe)

        progress.update_progress(95, "Finalizing update...")

        time.sleep(1)

        log_update(f"Update completed successfully to {latest_version}")

        progress.update_progress(100, "Launching application...")

        time.sleep(2)

        os.startfile(local_exe)
        log_update("Updated application launched successfully")
        sys.exit(0)

    except Exception as e:
        log_update(f"ERROR: Update failed - {e}")

        rollback(backup_exe, local_exe)

        messagebox.showerror(
            "Update Failed",
            f"Update could not be completed.\n\n{str(e)}"
        )

        sys.exit(1)

    finally:
        if os.path.exists(temp_exe):
            try:
                os.remove(temp_exe)
            except:
                pass
        if progress:
            progress.close()


if __name__ == "__main__":
    main()