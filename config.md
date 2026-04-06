# Study Tracker – Configuration

| Key | Mô tả | Ví dụ |
|-----|-------|-------|
| `my_name` | Tên hiển thị của bạn trên calendar | `"Ban"` |
| `my_color` | Màu avatar của bạn (hex) | `"#378ADD"` |
| `repo_path` | Đường dẫn tuyệt đối đến thư mục GitHub repo đã clone | `"/Users/ban/anki-study-group"` |

## Setup nhanh

1. Một người tạo repo trên GitHub (public hoặc private).
2. Mỗi người `git clone <repo-url>` về máy.
3. Điền `repo_path` vào config (đường dẫn đến thư mục vừa clone).
4. Điền `my_name` và `my_color` khác nhau cho mỗi người.
5. Mở **Tools → Study Tracker** để xem calendar.

Sau mỗi lần nhấn **Sync** trong Anki, plugin tự động push dữ liệu của bạn lên GitHub.
