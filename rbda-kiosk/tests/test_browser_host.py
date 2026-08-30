"""Tests for browser_host — chế độ chạy dự phòng bằng trình duyệt, dùng
khi pywebview/pythonnet không khởi động được trên máy người dùng.

Điều quan trọng nhất phải bảo đảm: cầu nối HTTP này gọi ĐÚNG vào
PipelineAPI thật (không phải bản giả), và KHÔNG mở toang thứ gì ra ngoài
— chỉ nghe trên 127.0.0.1, bắt buộc có token, và không cho gọi phương
thức nội bộ (bắt đầu bằng dấu gạch dưới).
"""

import json
import os
import time
import urllib.error
import urllib.request

import pytest

import browser_host

RESOURCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def hosted(api):
    """Khởi động browser_host trước một PipelineAPI thật (không mở trình
    duyệt), trả về (url_goc, token)."""
    url = browser_host.serve(api, RESOURCE_DIR, "index.html", open_browser=False)
    base, token = url.split("/index.html?t=")
    return base, token


def _post(base, token, method, args=None, extra_headers=None):
    req = urllib.request.Request(
        f"{base}/__api__/{method}",
        data=json.dumps({"args": args or []}).encode(),
        headers={"Content-Type": "application/json",
                 **({"X-Kiosk-Token": token} if token else {}),
                 **(extra_headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def test_api_call_reaches_the_real_pipeline_api(hosted, api):
    base, token = hosted
    api.create_or_update_club("A", "Club A", 5, 0, "")
    api.create_student_if_missing("s1", "Student 1")
    api.submit_preferences("s1", ["A"])

    res = _post(base, token, "get_dashboard_status")
    assert res["ok"] is True
    # đúng dữ liệu vừa tạo qua đối tượng Python, đọc lại qua HTTP
    assert res["data"]["n_students"] == 1
    assert res["data"]["n_clubs"] == 1


def test_api_call_passes_arguments_through(hosted, api):
    base, token = hosted
    res = _post(base, token, "create_student_if_missing", ["s9", "Nguyen Van A"])
    assert res["ok"] is True
    # thật sự đã ghi vào DB, không phải trả lời cho có
    assert api.get_dashboard_status()["data"]["n_students"] == 1


def test_request_without_token_is_rejected(hosted):
    base, _ = hosted
    with pytest.raises(urllib.error.HTTPError) as exc:
        _post(base, None, "get_dashboard_status")
    assert exc.value.code == 403


def test_request_with_wrong_token_is_rejected(hosted):
    base, _ = hosted
    with pytest.raises(urllib.error.HTTPError) as exc:
        _post(base, "sai-token-hoan-toan", "get_dashboard_status")
    assert exc.value.code == 403


def test_private_methods_are_not_exposed(hosted):
    """_backup_db, _move_corrupt_db_aside... phải nằm ngoài tầm với của HTTP."""
    base, token = hosted
    with pytest.raises(urllib.error.HTTPError) as exc:
        _post(base, token, "_backup_db")
    assert exc.value.code == 404


def test_unknown_method_returns_404_not_a_crash(hosted):
    base, token = hosted
    with pytest.raises(urllib.error.HTTPError) as exc:
        _post(base, token, "khong_ton_tai")
    assert exc.value.code == 404


def test_exception_in_api_becomes_a_normal_error_response(hosted):
    """Lỗi trong backend phải trả về {ok: false} để UI hiện được, chứ
    không làm sập cả máy chủ."""
    base, token = hosted
    # submit_preferences thiếu tham số -> TypeError bên trong
    res = _post(base, token, "submit_preferences", [])
    assert res["ok"] is False
    assert res["errors"]


def test_html_is_served_with_the_pywebview_shim_injected(hosted):
    """Đây là mấu chốt khiến app.js/recovery.js chạy y nguyên, không sửa gì."""
    base, _ = hosted
    with urllib.request.urlopen(f"{base}/index.html") as r:
        html = r.read().decode("utf-8")
    assert "window.pywebview" in html
    assert "/__api__/" in html
    # chèn TRƯỚC </head> để window.pywebview tồn tại trước khi app.js chạy
    assert html.index("window.pywebview") < html.index("</head>")
    # và nội dung gốc vẫn còn nguyên
    assert 'src="app.js"' in html


def test_recovery_page_also_gets_the_shim(hosted):
    base, _ = hosted
    with urllib.request.urlopen(f"{base}/recovery.html") as r:
        html = r.read().decode("utf-8")
    assert "window.pywebview" in html
    assert 'src="recovery.js"' in html


def test_static_assets_are_served_unmodified(hosted):
    base, _ = hosted
    with urllib.request.urlopen(f"{base}/app.js") as r:
        js = r.read().decode("utf-8")
    # app.js phải được phục vụ NGUYÊN VĂN — chỉ .html mới bị chèn shim
    assert "callApi" in js
    with open(os.path.join(RESOURCE_DIR, "app.js"), encoding="utf-8") as f:
        assert js == f.read()
    # style.css cũng phải phục vụ được, nếu không giao diện sẽ trắng trơn
    with urllib.request.urlopen(f"{base}/style.css") as r:
        assert "--ink" in r.read().decode("utf-8")


def test_server_binds_only_to_loopback(hosted):
    """Không được lắng nghe ra ngoài mạng — đây là máy kiosk chứa dữ liệu
    học sinh."""
    base, _ = hosted
    assert base.startswith("http://127.0.0.1:")


# ------------------------------------------------------------------ #
# Chế độ CỬA SỔ RIÊNG (app mode)
#
# Yêu cầu: app phải mở như một ứng dụng riêng — cửa sổ riêng, KHÔNG
# thanh địa chỉ, KHÔNG tab — chứ không phải một tab lẫn trong trình
# duyệt người dùng đang mở. Đây là phần mềm kiosk đặt ở trường: học
# sinh không được nhìn thấy thanh địa chỉ để gõ sang trang khác.
# ------------------------------------------------------------------ #


def test_app_window_command_asks_for_a_separate_window():
    cmd = browser_host.build_app_window_command(
        "/usr/bin/chromium",
        "http://127.0.0.1:9/index.html?t=abc",
        "/tmp/ho-so",
        1280, 800,
    )
    assert cmd[0] == "/usr/bin/chromium"
    # --app= là cờ DUY NHẤT tạo cửa sổ không thanh địa chỉ, không tab.
    assert "--app=http://127.0.0.1:9/index.html?t=abc" in cmd
    # hồ sơ riêng: không dính extension/lịch sử/tab cũ của người dùng
    assert "--user-data-dir=/tmp/ho-so" in cmd
    assert "--window-size=1280,800" in cmd
    # tuyệt đối không được mở thành tab
    assert not any(c.startswith("--new-tab") for c in cmd)


def test_browser_lookup_prefers_env_override(monkeypatch, tmp_path):
    """Cho phép người vận hành chỉ định trình duyệt cụ thể khi máy
    trường cài ở đường dẫn lạ."""
    fake = tmp_path / "trinh-duyet"
    fake.write_text("")
    fake.chmod(0o755)
    monkeypatch.setenv("RBDA_BROWSER", str(fake))
    assert browser_host.find_app_window_browser() == str(fake)


def test_browser_lookup_ignores_env_override_that_does_not_exist(monkeypatch):
    """Đường dẫn rác phải bị bỏ qua, nếu không Popen sẽ ném lỗi."""
    monkeypatch.setenv("RBDA_BROWSER", "/khong/he/ton/tai/browser.exe")
    assert browser_host.find_app_window_browser() != "/khong/he/ton/tai/browser.exe"


def test_open_ui_falls_back_to_normal_browser_when_none_found(monkeypatch):
    monkeypatch.setattr(browser_host, "find_app_window_browser", lambda: None)
    opened = []
    monkeypatch.setattr(browser_host.webbrowser, "open", opened.append)
    browser_host.open_ui("http://x/y", 1280, 800)
    # Thà mở tab thường còn hơn không mở được gì.
    assert opened == ["http://x/y"]


def test_open_ui_falls_back_when_launching_the_browser_fails(monkeypatch):
    monkeypatch.setattr(
        browser_host, "find_app_window_browser", lambda: "/khong/ton/tai"
    )
    opened = []
    monkeypatch.setattr(browser_host.webbrowser, "open", opened.append)
    browser_host.open_ui("http://x/y", 1280, 800)
    assert opened == ["http://x/y"]


def test_open_ui_uses_app_window_when_a_browser_exists(monkeypatch):
    calls = []
    monkeypatch.setattr(browser_host, "find_app_window_browser", lambda: "/bin/echo")
    monkeypatch.setattr(
        browser_host.subprocess, "Popen", lambda cmd, **kw: calls.append(cmd)
    )
    monkeypatch.setattr(
        browser_host.webbrowser, "open",
        lambda u: pytest.fail("khong duoc mo tab trinh duyet thuong"),
    )
    browser_host.open_ui("http://x/y", 1280, 800)
    assert calls
    assert any(c.startswith("--app=") for c in calls[0])


# ------------------------------------------------------------------ #
# TẮT ĐÚNG LÚC — không tắt nhầm khi thu nhỏ, tắt ngay khi đóng thật
#
# Cách đếm ping ĐÃ HỎNG THẬT trên máy học sinh ngày 30/08: trình duyệt
# không bóp thưa bộ đếm giờ của trang bị che, nó ĐÓNG BĂNG hẳn (Chromium
# intensive throttling, Edge còn thêm Efficiency mode). Ping ngừng hẳn,
# máy chủ tự tắt trong khi cửa sổ VẪN MỞ, và mọi thao tác sau đó báo
# "TypeError: Failed to fetch" mà không nói vì sao.
#
# Nay tín hiệu chính là một KẾT NỐI MỞ (EventSource): trình duyệt không
# đóng băng socket, chỉ đóng băng bộ đếm giờ. Ping chỉ còn là lưới đỡ khi
# kết nối đó không dùng được.
# ------------------------------------------------------------------ #


def test_ping_timeout_outlasts_browser_throttling():
    """Lưới đỡ khi không có kết nối sống nào thì vẫn phải rộng rãi."""
    assert browser_host._PING_TIMEOUT_SECONDS >= 90


def _mo_ket_noi_song(base, token):
    """Mở kết nối EventSource và GIỮ nguyên — không đọc tới hết."""
    return urllib.request.urlopen(f"{base}/__alive__?t={token}", timeout=5)


def test_ket_noi_song_can_dung_token(hosted):
    base, _ = hosted
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(f"{base}/__alive__?t=sai", timeout=5)
    assert e.value.code == 403


def test_shim_mo_ket_noi_song(hosted):
    base, _ = hosted
    with urllib.request.urlopen(f"{base}/index.html") as r:
        html = r.read().decode("utf-8")
    assert "EventSource" in html
    assert "/__alive__" in html


def test_cua_so_mo_thi_khong_tat_du_ping_bi_dong_bang(monkeypatch, api):
    """Đây chính là lỗi học sinh gặp: trang bị đóng băng, ping ngừng hẳn,
    máy chủ tắt trong khi cửa sổ vẫn mở. Kết nối sống phải giữ được nó."""
    monkeypatch.setattr(browser_host, "_PING_TIMEOUT_SECONDS", 1)
    monkeypatch.setattr(browser_host, "_GRACE_SECONDS", 1)
    monkeypatch.setattr(browser_host, "_ALIVE_BEAT_SECONDS", 0.2)
    url = browser_host.serve(api, RESOURCE_DIR, "index.html", open_browser=False)
    base, token = url.split("/index.html?t=")

    song = _mo_ket_noi_song(base, token)
    try:
        # Một ping duy nhất rồi im hẳn — đúng như trang bị đóng băng.
        urllib.request.urlopen(urllib.request.Request(
            f"{base}/__ping__", data=b"", method="POST"), timeout=5).read()
        time.sleep(8)          # quá xa ngưỡng ping (1 giây)
        res = _post(base, token, "get_dashboard_status")
        assert res["ok"] is True, "máy chủ đã tắt dù cửa sổ còn mở"
    finally:
        song.close()


def test_dong_cua_so_thi_may_chu_tat(monkeypatch, api):
    """Mặt còn lại: đóng thật thì phải tắt, không để tiến trình chạy ngầm."""
    monkeypatch.setattr(browser_host, "_PING_TIMEOUT_SECONDS", 1)
    monkeypatch.setattr(browser_host, "_GRACE_SECONDS", 1)
    monkeypatch.setattr(browser_host, "_ALIVE_BEAT_SECONDS", 0.2)
    url = browser_host.serve(api, RESOURCE_DIR, "index.html", open_browser=False)
    base, token = url.split("/index.html?t=")

    song = _mo_ket_noi_song(base, token)
    urllib.request.urlopen(urllib.request.Request(
        f"{base}/__ping__", data=b"", method="POST"), timeout=5).read()
    song.close()               # cửa sổ đóng

    for _ in range(40):        # tối đa 20 giây
        time.sleep(0.5)
        try:
            urllib.request.urlopen(f"{base}/index.html", timeout=2).read()
        except Exception:
            return             # đã tắt — đúng
    pytest.fail("máy chủ vẫn chạy sau khi cửa sổ đóng")


def test_shim_reports_the_window_closing(hosted):
    base, _ = hosted
    with urllib.request.urlopen(f"{base}/index.html") as r:
        html = r.read().decode("utf-8")
    # Đóng cửa sổ -> báo ngay, không phải chờ hết ngưỡng.
    assert "pagehide" in html
    assert "sendBeacon" in html
    assert "/__closed__" in html


def test_closing_the_window_shuts_the_server_down(hosted):
    base, token = hosted
    req = urllib.request.Request(
        f"{base}/__closed__?t={token}", data=b"", method="POST"
    )
    with urllib.request.urlopen(req) as r:
        assert json.loads(r.read())["ok"] is True

    # Máy chủ phải thật sự ngừng phục vụ (chứ không chỉ trả lời cho có).
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{base}/index.html", timeout=1)
        except Exception:
            return
        time.sleep(0.2)
    pytest.fail("may chu van con phuc vu sau khi cua so da dong")


def test_close_request_without_the_token_is_ignored(hosted):
    """Không để một trang web khác trong cùng máy tắt được app."""
    base, _ = hosted
    req = urllib.request.Request(f"{base}/__closed__?t=sai", data=b"", method="POST")
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req)
    assert exc.value.code == 403
    # và máy chủ vẫn sống
    with urllib.request.urlopen(f"{base}/index.html") as r:
        assert r.status == 200
