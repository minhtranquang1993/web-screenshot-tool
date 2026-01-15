# 📸 Web Screenshot Tool

Tool Python để chụp ảnh màn hình các trang web và lưu thành file JPG.

## ✨ Tính năng

- 🌐 Chụp ảnh toàn bộ trang web (full page screenshot)
- 📝 Hỗ trợ nhập nhiều URL cùng lúc
- 📁 Cho phép chọn thư mục lưu ảnh
- 📊 Hiển thị tiến trình và kết quả chi tiết
- 🖼️ Lưu ảnh định dạng JPG chất lượng cao (90%)

## 🚀 Cài đặt

### 1. Tạo môi trường ảo (khuyến nghị)

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 3. Cài đặt browser cho Playwright

```bash
playwright install chromium
```

## 📖 Sử dụng

### Chạy tool

```bash
python screenshot_tool.py
```

### Hướng dẫn sử dụng

1. **Nhập URLs**: Nhập các URL cần chụp vào ô text, mỗi URL một dòng
   - Có thể bỏ qua `https://`, tool sẽ tự thêm
   - Dòng bắt đầu bằng `#` sẽ được bỏ qua (comment)

2. **Chọn thư mục**: Click "Chọn..." để chọn thư mục lưu ảnh

3. **Chụp ảnh**: Click "📸 Chụp Ảnh" để bắt đầu

4. **Xem kết quả**: Theo dõi tiến trình và kết quả trong phần log

## 📋 Ví dụ

```
https://google.com
https://github.com
facebook.com
# Dòng này sẽ bị bỏ qua
https://stackoverflow.com
```

## ⚠️ Lưu ý

- Tool sử dụng Chromium ở chế độ headless
- Viewport mặc định: 1920x1080
- Timeout cho mỗi trang: 60 giây
- Ảnh được lưu với chất lượng JPEG 90%

## 🔧 Yêu cầu hệ thống

- Python 3.9+
- Windows/macOS/Linux
- Kết nối Internet
