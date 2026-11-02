# VKSTAR Smart Attendance – Flask Backend

## 1. Kiến trúc
- `templates/index.html`: giao diện HTML/CSS/JavaScript gốc bạn gửi.
- `app.py`: backend Python Flask, xử lý đăng nhập, phân quyền, nhân viên, chấm công và đơn.
- `vkstar.db`: SQLite tự tạo khi chạy lần đầu.

Lưu ý: trình duyệt vẫn cần HTML/CSS/JavaScript để hiển thị giao diện và mở camera. Python đảm nhiệm backend, lưu dữ liệu và xử lý nghiệp vụ. File HTML gốc hiện đang dùng `localStorage` cho nhiều chức năng; backend trong bản này đã có API và database riêng, nhưng chưa tự động thay toàn bộ các lệnh `localStorage` trong giao diện thành gọi API. Vì vậy giao diện gốc vẫn có thể hoạt động theo chế độ demo cũ; muốn mọi thao tác trên giao diện lưu tập trung vào SQLite thì cần nối từng chức năng frontend với API tương ứng.

## 2. Cài đặt trên Windows
1. Cài Python 3.10 trở lên.
2. Giải nén thư mục này.
3. Mở thư mục `VKSTAR_Flask_Backend` bằng VS Code.
4. Mở Terminal trong VS Code và chạy:

```bash
py -m venv venv
venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

5. Mở trình duyệt tại: http://127.0.0.1:5000

Nếu PowerShell chặn activate, có thể dùng CMD terminal hoặc chạy trực tiếp:
`venv\Scripts\python.exe -m pip install -r requirements.txt`
và
`venv\Scripts\python.exe app.py`

## 3. Tài khoản demo backend
| Vai trò | Tài khoản | Mật khẩu |
|---|---|---|
| Nhân viên | nv01 | 123456 |
| Trưởng ca | tc01 | 123456 |
| Nhân sự | hr01 | 123456 |

Đây là tài khoản minh họa, cần đổi mật khẩu trước khi dùng thật.

## 4. API có sẵn
- `GET /api/health`: kiểm tra backend.
- `POST /api/login`: đăng nhập JSON `{ "username": "nv01", "password": "123456" }`.
- `POST /api/logout`: đăng xuất.
- `GET /api/me`: thông tin tài khoản đang đăng nhập.
- `GET /api/staff`: danh sách nhân viên (Trưởng ca/HR).
- `POST /api/staff`: tạo tài khoản (chỉ HR).
- `GET /api/attendance`: lịch sử chấm công theo quyền.
- `POST /api/attendance`: `{ "action": "check_in" }` hoặc `{ "action": "check_out" }` (nhân viên).
- `GET /api/requests`: danh sách đơn theo quyền.
- `POST /api/requests`: gửi đơn `{ "type": "Nghỉ phép", "date": "2026-11-02", "note": "..." }`.
- `PATCH /api/requests/1`: duyệt/từ chối `{ "status": "Đã duyệt" }`.

## 5. Test nhanh API
Có thể mở `http://127.0.0.1:5000/api/health` để xem backend sống chưa.
Dùng Postman để thử `POST /api/login`, sau đó gọi các API cần đăng nhập với cookie session được giữ lại.

## 6. Những phần cần hoàn thiện trước khi triển khai thật
- Nối form đăng nhập, nút chấm công, danh sách nhân viên, đơn từ trong HTML sang API.
- Xác thực khuôn mặt cần kiểm tra phía server hoặc có quy trình xác thực an toàn; việc nhận diện trên trình duyệt hiện tại không thay thế bảo mật backend.
- Ảnh khuôn mặt/bằng chứng cần lưu file an toàn hoặc object storage, không nhét trực tiếp vào database nếu dữ liệu lớn.
- Bổ sung CSRF protection, HTTPS, giới hạn đăng nhập sai, đổi secret key, phân quyền chi tiết và sao lưu database.
- Quy tắc đi muộn hiện đặt mốc demo 08:00 trong `app.py`; chỉnh lại theo ca thực tế của doanh nghiệp.
