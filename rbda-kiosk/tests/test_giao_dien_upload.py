"""Test GIAO DIỆN nạp CSV bằng trình duyệt thật (Playwright + Chromium).

Toàn bộ test còn lại của dự án chạy ở tầng Python — không có test nào
chạm tới `app.js`. Mà vùng nạp file là chỗ người dùng thao tác nhiều
nhất, và cũng là chỗ vừa có bug nặng nhất: hai ô riêng bắt người dùng
tự chọn, chọn nhầm thì dữ liệu vào SAI BẢNG mà vẫn báo thành công.

File này chạy giao diện thật để bảo đảm luồng mới không vỡ trong im
lặng. Máy nào không có `playwright` hoặc không có Chromium thì tự bỏ
qua — nó là lớp kiểm tra thêm, không phải điều kiện bắt buộc để chạy
được bộ test.
"""

import os

import pytest

pytest.importorskip("playwright", reason="chưa cài playwright")
from playwright.sync_api import sync_playwright  # noqa: E402

import browser_host  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAU = os.path.join(GOC, "mau_csv")

# Chromium do Playwright cài sẵn; đường dẫn này là của môi trường phát
# triển. Không có thì bỏ qua cả file.
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROMIUM):
    CHROMIUM = None


@pytest.fixture
def trang(api):
    """Mở index.html thật, backend là PipelineAPI thật qua browser_host."""
    if CHROMIUM is None:
        pytest.skip("khong tim thay Chromium")
    url = browser_host.serve(api, GOC, "index.html", open_browser=False)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        page = br.new_page()
        loi = []
        page.on("pageerror", lambda e: loi.append(str(e)))
        page.goto(url)
        page.wait_for_selector("#dropZone")
        yield page, loi
        br.close()


def mau(ten):
    return os.path.join(MAU, ten)


def test_tha_ba_file_mot_luc_va_nhan_dien_dung_tung_file(trang):
    page, loi = trang
    page.locator("#fileAny").set_input_files([
        mau("05_danh_sach_club.csv"),
        mau("03_nguyen_vong_dang_rong.csv"),
        mau("01_chon_club_thi_dang_rong.csv"),
    ])
    page.wait_for_function("document.querySelectorAll('.queue-row').length === 3")

    nhan_dien = {
        r.locator(".queue-file").inner_text(): r.locator(".queue-detail").inner_text()
        for r in page.locator(".queue-row").all()
    }
    assert "Danh sách CLB" in nhan_dien["05_danh_sach_club.csv"]
    assert "Xếp hạng nguyện vọng" in nhan_dien["03_nguyen_vong_dang_rong.csv"]
    assert "Chọn CLB muốn thi" in nhan_dien["01_chon_club_thi_dang_rong.csv"]
    assert not loi, loi


def test_nhap_tat_ca_tu_xep_CLB_truoc_nen_khong_hoc_sinh_nao_bi_bo_qua(trang, api):
    """Đây là phép thử thật của thứ tự nhập: học sinh tham chiếu tới
    club_id, nạp học sinh trước khi có CLB thì CẢ học sinh bị bỏ qua.
    Thả CLB ở giữa để chắc chắn thứ tự không phải nhờ may."""
    page, loi = trang
    page.locator("#fileAny").set_input_files([
        mau("03_nguyen_vong_dang_rong.csv"),
        mau("05_danh_sach_club.csv"),
        mau("01_chon_club_thi_dang_rong.csv"),
    ])
    page.wait_for_function("document.querySelectorAll('.queue-row').length === 3")
    page.locator("#btnImportAll").click()
    page.wait_for_function(
        "document.querySelectorAll('.queue-row.is-done').length === 3", timeout=15000
    )

    for r in page.locator(".queue-row").all():
        assert "0 bỏ qua" in r.locator(".queue-detail").inner_text() or \
               "0 dòng bỏ qua" in r.locator(".queue-detail").inner_text()

    # và dữ liệu vào ĐÚNG bảng, không lẫn sang nhau
    st = api.get_student_entry_state("HS001")["data"]
    assert st["ranked_clubs"] == ["clb_bongro", "clb_amnhac", "clb_tienganh"]
    assert sorted(st["tested_clubs"]) == ["clb_amnhac", "clb_bongro", "clb_tienganh"]
    assert len(api.list_clubs_admin()["data"]) == 5
    assert not loi, loi


def test_file_mo_ho_hien_o_chon_loai_chu_khong_tu_doan(trang):
    page, loi = trang
    page.locator("#fileAny").set_input_files([mau("02_chon_club_thi_dang_dai.csv")])
    page.wait_for_selector(".queue-row.is-ambiguous")

    row = page.locator(".queue-row").first
    assert "Chưa chắc" in row.locator(".queue-detail").inner_text()
    lua_chon = row.locator("select option").all_inner_texts()
    assert "Chọn CLB muốn thi" in lua_chon
    assert "Xếp hạng nguyện vọng" in lua_chon
    assert not loi, loi


def test_chon_loai_cho_file_mo_ho_roi_nhap_thi_vao_dung_bang(trang, api):
    page, loi = trang
    page.locator("#fileAny").set_input_files([mau("05_danh_sach_club.csv")])
    page.wait_for_function("document.querySelectorAll('.queue-row').length === 1")
    page.locator("#btnImportAll").click()
    page.wait_for_selector(".queue-row.is-done")

    page.locator("#btnClearQueue").click()
    page.locator("#fileAny").set_input_files([mau("02_chon_club_thi_dang_dai.csv")])
    page.wait_for_selector(".queue-row.is-ambiguous")
    page.locator(".queue-row select").select_option("test_selection")
    page.locator("#btnImportAll").click()
    page.wait_for_selector(".queue-row.is-done")

    st = api.get_student_entry_state("HS001")["data"]
    assert sorted(st["tested_clubs"]) == ["clb_amnhac", "clb_bongro", "clb_tienganh"]
    assert st["ranked_clubs"] == []   # KHÔNG lẫn sang bảng nguyện vọng
    assert not loi, loi


def test_bo_danh_sach_xoa_luon_phan_hoi_cua_lan_nhap_truoc(trang):
    """Để lại kết quả cũ thì người dùng tưởng đó là của danh sách đang có."""
    page, loi = trang
    page.locator("#fileAny").set_input_files([mau("05_danh_sach_club.csv")])
    page.wait_for_function("document.querySelectorAll('.queue-row').length === 1")
    page.locator("#btnImportAll").click()
    page.wait_for_selector(".queue-row.is-done")
    assert page.locator("#feedbackImportAll").inner_text().strip()

    page.locator("#btnClearQueue").click()
    page.wait_for_function(
        "document.getElementById('feedbackImportAll').textContent.trim() === ''"
    )
    assert page.locator("#importQueue").is_hidden()
    assert not loi, loi


# ------------------------------------------------------------------ #
# THẢ THẲNG FILE EXCEL
#
# Microsoft Forms xuất ra .xlsx. Đây là phép thử end-to-end của đường
# đi mới: trình duyệt đọc file nhị phân -> base64 -> Python đọc bằng
# openpyxl -> quay lại luồng nhận diện như file CSV thường.
# ------------------------------------------------------------------ #


def test_tha_file_excel_duoc_nhan_dien_nhu_file_csv(trang):
    page, loi = trang
    page.locator("#fileAny").set_input_files([mau("MAU_01_danh_sach_CLB.xlsx")])
    page.wait_for_function("document.querySelectorAll('.queue-row').length === 1")
    chi_tiet = page.locator(".queue-row .queue-detail").inner_text()
    assert "Danh sách CLB" in chi_tiet
    assert not loi, loi


def test_tha_ca_excel_lan_csv_cung_luc_va_nhap_het(trang, api):
    """Trường có thể có file này .xlsx, file kia .csv — phải trộn được."""
    page, loi = trang
    page.locator("#fileAny").set_input_files([
        mau("MAU_03_xep_hang_nguyen_vong.xlsx"),
        mau("05_danh_sach_club.csv"),
        mau("MAU_02_chon_CLB_muon_thi.xlsx"),
    ])
    page.wait_for_function("document.querySelectorAll('.queue-row').length === 3")
    page.locator("#btnImportAll").click()
    page.wait_for_function(
        "document.querySelectorAll('.queue-row.is-done').length === 3", timeout=20000
    )

    st = api.get_student_entry_state("HS001")["data"]
    assert st["ranked_clubs"] == ["clb_bongro", "clb_amnhac", "clb_tienganh"]
    assert sorted(st["tested_clubs"]) == ["clb_amnhac", "clb_bongro", "clb_tienganh"]
    assert len(api.list_clubs_admin()["data"]) == 5
    assert not loi, loi


def test_file_excel_hong_bao_loi_chu_khong_sap_giao_dien(trang, tmp_path):
    hong = tmp_path / "khong_phai_excel.xlsx"
    hong.write_bytes(b"day khong phai file excel")
    page, loi = trang
    page.locator("#fileAny").set_input_files([str(hong)])
    page.wait_for_selector(".queue-row.is-unknown")
    assert page.locator(".queue-row .queue-detail").inner_text().strip()
    assert not loi, loi
