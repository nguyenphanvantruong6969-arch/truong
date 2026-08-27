"""Tests for browser_host — chế độ chạy dự phòng bằng trình duyệt, dùng
khi pywebview/pythonnet không khởi động được trên máy người dùng.

Điều quan trọng nhất phải bảo đảm: cầu nối HTTP này gọi ĐÚNG vào
PipelineAPI thật (không phải bản giả), và KHÔNG mở toang thứ gì ra ngoài
— chỉ nghe trên 127.0.0.1, bắt buộc có token, và không cho gọi phương
thức nội bộ (bắt đầu bằng dấu gạch dưới).
"""

import json
import os
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
