# 📅 Anki Study Tracker

Một add-on Anki để **theo dõi tiến độ học tập** và **chia sẻ với bạn bè qua GitHub**. Giúp bạn và nhóm bạn cùng nhau học tập và theo dõi tiến độ của nhau một cách công khai.

---

## 🎯 Mục Đích Của Addon

Addon này giải quyết 3 vấn đề chính:

1. **Tracking Cá Nhân** - Tự động ghi lại số card bạn học mỗi ngày từ Anki
2. **Chia Sẻ Nhóm** - Chia sẻ tiến độ với bạn bè qua GitHub (mọi người có thể thấy)
3. **Động Lực Học Tập** - Xem tiến độ của nhau, tạo áp lực tích cực (accountability)

**Ví dụ:**
- Ban học 15 cards hôm nay ✓
- Khánh học 8 cards hôm nay ✗
- Minh chưa học ·
- Calendar sẽ hiển thị: **◐** (một số hoàn thành mục tiêu)

---

## 🚀 Hướng Dẫn Cài Đặt

### 1️⃣ Clone Repository

```bash
git clone https://github.com/Halibut205/anki-study-group-me-and-friend.git
cd anki-study-group-me-and-friend
```

### 2️⃣ Setup Lần Đầu Tiên

1. Mở Anki
2. Vào **Tools → Study Tracker**
3. **Setup Wizard** sẽ hiển thị
4. Nhập **tên** của bạn (ví dụ: "Hali", "Ban", "Khánh")
5. Chọn **màu avatar** bằng color picker
6. Nhấn **Save & Continue**
7. ✅ Calendar sẽ hiển thị tiến độ

### 3️⃣ Sync Dữ Liệu

Mỗi lần nhấn **Sync**, addon sẽ:
- 📤 Push dữ liệu học tập của bạn lên GitHub
- 📥 Pull dữ liệu của bạn bè về máy
- 📊 Cập nhật calendar với dữ liệu mới nhất

**Lưu ý:** Auto-sync xảy ra sau mỗi lần bạn sync Anki (nếu config đã setup)

---

## 📁 Cấu Trúc Thư Mục & Files

```
addon-root/
├── __init__.py              # Entry point - kết nối Anki menu
├── qt_ui.py                 # Giao diện chính (Calendar + Settings)
├── sync.py                  # GitHub sync logic
├── tracker.py               # Trích xuất dữ liệu từ Anki database
├── config.json              # ⭐ Config cá nhân (gitignored)
├── goals.json               # ⭐ Mục tiêu chung (shared trên Git)
├── config.example.json      # Template config (reference)
├── README.md                # File này
└── User/
    └── {username}/
        ├── {username}.json  # ⭐ Dữ liệu học tập (pushed to Git)
        └── ...
```

### ⭐ Giải Thích 3 Loại File Quan Trọng

| File | Vị Trí | Gitignore? | Ý Nghĩa |
|------|--------|-----------|---------|
| `config.json` | Root | ✅ Yes | Cá nhân: tên, màu (mỗi máy khác nhau) |
| `goals.json` | Root | ❌ No | Chung: mục tiêu daily/weekly (shared) |
| `User/{username}.json` | User/ folder | ❌ No | Dữ liệu học tập (pushed to GitHub) |

---

## ⚙️ Chi Tiết Cấu Hình

### `config.json` (Local, Gitignored)

```json
{
  "my_name": "Hali",
  "my_color": "#378ADD"
}
```

- `my_name`: Tên hiển thị trên calendar (mỗi máy có thể khác)
- `my_color`: Màu hex code của avatar (format: `#RRGGBB`)

**Chú ý:** File này không được push lên Git (trong `.gitignore`), mỗi máy có config riêng

### `goals.json` (Shared, On Git)

```json
{
  "daily": 10,
  "weekly": 50
}
```

- `daily`: Mục tiêu số cards/ngày
- `weekly`: Mục tiêu số cards/tuần

**Chú ý:** Tất cả thành viên nhóm dùng chung file này. Thay đổi tại máy bất kỳ sẽ ảnh hưởng toàn nhóm.

### `User/{username}/{username}.json` (Shared, On Git)

```json
{
  "name": "Hali",
  "color": "#378ADD",
  "reviews": {
    "2026-04-06": 12,
    "2026-04-05": 8,
    "2026-04-04": 15
  },
  "last_updated": "2026-04-06T15:30:45"
}
```

- `name`: Tên của người dùng
- `color`: Màu avatar
- `reviews`: Dict `{ngày: số_cards}` cho 90 ngày qua
- `last_updated`: Thời điểm sync cuối cùng

**Chú ý:** File này được push lên Git và giúp bạn bè xem tiến độ của bạn

---

## 🎨 Hiểu Calendar & Status Icons

### Calendar Status Icons

Mỗi ngày trên calendar có biểu tượng thể hiện trạng thái hoàn thành mục tiêu:

| Icon | Màu | Ý Nghĩa |
|------|-----|---------|
| **✓** | 🟢 Xanh | **Tất cả** mọi người hoàn thành daily goal |
| **◐** | 🟠 Cam | **Một số** người hoàn thành daily goal |
| **✗** | 🔴 Đỏ | **Không ai** hoàn thành daily goal |
| **·** | ⚫ Xám | **Chưa có** dữ liệu (ai cũng chưa học) |

### Ví Dụ Cụ Thể

Daily goal = 10 cards, có 3 bạn: Hali, Ban, Khánh

**Ngày 6/4:**
- Hali: 12 cards → ✓ (≥10)
- Ban: 5 cards → ✗ (<10)
- Khánh: 8 cards → ✗ (<10)
- **Kết quả: ◐** (1/3 hoàn thành)

**Ngày 5/4:**
- Hali: 10 cards → ✓
- Ban: 15 cards → ✓
- Khánh: 12 cards → ✓
- **Kết quả: ✓** (3/3 hoàn thành)

---

## 🔄 Luồng Dữ Liệu (Data Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ANKI DATABASE                               │
│                      (revlog table)                              │
│           Ghi lại mọi card bạn học (timestamp, id)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ╔════════════════════════════════════════╗
        ║         tracker.py                     ║
        ║  get_my_reviews() - Query revlog       ║
        ║  → {2026-04-06: 12, 2026-04-05: 8}    ║
        ╚════════════════════════════════════════╝
                         │
                         ▼
        ╔════════════════════════════════════════╗
        ║         sync.py                        ║
        ║  1. git pull --rebase                  ║
        ║  2. Write User/{username}.json         ║
        ║  3. git add + commit + push            ║
        ╚════════════════════════════════════════╝
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              GITHUB REPOSITORY                           │
│  User/                                                   │
│  ├── hali/                                               │
│  │   └── hali.json (Hali's data)                        │
│  ├── ban/                                                │
│  │   └── ban.json (Ban's data)                          │
│  ├── khanh/                                             │
│  │   └── khanh.json (Khánh's data)                      │
│  └── goals.json (Shared goals)                          │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
        ╔════════════════════════════════════════╗
        ║         sync.py                        ║
        ║  pull_all_data()                       ║
        ║  → Read all *.json from User/          ║
        ║  → Return list of friend data          ║
        ╚════════════════════════════════════════╝
                         │
                         ▼
        ╔════════════════════════════════════════╗
        ║         qt_ui.py                       ║
        ║  1. Load all friend data               ║
        ║  2. Calculate status icons (✓/◐/✗)   ║
        ║  3. Render calendar grid               ║
        ║  4. Show avatars + progress bars       ║
        ╚════════════════════════════════════════╝
                         │
                         ▼
         ┌──────────────────────────────────┐
         │   CALENDAR UI (MainWindow)       │
         │   - Calendar grid (7x6)          │
         │   - Detail panel (day info)      │
         │   - Friends list + their scores  │
         └──────────────────────────────────┘
```

---

## 🎯 Các Thành Phần Chính

### 1️⃣ **tracker.py** - Trích Xuất Dữ Liệu

```python
get_my_reviews() → dict
```

- Query Anki database (bảng `revlog`)
- Lấy số card học trong **90 ngày qua**
- Format: `{"2026-04-06": 12, "2026-04-05": 8}`

**Cách hoạt động:**
- Tính thời gian 90 ngày trước = cutoff time
- Query: `SELECT COUNT(*) FROM revlog WHERE id > cutoff`
- Nhóm theo ngày (day_bucket = id / 86400000)
- Convert timestamp → "YYYY-MM-DD"

### 2️⃣ **sync.py** - GitHub Sync

#### `push_my_data()`
1. Load config từ `config.json` (root)
2. Get dữ liệu từ `tracker.get_my_reviews()`
3. Tạo file `User/{username}/{username}.json`
4. `git pull --rebase` (update từ bạn bè)
5. `git add + commit + push` (đẩy data lên)

#### `pull_all_data()`
1. `git pull --rebase` (lấy dữ liệu mới)
2. Đọc tất cả `*.json` từ `User/` folders
3. Return list: `[{name: "Hali", reviews: {...}}, ...]`

### 3️⃣ **qt_ui.py** - Giao Diện

#### **SetupWizard**
- Dialog đầu tiên nếu chưa config
- Nhập tên + chọn màu
- Lưu vào `config.json`

#### **GoalManager**
- Load `goals.json` (shared)
- Calculate status: `✓` / `◐` / `✗` / `·`
- Logic: đếm số người hoàn thành goal

#### **CalendarPanel**
- Grid 7×6 (7 cột = thứ trong tuần, 6 dòng = tuần)
- Mỗi ô là `DayCell`
- Click ngày → detail panel update

#### **DayCell**
- Hiển thị: ngày, status icon, avatars bạn bè
- Progress bar (%)

#### **DetailPanel**
- Thống kê: số người học / tổng
- Danh sách chi tiết từng bạn
- Số card + trạng thái (Done/Miss)

#### **MainWindow**
- Kết hợp Calendar + Detail
- Top bar: title, goals, sync button
- Status bar: trạng thái sync

#### **Settings Dialog**
- Tab 1: Profile (tên, màu)
- Tab 2: Friends (xem danh sách)
- Tab 3: Data Management (xóa revlog)

---

## 👥 Mời Bạn Tham Gia Nhóm

### Với Bạn Lần Đầu

1. Nhận link repo từ bạn: `https://github.com/Halibut205/anki-study-group-me-and-friend.git`
2. Clone về: `git clone <link>`
3. Mở Anki, vào **Tools → Study Tracker**
4. Setup wizard: nhập tên + chọn màu
5. Nhấn **Sync** → dữ liệu bạn sẽ được push lên GitHub
6. Thêm `.gitignore` nếu chưa có (exclude `config.json`)

### Với Bạn Bè Bạn Đã Setup

Mỗi người có:
- **`config.json` riêng** (không nhìn thấy) ← local cá nhân
- **`User/{username}.json` shared** (mọi người nhìn thấy) ← trên GitHub
- **`goals.json` chung** (shared) ← cùng mục tiêu

---

## 🔧 Thiết Lập & Cấu Hình Chi Tiết

### Tìm Màu Avatar

1. Vào [colorpicker.com](https://www.colorpicker.com)
2. Chọn màu yêu thích
3. Copy hex code (ví dụ: `#FF6B6B`)
4. Paste vào **Settings → Profile → 🎨 Color**

### Thay Đổi Goals (Mục Tiêu)

**Cách 1: Sửa file**
- Mở `goals.json`
- Sửa `daily` và `weekly`
- Commit + Push (tất cả bạn bè sẽ thấy)

**Cách 2: UI Settings**
- Settings → Data → có thể sẽ thêm chỉnh sửa goals

### Xem Dữ Liệu Bạn Bè

- Mở folder `User/`
- Xem file `{username}.json` của bạn bè
- Hoặc click ngày trên calendar để xem chi tiết

---

## 🐛 Troubleshooting

### Sync Không Hoạt Động

**Lỗi: "git not found"**
- Cài Git: `sudo apt install git` (Linux) hoặc [git-scm.com](https://git-scm.com)
- Kiểm tra: `git --version`

**Lỗi: "git commit failed"**
- Kiểm tra git config:
  ```bash
  git config user.name
  git config user.email
  ```
- Nếu chưa setup:
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your@email.com"
  ```

**Lỗi: "git push failed"**
- Repo offline → sync sẽ fail an toàn (không mất dữ liệu)
- Kiểm tra internet + SSH key (nếu dùng SSH)
- Retry sau khi internet OK

### Không Thấy Dữ Liệu Bạn Bè

- Bạn bè đã setup config chưa?
- Bạn bè đã nhấn Sync chưa?
- Thử nhấn Sync lại: `[Sync]` button

### Không Thấy Mục Tiêu Ngày Hôm Nay

- Bạn đã sync Anki (cardboard icon)?
  - Auto-sync sẽ kích hoạt sau khi sync Anki
- Hoặc nhấn `[Sync]` trong Study Tracker

### Calendar Trống Trơn

- Bạn chưa học card nào trong 90 ngày?
  - Học vài card, sync lại
- File `hali.json` tồn tại trong `User/hali/`?
  - Kiểm tra: `User/hali/hali.json` có dữ liệu?

### Config Lost Sau Khi Restart

- `config.json` có tồn tại?
  - Nếu không: Setup wizard sẽ hiện, setup lại
- File có bị gitignore? → Đúng rồi, nên bị ignore

---

## 📊 Ví Dụ Thực Tế

### Scenario: 3 Bạn Học Cùng Nhóm

**Repo GitHub có cấu trúc:**
```
User/
├── hali/
│   └── hali.json
├── ban/
│   └── ban.json
├── khanh/
│   └── khanh.json
goals.json
```

**Mỗi ngày sáng:**
1. Mở Anki → học vài card
2. Sync Anki (cardboard icon)
   - Auto-sync kích hoạt
   - Dữ liệu push lên GitHub
3. Mở Study Tracker
   - Xem calendar
   - Thấy bạn bè học bao nhiêu
   - **Động lực: "Hôm nay tớ phải học nhiều hơn"**

**Cuối tuần:**
- Xem biểu đồ tuần
- Nhìn ai học nhiều nhất / ít nhất
- Adjust goals nếu cần

---

## 🔐 Privacy & Security

### Dữ Liệu Nào Bị Chia Sẻ?

**Được chia sẻ (public trên GitHub):**
- ✅ Tên bạn
- ✅ Màu avatar
- ✅ Số card học mỗi ngày (90 ngày qua)
- ✅ Thời gian last sync

**Không được chia sẻ (local gitignored):**
- ❌ `config.json` (mỗi máy khác nhau)
- ❌ Nội dung card, câu hỏi, đáp án
- ❌ Các thông tin khác trong Anki database

### Xóa Dữ Liệu

Muốn xóa dữ liệu công khai?
1. Settings → Data Management → "Clear All Study Data"
2. Hoặc xóa file `User/{username}/{username}.json` rồi commit

---

## 💡 Tips & Tricks

### Tối Ưu Hiệu Suất

- Setup goals hợp lý (không quá cao)
- Sync thường xuyên (hàng ngày)
- Backup repo: `git push` định kỳ

### Extend Addon

Có thể sửa:
- Thay đổi colors, icons
- Thêm weekly/monthly view
- Thêm achievements badges
- Tích hợp với Trello, Notion, v.v.

---

## 📞 Support & Contact

Gặp vấn đề?
1. Kiểm tra **Anki console** (View → Toggle Dev Tools)
2. Xem error message
3. Tạo **issue trên GitHub**
4. Hoặc liên hệ trực tiếp

---

## 📚 File Reference

| File | Dòng | Chức Năng |
|------|------|----------|
| `__init__.py` | Toàn bộ | Entry point, menu hook, auto-sync |
| `tracker.py` | `get_my_reviews()` | Query Anki revlog |
| `sync.py` | `push_my_data()` | Push data to GitHub |
| `sync.py` | `pull_all_data()` | Pull friends' data |
| `qt_ui.py` | `MainWindow` | Calendar UI |
| `qt_ui.py` | `GoalManager` | Status calculation |
| `qt_ui.py` | `DayCell` | Individual day cell |
| `qt_ui.py` | `CalendarPanel` | Calendar grid |
| `qt_ui.py` | `DetailPanel` | Day detail view |

---

**Happy studying with your friends! 📚✨**
