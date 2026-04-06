# 📅 Anki Study Tracker

Một add-on Anki để track và chia sẻ progress học tập với bạn bè qua GitHub.

## 🚀 Quick Setup

### 1️⃣ Clone Repository
```bash
git clone https://github.com/Halibut205/anki-study-group-me-and-friend.git
cd anki-study-group-me-and-friend
```

### 2️⃣ Setup Config (First Time Only)
```bash
# Copy template config
cp config.example.json config.json

# Edit config.json with your info
nano config.json
```

Chỉnh sửa các fields:
- `"my_name": "Ban"` → Đổi thành tên của bạn
- `"my_color": "#378ADD"` → Chọn màu hex (ví dụ: `#FF6B6B`, `#4ECDC4`)
- `"repo_path": "/path/to/your/cloned/repo"` → Đường dẫn đến thư mục vừa clone

### 3️⃣ Trong Anki
- Mở Anki
- Vào **Tools → Study Tracker 📅**
- Nhấn **⚙️** để mở Settings
- Kiểm tra Profile tab (Name, Color, Repo Path)
- Nhấn **💾 Save** khi chắc chắn

### 4️⃣ Sync
- Mỗi khi nhấn **↻ Sync** trong Study Tracker, data của bạn tự động push lên GitHub
- Data của bạn bè sẽ được pull về để hiển thị trên calendar

---

## 📋 Configuration Details

| Field | Ý Nghĩa | Ví Dụ |
|-------|---------|-------|
| `my_name` | Tên hiển thị trên calendar | `"Ban"`, `"Linh"` |
| `my_color` | Màu avatar (hex code) | `"#378ADD"`, `"#FF6B6B"` |
| `repo_path` | Đường dẫn đến repo trên máy | `/home/user/anki-study-group` |
| `goals.daily` | Mục tiêu số cards mỗi ngày | `10` |
| `goals.weekly` | Mục tiêu số cards mỗi tuần | `50` |

---

## 🎨 Color Picker Tips

Sử dụng color picker online để chọn màu sắc yêu thích:
- [colorpicker.com](https://www.colorpicker.com)
- Copy hex code (ví dụ: `#FF6B6B`) vào config.json

Hoặc dùng UI: Settings → Profile → nhấn **🎨** để chọn màu

---

## 👥 Mời Bạn Tham Gia

1. Chia link GitHub repo cho bạn: `https://github.com/Halibut205/anki-study-group-me-and-friend.git`
2. Bạn clone về và follow các bước setup ở trên
3. Mỗi người có config.json riêng (không được commit lên GitHub)
4. Data tracking được share qua GitHub để mọi người xem tiến độ của nhau

---

## 📊 Hiểu Cách Hoạt Động

### Calendar Indicators
- **✓** (xanh) = Tất cả mọi người đã học
- **◐** (cam) = Hầu hết mọi người đã học (70%+)
- **◑** (vàng) = Khoảng nửa mọi người học (50%+)
- **✗** (đỏ) = Ít người học (<50%)
- **·** (xám) = Chưa có ai học

### Files Structure
```
├── __init__.py          # Entry point của addon
├── qt_ui.py            # UI chính (Calendar + Settings)
├── sync.py             # GitHub sync logic
├── tracker.py          # Extract data từ Anki revlog
├── config.example.json # Template (không push lên Git)
├── config.json         # Cá nhân (trong .gitignore)
└── .gitignore          # Exclude config.json
```

---

## 🐛 Troubleshooting

### Repo path không tìm được
- Kiểm tra đường dẫn có đúng không
- Thử dùng absolute path (ví dụ: `/home/user/anki-study-group`, không phải `~/anki-study-group`)

### Sync không hoạt động
- Kiểm tra git config: `git config user.name` và `git config user.email`
- Đảm bảo repo URL đúng

### Không thấy dữ liệu bạn bè
- Kiểm tra bạn bè đã nhấn Sync chưa
- Nhấn Sync lại để pull dữ liệu mới

---

## 📞 Support

Gặp lỗi? Kiểm tra Anki console hoặc tạo issue trên GitHub.

---

**Happy studying! 🎓**
