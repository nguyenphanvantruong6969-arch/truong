# -*- coding: utf-8 -*-
"""Canh phần chẩn đoán khởi động.

Lỗi gốc không phải pywebview hỏng — mà là **hỏng mà không ai biết vì
sao**. `main.py` ghi vết lỗi ra `sys.stderr`, còn bản đóng gói chạy
`console=False` thì không có stderr nào. Vết lỗi bị vứt đi đúng lúc nó
xảy ra, nên ba phiên làm việc phải đoán nguyên nhân.
"""

import io
import os
import sys

import pytest

import chan_doan

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_ghi_log_ra_dung_cho(tmp_path):
    chan_doan.ghi(str(tmp_path), "dòng một", "dòng hai")
    p = chan_doan.duong_log(str(tmp_path))
    assert os.path.exists(p)
    noi_dung = io.open(p, encoding="utf-8").read()
    assert "dòng một" in noi_dung and "dòng hai" in noi_dung


def test_ghi_log_noi_them_chu_khong_ghi_de(tmp_path):
    """Mất lần hỏng trước để lấy lần hỏng sau là mất đúng thứ cần so sánh."""
    chan_doan.ghi(str(tmp_path), "lần một")
    chan_doan.ghi(str(tmp_path), "lần hai")
    noi_dung = io.open(chan_doan.duong_log(str(tmp_path)), encoding="utf-8").read()
    assert "lần một" in noi_dung and "lần hai" in noi_dung


def test_ghi_log_khong_bao_gio_nem_loi():
    """Hỏng phần ghi log mà làm chết app thì tệ hơn cả lỗi đang chẩn đoán."""
    chan_doan.ghi("/khong/ton/tai/o/dau/ca", "gì đó")   # không được ném


def test_ghi_ngoai_le_luu_nguyen_van_vet_loi(tmp_path):
    try:
        raise ValueError("lỗi giả để thử")
    except ValueError:
        chan_doan.ghi_ngoai_le(str(tmp_path), "tiêu đề thử:")
    noi_dung = io.open(chan_doan.duong_log(str(tmp_path)), encoding="utf-8").read()
    assert "tiêu đề thử:" in noi_dung
    assert "ValueError" in noi_dung
    assert "lỗi giả để thử" in noi_dung


def test_go_dau_tai_ve_khong_lam_gi_ngoai_windows(tmp_path):
    (tmp_path / "a.dll").write_bytes(b"x")
    ket = chan_doan.go_dau_tai_ve(str(tmp_path))
    assert set(ket) == {"da_go", "bo_qua", "loi"}
    if not sys.platform.startswith("win"):
        assert ket == {"da_go": 0, "bo_qua": 0, "loi": 0}


def test_go_dau_tai_ve_chiu_duoc_thu_muc_khong_ton_tai():
    assert chan_doan.go_dau_tai_ve("/khong/ton/tai") == {
        "da_go": 0, "bo_qua": 0, "loi": 0}


# ------------------------------------------------------------------ #
# Thứ tự gọi: gỡ dấu PHẢI chạy trước khi nạp webview
# ------------------------------------------------------------------ #
def test_go_dau_tai_ve_duoc_goi_TRUOC_khi_nap_webview():
    """Đảo thứ tự là mất tác dụng HOÀN TOÀN mà không test nào đỏ.

    .NET quyết định nạp hay từ chối Python.Runtime.dll ngay lúc `import
    webview`. Gỡ dấu sau đó thì dấu đã bị đọc rồi — quá muộn. Đây đúng
    loại lỗi im lặng dự án này đã phải sửa mười lần: mã trông vẫn đúng,
    chạy vẫn không lỗi, chỉ là không còn tác dụng gì.
    """
    src = io.open(os.path.join(GOC, "main.py"), encoding="utf-8").read()
    vi_tri_go_dau = src.index("go_dau_tai_ve")
    vi_tri_nap_webview = src.index("import webview")
    assert vi_tri_go_dau < vi_tri_nap_webview, (
        "go_dau_tai_ve() phải đứng TRƯỚC `import webview` trong main.py")


def test_go_dau_tai_ve_chi_chay_o_ban_dong_goi():
    """Chạy từ mã nguồn thì thư mục là kho mã của lập trình viên, không
    phải gói tải về — không có gì để gỡ, và đụng vào là sai phạm vi."""
    src = io.open(os.path.join(GOC, "main.py"), encoding="utf-8").read()
    doan = src[src.index("go_dau_tai_ve") - 300:src.index("go_dau_tai_ve")]
    assert 'getattr(sys, "frozen", False)' in doan


# ------------------------------------------------------------------ #
# Người dùng phải NHÌN THẤY app đang chạy bằng đường nào
# ------------------------------------------------------------------ #
def test_shim_danh_dau_che_do_trinh_duyet():
    import browser_host
    assert "__CHE_DO_HIEN_THI" in browser_host._SHIM_TEMPLATE
    assert "trinh_duyet" in browser_host._SHIM_TEMPLATE


def test_giao_dien_co_cho_hien_che_do():
    html = io.open(os.path.join(GOC, "index.html"), encoding="utf-8").read()
    js = io.open(os.path.join(GOC, "app.js"), encoding="utf-8").read()
    assert 'id="cheDoHienThi"' in html
    assert "__CHE_DO_HIEN_THI" in js


@pytest.mark.parametrize("ma", ["display_native", "display_browser"])
def test_hai_chuoi_che_do_nam_o_UI_STRINGS_ca_hai_ngon_ngu(ma):
    """Đây là chuỗi GIAO DIỆN, không phải mã lỗi. Đặt nhầm vào bảng mã lỗi
    thì t() không tìm thấy và giao diện hiện ra nguyên cái khoá — đã xảy
    ra thật, chỉ lộ ra khi mở bằng trình duyệt thật."""
    js = io.open(os.path.join(GOC, "i18n.js"), encoding="utf-8").read()
    ui = js[js.index("const UI_STRINGS"):]
    assert ui.count(ma + ":") == 2, "phải có ở CẢ vi và en trong UI_STRINGS"

    from i18n_errors import MESSAGES
    assert ma not in MESSAGES, "chuỗi giao diện không được nằm trong bảng mã lỗi"


# ------------------------------------------------------------------ #
# Tệp cấu hình .NET phải nằm cạnh .exe, không phải trong _internal/
# ------------------------------------------------------------------ #
def test_co_tep_cau_hinh_net_cho_phep_nap_assembly_bi_danh_dau():
    p = os.path.join(GOC, "PhanBoCauLacBo.exe.config")
    assert os.path.exists(p), "thiếu PhanBoCauLacBo.exe.config"
    noi_dung = io.open(p, encoding="utf-8").read()
    assert "loadFromRemoteSources" in noi_dung
    assert 'enabled="true"' in noi_dung


def test_quy_trinh_build_chep_cau_hinh_ra_canh_exe():
    """Để trong kho mà không chép vào gói thì .NET không bao giờ đọc tới."""
    p = os.path.join(os.path.dirname(GOC), ".github", "workflows",
                     "build-windows-exe.yml")
    yml = io.open(p, encoding="utf-8").read()
    assert "PhanBoCauLacBo.exe.config dist/PhanBoCauLacBo/" in yml
