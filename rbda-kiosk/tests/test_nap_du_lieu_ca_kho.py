"""Các ca khó khi nạp dữ liệu — tìm ra bằng cách soát thủ công luồng nhập.

Ba vấn đề file này khoá lại, hai trong số đó là MẤT DỮ LIỆU IM LẶNG:

1. Cùng một student_id xuất hiện hai lần trong file dạng rộng: dòng sau
   âm thầm ghi đè dòng trước, không một cảnh báo. Học sinh điền form hai
   lần, hoặc người nhập dán nhầm, là mất nguyện vọng của một dòng.

2. student_id chỉ khác hoa/thường (`hs001` và `HS001`) tạo ra HAI học
   sinh riêng biệt. File tick chọn dùng kiểu này, file nguyện vọng dùng
   kiểu kia, thế là hai hồ sơ rời rạc mỗi cái thiếu một nửa — và pipeline
   xử lý cả hai như hai người thật.

3. club_id khác hoa/thường thì cả học sinh bị bỏ qua. Ca này ĐÃ có cảnh
   báo rõ nên không im lặng, nhưng vẫn là mất công vô ích: đây rõ ràng là
   cùng một CLB.
"""

import pytest


@pytest.fixture
def api_co_club(api):
    api.create_or_update_club("clb_bongro", "CLB Bóng rổ", 20, 0, "")
    api.create_or_update_club("clb_amnhac", "CLB Âm nhạc", 20, 0, "")
    return api


def ma_canh_bao(res):
    return [w["code"] for w in res["data"]["warnings"]]


# ------------------------------------------------------------------ #
# 1. TRÙNG student_id TRONG CÙNG MỘT FILE
# ------------------------------------------------------------------ #


def test_trung_student_id_trong_file_dang_rong_phai_canh_bao(api_co_club):
    res = api_co_club.import_preferences_csv(
        "student_id,name,pref_1\n"
        "HS001,An,clb_bongro\n"
        "HS001,An,clb_amnhac\n"
    )
    assert res["ok"] is True
    assert "csv_duplicate_student_rows" in ma_canh_bao(res)


def test_trung_student_id_giu_dong_CUOI_va_noi_ro(api_co_club):
    """Giữ dòng cuối vì đó thường là bản sửa mới nhất — nhưng phải nói
    ra, không được im."""
    res = api_co_club.import_preferences_csv(
        "student_id,name,pref_1\n"
        "HS001,An,clb_bongro\n"
        "HS001,An,clb_amnhac\n"
    )
    assert api_co_club.get_student_entry_state("HS001")["data"]["ranked_clubs"] == ["clb_amnhac"]
    w = next(w for w in res["data"]["warnings"] if w["code"] == "csv_duplicate_student_rows")
    assert w["params"]["student_id"] == "HS001"
    assert w["params"]["n"] == 2


def test_trung_trong_file_chon_club_thi_cung_canh_bao(api_co_club):
    res = api_co_club.import_test_selection_csv(
        "student_id,name,test_club_1\n"
        "HS001,An,clb_bongro\n"
        "HS001,An,clb_amnhac\n"
    )
    assert "csv_duplicate_student_rows" in ma_canh_bao(res)


def test_dang_DAI_nhieu_dong_moi_hoc_sinh_la_BINH_THUONG_khong_canh_bao(api_co_club):
    """Dạng dài vốn dĩ mỗi lựa chọn một dòng — đó không phải trùng lặp."""
    res = api_co_club.import_preferences_csv(
        "student_id,name,club_id,rank\n"
        "HS001,An,clb_bongro,1\n"
        "HS001,An,clb_amnhac,2\n"
    )
    assert "csv_duplicate_student_rows" not in ma_canh_bao(res)
    assert api_co_club.get_student_entry_state("HS001")["data"]["ranked_clubs"] == [
        "clb_bongro", "clb_amnhac"
    ]


# ------------------------------------------------------------------ #
# 2. student_id CHỈ KHÁC HOA/THƯỜNG
# ------------------------------------------------------------------ #


def test_ma_hoc_sinh_khac_hoa_thuong_phai_duoc_canh_bao(api_co_club):
    """KHÔNG tự gộp — gộp nhầm hai em thật là hỏng nặng hơn. Chỉ báo để
    người nhập tự quyết."""
    api_co_club.import_test_selection_csv(
        "student_id,name,test_club_1\nhs001,An,clb_bongro\n"
    )
    res = api_co_club.import_preferences_csv(
        "student_id,name,pref_1\nHS001,An,clb_bongro\n"
    )
    assert "csv_student_id_case_conflict" in ma_canh_bao(res)
    w = next(w for w in res["data"]["warnings"]
             if w["code"] == "csv_student_id_case_conflict")
    assert w["params"]["student_id"] == "HS001"
    assert w["params"]["da_co"] == "hs001"


def test_ma_hoc_sinh_khop_chinh_xac_thi_khong_canh_bao(api_co_club):
    api_co_club.import_test_selection_csv(
        "student_id,name,test_club_1\nHS001,An,clb_bongro\n"
    )
    res = api_co_club.import_preferences_csv(
        "student_id,name,pref_1\nHS001,An,clb_bongro\n"
    )
    assert "csv_student_id_case_conflict" not in ma_canh_bao(res)


def test_khong_tu_gop_hai_ma_khac_hoa_thuong(api_co_club):
    """Cảnh báo, nhưng dữ liệu vẫn giữ nguyên hai bản ghi — người nhập
    mới biết hai mã đó là một người hay hai người."""
    api_co_club.import_test_selection_csv(
        "student_id,name,test_club_1\nhs001,An,clb_bongro\n"
    )
    api_co_club.import_preferences_csv(
        "student_id,name,pref_1\nHS001,An,clb_bongro\n"
    )
    ma = {r["student_id"] for r in api_co_club.list_students_admin("")["data"]["rows"]}
    assert ma == {"hs001", "HS001"}


# ------------------------------------------------------------------ #
# 3. club_id KHÁC HOA/THƯỜNG
# ------------------------------------------------------------------ #


def test_club_id_khac_hoa_thuong_van_nhan_ra(api_co_club):
    """Rõ ràng là cùng một CLB — không có lý do bắt cả học sinh bị loại."""
    res = api_co_club.import_preferences_csv(
        "student_id,name,pref_1,pref_2\nHS001,An,CLB_BongRo,Clb_AmNhac\n"
    )
    assert res["ok"] is True, res["errors"]
    assert res["data"]["n_students_skipped"] == 0, res["data"]["warnings"]
    # ghi vào DB bằng đúng mã GỐC của CLB, không phải mã người dùng gõ
    assert api_co_club.get_student_entry_state("HS001")["data"]["ranked_clubs"] == [
        "clb_bongro", "clb_amnhac"
    ]


def test_club_id_khac_hoa_thuong_trong_file_chon_club_thi(api_co_club):
    res = api_co_club.import_test_selection_csv(
        "student_id,name,test_club_1\nHS001,An,CLB_BONGRO\n"
    )
    assert res["data"]["n_students_skipped"] == 0, res["data"]["warnings"]
    assert api_co_club.get_student_entry_state("HS001")["data"]["tested_clubs"] == ["clb_bongro"]


def test_club_id_SAI_HAN_van_bi_bo_qua_va_bao_ro(api_co_club):
    """Tha thứ hoa/thường KHÔNG được biến thành tha thứ mọi thứ."""
    res = api_co_club.import_preferences_csv(
        "student_id,name,pref_1\nHS001,An,clb_khong_ton_tai\n"
    )
    assert res["data"]["n_students_skipped"] == 1
    assert "csv_unknown_clubs_skipped" in ma_canh_bao(res)


def test_hai_club_chi_khac_hoa_thuong_thi_KHONG_tu_doan(api):
    """Nếu trường thật sự tạo cả clb_a lẫn CLB_A thì phần mềm không được
    tự chọn hộ — khớp chính xác vẫn thắng."""
    api.create_or_update_club("clb_a", "CLB thường", 10, 0, "")
    api.create_or_update_club("CLB_A", "CLB hoa", 10, 0, "")
    api.import_preferences_csv("student_id,name,pref_1\nHS001,An,CLB_A\n")
    assert api.get_student_entry_state("HS001")["data"]["ranked_clubs"] == ["CLB_A"]
