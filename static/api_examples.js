// Ví dụ gọi backend từ JavaScript trong trang HTML.
// Đăng nhập:
async function backendLogin(username, password) {
  const response = await fetch("/api/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Đăng nhập thất bại");
  return result.user;
}

// Chấm công đầu ca:
async function backendCheckIn() {
  const response = await fetch("/api/attendance", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({action: "check_in"})
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Không thể chấm công");
  return result;
}
