"""
Web Screenshot Tool
Tool để chụp ảnh màn hình các trang web và lưu thành file JPG.
"""

import os
import sys
import re
from datetime import datetime
from urllib.parse import urlparse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import threading
from playwright.sync_api import sync_playwright
from google_drive_manager import GoogleDriveManager


def sanitize_filename(url: str) -> str:
    """Tạo tên file an toàn từ URL."""
    parsed = urlparse(url)
    # Lấy domain và path
    name = parsed.netloc + parsed.path
    # Thay thế các ký tự không hợp lệ
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Giới hạn độ dài
    name = name[:100] if len(name) > 100 else name
    # Thêm timestamp để tránh trùng lặp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}.jpg"


def capture_screenshot(url: str, output_folder: str, progress_callback=None) -> tuple[bool, str]:
    """
    Chụp ảnh màn hình của một URL.
    
    Args:
        url: URL cần chụp
        output_folder: Thư mục lưu ảnh
        progress_callback: Hàm callback để cập nhật tiến trình
        
    Returns:
        Tuple (success, message)
    """
    try:
        # Đảm bảo URL có protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        if progress_callback:
            progress_callback(f"Đang mở trình duyệt cho: {url}")
            
        with sync_playwright() as p:
            # Khởi động browser (headless mode)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1
            )
            page = context.new_page()
            
            if progress_callback:
                progress_callback(f"Đang tải trang: {url}")
            
            # Truy cập URL với timeout 60 giây
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Đợi thêm một chút để đảm bảo trang load hoàn toàn
            page.wait_for_timeout(2000)
            
            # Tạo tên file
            filename = sanitize_filename(url)
            filepath = os.path.join(output_folder, filename)
            
            if progress_callback:
                progress_callback(f"Đang chụp ảnh: {url}")
            
            # Chụp ảnh toàn trang
            page.screenshot(path=filepath, full_page=True, type='jpeg', quality=90)
            
            browser.close()
            
            return True, f"✓ Đã lưu: {filepath}"
            
    except Exception as e:
        return False, f"✗ Lỗi với {url}: {str(e)}"


class ScreenshotToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Screenshot Tool")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Thiết lập style
        style = ttk.Style()
        style.configure('TButton', padding=6)
        style.configure('TLabel', padding=2)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === URL Input Section ===
        url_label = ttk.Label(main_frame, text="📝 Nhập các URL (mỗi URL một dòng):", font=('Segoe UI', 10, 'bold'))
        url_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Text area for URLs
        self.url_text = scrolledtext.ScrolledText(main_frame, height=12, font=('Consolas', 10))
        self.url_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.url_text.insert(tk.END, "# Nhập URL ở đây, ví dụ:\n# https://google.com\n# https://github.com\n")
        
        # === Output Folder Section ===
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        folder_label = ttk.Label(folder_frame, text="📁 Thư mục lưu:", font=('Segoe UI', 10, 'bold'))
        folder_label.pack(side=tk.LEFT)
        
        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Desktop/Screenshots"))
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(folder_frame, text="Chọn...", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT)
        
        # === Google Drive Section ===
        drive_frame = ttk.LabelFrame(main_frame, text="☁️ Google Drive Support", padding="10")
        drive_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.use_drive_var = tk.BooleanVar(value=False)
        self.drive_check = ttk.Checkbutton(drive_frame, text="Upload lên Google Drive", variable=self.use_drive_var, command=self.toggle_drive_ui)
        self.drive_check.pack(side=tk.LEFT, padx=(0, 10))
        
        self.connect_btn = ttk.Button(drive_frame, text="🔗 Kết nối Drive", command=self.connect_drive)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(drive_frame, text="Chọn Folder:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.drive_folder_var = tk.StringVar()
        self.drive_folder_cb = ttk.Combobox(drive_frame, textvariable=self.drive_folder_var, width=30, state="readonly")
        self.drive_folder_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # State
        self.drive_manager = GoogleDriveManager()
        self.drive_folders_map = {} # name -> id
        self.toggle_drive_ui()

        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.capture_btn = ttk.Button(btn_frame, text="📸 Chụp Ảnh", command=self.start_capture)
        self.capture_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(btn_frame, text="🗑️ Xóa URLs", command=self.clear_urls)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        open_folder_btn = ttk.Button(btn_frame, text="📂 Mở Thư Mục", command=self.open_output_folder)
        open_folder_btn.pack(side=tk.LEFT)
        
        # === Progress Section ===
        progress_label = ttk.Label(main_frame, text="📊 Tiến trình:", font=('Segoe UI', 10, 'bold'))
        progress_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar(value="Sẵn sàng")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=('Segoe UI', 9))
        status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # === Log Section ===
        log_label = ttk.Label(main_frame, text="📋 Kết quả:", font=('Segoe UI', 10, 'bold'))
        log_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=8, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def toggle_drive_ui(self):
        """Enable/Disable Drive UI based on checkbox."""
        state = tk.NORMAL if self.use_drive_var.get() else tk.DISABLED
        self.connect_btn.config(state=state)
        self.drive_folder_cb.config(state="readonly" if self.use_drive_var.get() else tk.DISABLED)
        
    def connect_drive(self):
        """Connects to Drive and lists folders."""
        self.update_status("Đang kết nối Google Drive...")
        self.connect_btn.config(state=tk.DISABLED)
        
        def run_auth():
            try:
                success = self.drive_manager.authenticate()
                if success:
                    folders = self.drive_manager.list_folders()
                    self.root.after(0, lambda: self.on_auth_success(folders))
                else:
                     self.root.after(0, lambda: messagebox.showerror("Lỗi", "Kết nối thất bại!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Lỗi kết nối: {e}"))
            finally:
                self.root.after(0, lambda: self.connect_btn.config(state=tk.NORMAL))
                
        threading.Thread(target=run_auth, daemon=True).start()
        
    def on_auth_success(self, folders):
        """Callback when auth is successful."""
        self.update_status("Kết nối Google Drive thành công!")
        self.drive_folders_map = {f['name']: f['id'] for f in folders}
        names = list(self.drive_folders_map.keys())
        self.drive_folder_cb['values'] = names
        if names:
            self.drive_folder_cb.current(0)
        messagebox.showinfo("Thành công", "Đã kết nối Google Drive!")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu ảnh")
        if folder:
            self.folder_var.set(folder)
            
    def clear_urls(self):
        self.url_text.delete(1.0, tk.END)
        
    def open_output_folder(self):
        folder = self.folder_var.get()
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showwarning("Cảnh báo", f"Thư mục không tồn tại: {folder}")
            
    def log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_status(self, message: str):
        self.status_var.set(message)
        self.root.update()
        
    def get_urls(self) -> list[str]:
        """Lấy danh sách URL từ text area."""
        text = self.url_text.get(1.0, tk.END)
        urls = []
        for line in text.split('\n'):
            line = line.strip()
            # Bỏ qua dòng trống và comment
            if line and not line.startswith('#'):
                urls.append(line)
        return urls
        
    def start_capture(self):
        urls = self.get_urls()
        if not urls:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một URL!")
            return
            
        output_folder = self.folder_var.get()
        
        # Check Drive requirements if enabled
        upload_to_drive = self.use_drive_var.get()
        drive_folder_id = None
        
        if upload_to_drive:
            folder_name = self.drive_folder_var.get()
            if not folder_name or folder_name not in self.drive_folders_map:
                messagebox.showwarning("Lỗi Drive", "Vui lòng kết nối và chọn folder trên Drive trước!")
                return
            drive_folder_id = self.drive_folders_map[folder_name]
        
        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo thư mục: {str(e)}")
                return
        
        # Reset progress
        self.log_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(urls)
        
        # Disable button during capture
        self.capture_btn.config(state=tk.DISABLED)
        
        self.log(f"🚀 Bắt đầu chụp {len(urls)} trang web...")
        self.log(f"📁 Lưu vào: {output_folder}")
        if upload_to_drive:
            self.log(f"☁️ Upload lên Drive folder: {self.drive_folder_var.get()}")
        self.log("")
        
        success_count = 0
        fail_count = 0
        
        for i, url in enumerate(urls, 1):
            self.update_status(f"Đang xử lý {i}/{len(urls)}: {url}")
            
            success, message = capture_screenshot(url, output_folder, self.update_status)
            self.log(message)
            
            if success:
                success_count += 1
                # Handle Upload
                if upload_to_drive:
                    # Extract filepath from message "✓ Đã lưu: filepath"
                    local_path = message.replace("✓ Đã lưu: ", "").strip()
                    if os.path.exists(local_path):
                         self.update_status(f"Đang upload lên Drive: {os.path.basename(local_path)}")
                         self.log(f"   ⬆️ Đang upload...")
                         file_id = self.drive_manager.upload_file(local_path, drive_folder_id)
                         if file_id:
                             self.log(f"   ✅ Upload thành công (ID: {file_id})")
                         else:
                             self.log(f"   ❌ Upload thất bại")
            else:
                fail_count += 1
                
            self.progress_bar['value'] = i
            self.root.update()
        
        # Summary
        self.log(f"\n{'='*50}")
        self.log(f"✅ Hoàn thành! Thành công: {success_count}, Thất bại: {fail_count}")
        self.update_status(f"Hoàn thành! {success_count} thành công, {fail_count} thất bại")
        
        # Re-enable button
        self.capture_btn.config(state=tk.NORMAL)
        
        # Show completion message
        if fail_count == 0:
            messagebox.showinfo("Thành công", f"Đã chụp xong {success_count} trang web!")
        else:
            messagebox.showwarning("Hoàn thành", f"Thành công: {success_count}\nThất bại: {fail_count}\n\nXem chi tiết trong log.")


def main():
    root = tk.Tk()
    app = ScreenshotToolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
