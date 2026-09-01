"""Test khối "Vùng nguy hiểm" bằng TRÌNH DUYỆT THẬT (Playwright + Chromium).

Có một loại lỗi mà không test Python nào bắt được: đặt chuỗi giao diện
nhầm sang bảng mã lỗi (hoặc ngược lại) trong `i18n.js`. Khi đó `t()` trả
về đúng cái KHOÁ chứ không phải câu tiếng Việt, và người dùng nhìn thấy
`btn_reset_all` in ra trên nút. Dự án đã dính đúng lỗi này một lần và
chỉ phát hiện khi mở app thật.

Nên file này kiểm tra hai điều mà tầng Python mù tịt:
  1. Nhãn nút và tiêu đề khối hiện ra bằng tiếng người, không phải khoá.
  2. Xác nhận hai bước thật sự chặn: bấm MỘT lần không được xoá gì.

Máy nào không có playwright/Chromium thì bỏ qua cả file — đây là lớp
kiểm tra thêm, không phải điều kiện để chạy bộ test.
"""

import os
import sqlite3

import pytest

pytest.importorskip("playwright", reason="chưa cài playwright")
from playwright.sync_api import sync_playwright  # noqa: E402

import browser_host  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROMIUM):
    CHROMIUM = None


@pytest.fixture
def api_co_du_lieu(api):
    api.create_or_update_club("clb_a", "CLB A", 2, 0, "")
    for sid in ("HS01", "HS02"):
        api.create_student_if_missing(sid, "Học sinh " + sid)
        api.submit_test_selection(sid, ["clb_a"])
        api.submit_preferences(sid, ["clb_a"])
        api.submit_club_scores("clb_a", [{"student_id": sid, "score": 8.0}])
    return api


@pytest.fixture
def trang(api_co_du_lieu):
    if CHROMIUM is None:
        pytest.skip("khong tim thay Chromium")
    url = browser_host.serve(api_co_du_lieu, GOC, "index.html", open_browser=False)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        page = br.new_page()
        loi = []
        page.on("pageerror", lambda e: loi.append(str(e)))
        page.goto(url)
        page.wait_for_selector("#dropZone")
        page.locator('[data-tab="admin"]').click()
        page.wait_for_selector("#btnResetAll")
        yield page, loi, api_co_du_lieu
        br.close()


def _dem_hoc_sinh(api):
    conn = sqlite3.connect(api.db_path)
    n = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    return n


def test_nhan_hien_ra_bang_tieng_viet_khong_phai_khoa_i18n(trang):
    """Chuỗi giao diện phải nằm trong UI_STRINGS. Đặt nhầm sang bảng mã
    lỗi thì chỗ này in ra đúng chữ 'btn_reset_all'."""
    page, loi, _ = trang
    for chon in ("#btnResetStudents", "#btnResetAll"):
        chu = page.locator(chon).inner_text().strip()
        assert chu, chon
        assert "_" not in chu, "hien ra khoa i18n thay vi cau chu: %r" % chu

    khoi = page.locator('[data-i18n="danger_zone_title"]')
    assert "Vùng nguy hiểm" in khoi.inner_text()
    an_toan = page.locator('[data-i18n="danger_zone_safety"]').inner_text()
    assert "SAO LƯU" in an_toan and "run_history" in an_toan
    assert not loi, loi


def test_bam_mot_lan_khong_xoa_gi(trang):
    """Bước xác nhận thứ nhất chỉ đổi nhãn nút, tuyệt đối không gọi API."""
    page, loi, api = trang
    assert _dem_hoc_sinh(api) == 2

    nut = page.locator("#btnResetAll")
    nhan_goc = nut.inner_text()
    nut.click()
    page.wait_for_function(
        "document.querySelector('#btnResetAll').classList.contains('is-confirming')"
    )
    assert nut.inner_text() != nhan_goc
    assert _dem_hoc_sinh(api) == 2, "bam mot lan da xoa mat du lieu"
    assert not loi, loi


def test_bam_lan_hai_moi_xoa_that_va_bao_ten_tep_sao_luu(trang):
    page, loi, api = trang
    nut = page.locator("#btnResetStudents")
    nut.click()
    page.wait_for_function(
        "document.querySelector('#btnResetStudents').classList.contains('is-confirming')"
    )
    nut.click()

    page.wait_for_function("document.querySelectorAll('.toast').length > 0", timeout=10000)
    thong_bao = page.locator(".toast").first.inner_text()
    assert ".bak-" in thong_bao, "toast phai noi ro da sao luu vao tep nao: %r" % thong_bao
    assert "{" not in thong_bao, "con cho trong chua thay: %r" % thong_bao

    assert _dem_hoc_sinh(api) == 0
    # Pham vi "hoc_sinh" nen CLB phai con nguyen.
    conn = sqlite3.connect(api.db_path)
    assert conn.execute("SELECT COUNT(*) FROM clubs").fetchone()[0] == 1
    conn.close()
    assert not loi, loi


def test_moi_o_so_tren_man_hinh_cap_nhat_ngay_sau_khi_xoa(trang):
    """Sau khi xoá, KHÔNG chỗ nào trên màn hình được nói số cũ nữa.

    Thanh bên luôn hiện dù đang ở tab nào. Trước bản vá, ngay sau khi
    xoá nó vẫn ghi "Chạy gần nhất: … 2/2 xếp được" cho một lần chạy mà
    dữ liệu đằng sau đã bị xoá sạch — màn hình nói một điều không đúng,
    ngay sau thao tác nguy hiểm nhất trong app.
    """
    page, loi, api = trang
    assert api.run_pipeline(seed=42)["ok"]
    page.locator('[data-tab="pipeline"]').click()
    page.wait_for_function(
        "document.querySelector('#statStudents').textContent !== '—'"
    )
    assert page.locator("#statStudents").inner_text() == "2"
    assert "Chạy gần nhất" in page.locator("#lastRunLine").inner_text()

    page.locator('[data-tab="admin"]').click()
    nut = page.locator("#btnResetStudents")
    nut.click()
    page.wait_for_function(
        "document.querySelector('#btnResetStudents').classList.contains('is-confirming')"
    )
    nut.click()
    page.wait_for_function("document.querySelectorAll('.toast').length > 0", timeout=10000)

    # Vẫn đang đứng ở tab Quản lý — không được bắt người dùng chuyển tab
    # mới thấy sự thật.
    page.wait_for_function(
        "document.querySelector('#lastRunLine').textContent.indexOf('gần nhất') === -1",
        timeout=10000,
    )
    page.wait_for_function(
        "document.querySelector('#statStudents').textContent === '0'", timeout=10000
    )
    assert page.locator("#statMatched").inner_text() == "0"
    # CLB giữ nguyên vì phạm vi là "học sinh".
    assert page.locator("#statClubs").inner_text() == "1"
    assert not loi, loi
