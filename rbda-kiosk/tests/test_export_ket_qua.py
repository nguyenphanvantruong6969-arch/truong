"""Kiểm tra FILE KẾT QUẢ mà nhà trường nhận được sau khi chạy pipeline.

Trước đây file xuất ra chỉ có hai cột mã: `student_id,club_id`. Nhìn vào
đó không biết em nào tên gì, đỗ CLB nào, đỗ nguyện vọng thứ mấy — tức là
không dán bảng, không gửi phụ huynh, không phát cho giáo viên phụ trách
CLB được. Toàn bộ dữ liệu đó ĐÃ nằm sẵn trong DB, chỉ là câu lệnh xuất
không lấy.

File này khoá ba thứ: đủ cột để dùng được, Excel mở đúng tiếng Việt, và
người dùng biết file nằm ở đâu.
"""

import csv
import os

import pytest


@pytest.fixture
def api_da_chay(api, tmp_path):
    """Một lần chạy hoàn chỉnh: club, học sinh, điểm, pipeline."""
    api.create_or_update_club("clb_bongro", "CLB Bóng rổ", 2, 0, "")
    api.create_or_update_club("clb_amnhac", "CLB Âm nhạc", 5, 2, "chinh_sach")

    api.import_preferences_csv(
        "student_id,name,pref_1,pref_2\n"
        "HS001,Nguyễn Văn An,clb_bongro,clb_amnhac\n"
        "HS002,Trần Thị Bình,clb_bongro,clb_amnhac\n"
        "HS003,Lê Minh Cường,clb_amnhac,\n"
    )
    api.bulk_set_reserve_group(["HS003"], "chinh_sach")
    for c in api.get_scoring_overview()["data"]:
        ds = api.get_club_applicants_for_scoring(c["club_id"])["data"]["applicants"]
        if ds:
            api.submit_club_scores(
                c["club_id"],
                [{"student_id": u["student_id"], "score": 9.0 - i} for i, u in enumerate(ds)],
            )
    api.run_pipeline(seed=42)
    return api


def doc_csv(path):
    """Đọc như Excel đọc — utf-8-sig để nuốt BOM nếu có."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


# ------------------------------------------------------------------ #
# FILE TỔNG
# ------------------------------------------------------------------ #


def test_file_tong_co_ten_hoc_sinh_va_ten_club_chu_khong_chi_ma(api_da_chay, tmp_path):
    out = str(tmp_path / "ket_qua.csv")
    res = api_da_chay.export_csv(out)
    assert res["ok"] is True, res["errors"]

    rows = doc_csv(out)
    header = rows[0]
    # Đây chính là thứ trước đây thiếu.
    assert "Họ tên" in header
    assert "Tên CLB" in header
    assert "Nguyện vọng thứ" in header
    assert "Diện trúng tuyển" in header

    data = {r[0]: dict(zip(header, r)) for r in rows[1:]}
    assert data["HS001"]["Họ tên"] == "Nguyễn Văn An"
    assert data["HS001"]["Tên CLB"] == "CLB Bóng rổ"


def test_file_tong_ghi_ro_nguyen_vong_thu_may(api_da_chay, tmp_path):
    out = str(tmp_path / "ket_qua.csv")
    api_da_chay.export_csv(out)
    rows = doc_csv(out)
    header = rows[0]
    data = {r[0]: dict(zip(header, r)) for r in rows[1:]}
    # HS003 chỉ có 1 nguyện vọng (clb_amnhac) -> phải là nguyện vọng 1
    assert data["HS003"]["Nguyện vọng thứ"] == "1"


def test_dien_trung_tuyen_ghi_bang_tieng_Viet_khong_phai_ma_may(api_da_chay, tmp_path):
    """'reserve'/'general' là mã nội bộ — giáo viên không phải đoán."""
    out = str(tmp_path / "ket_qua.csv")
    api_da_chay.export_csv(out)
    rows = doc_csv(out)
    dien = {r[0]: dict(zip(rows[0], r))["Diện trúng tuyển"] for r in rows[1:]}
    assert set(dien.values()) <= {"Dự trữ", "Thường", ""}
    # HS003 thuộc nhóm chinh_sach, club Âm nhạc có 2 suất dự trữ
    assert dien["HS003"] == "Dự trữ"


def test_hoc_sinh_chua_duoc_xep_van_co_trong_file_va_ghi_ro(api_da_chay, tmp_path):
    """Bỏ sót các em chưa được xếp là bỏ sót đúng nhóm cần xử lý tiếp."""
    out = str(tmp_path / "ket_qua.csv")
    api_da_chay.export_csv(out)
    rows = doc_csv(out)
    assert len(rows) - 1 == 3  # đủ cả 3 em, không rơi em nào


def test_file_mo_bang_Excel_khong_loi_font(api_da_chay, tmp_path):
    """Không có BOM thì Excel hiện 'Nguyá»…n VÄƒn An'."""
    out = str(tmp_path / "ket_qua.csv")
    api_da_chay.export_csv(out)
    with open(out, "rb") as f:
        assert f.read(3) == b"\xef\xbb\xbf"


# ------------------------------------------------------------------ #
# NGƯỜI DÙNG PHẢI BIẾT FILE NẰM Ở ĐÂU
# ------------------------------------------------------------------ #


def test_xuat_vao_thu_muc_tai_ve_chu_khong_vao_thu_muc_phan_mem(tmp_path, api_da_chay):
    """Tệp kết quả phải rơi vào thư mục Tải xuống.

    Trước đây nó nằm CẠNH app.db — tìm được, nhưng nằm trong thư mục cài
    đặt, lẫn với .exe và dữ liệu. Không phải chỗ để tệp cho người ta mang
    đi. Ràng buộc cũ vẫn giữ nguyên: KHÔNG BAO GIỜ rơi vào thư mục làm
    việc của tiến trình, thứ có thể là bất kỳ đâu khi chạy .exe qua
    shortcut.
    """
    tai_ve = tmp_path / "TaiXuong"
    tai_ve.mkdir()
    api_da_chay.thu_muc_xuat = str(tai_ve)

    res = api_da_chay.export_csv("ket_qua.csv")
    assert res["ok"] is True
    duong_dan = res["data"]["path"]
    assert os.path.isabs(duong_dan), "phải trả về đường dẫn ĐẦY ĐỦ để hiện cho người dùng"
    assert os.path.dirname(duong_dan) == str(tai_ve)
    assert os.path.dirname(duong_dan) != os.path.dirname(api_da_chay.db_path)
    assert os.path.isfile(duong_dan)


def test_duong_dan_tuyet_doi_van_duoc_ton_trong_nguyen_van(tmp_path, api_da_chay):
    """Bên gọi tự chọn chỗ thì phần mềm không được tự ý dời đi nơi khác."""
    api_da_chay.thu_muc_xuat = str(tmp_path / "TaiXuong")
    cho_muon = tmp_path / "cho_rieng"
    cho_muon.mkdir()
    dich = cho_muon / "bao_cao.csv"

    res = api_da_chay.export_csv(str(dich))
    assert res["ok"] is True
    assert res["data"]["path"] == str(dich)
    assert dich.is_file()


def test_xuat_hai_lan_khong_ghi_de_tep_cu(tmp_path, api_da_chay):
    """Thư mục Tải xuống là thư mục của NGƯỜI DÙNG — ghi đè im lặng ở đó
    là xoá mất tệp họ có thể đang cần. Cư xử như trình duyệt: (2), (3)…"""
    tai_ve = tmp_path / "TaiXuong"
    tai_ve.mkdir()
    api_da_chay.thu_muc_xuat = str(tai_ve)

    lan_1 = api_da_chay.export_csv("")["data"]
    lan_2 = api_da_chay.export_csv("")["data"]

    assert lan_1["path"] != lan_2["path"], "lần xuất thứ hai đã ghi đè lần đầu"
    assert os.path.isfile(lan_1["path"]) and os.path.isfile(lan_2["path"])
    # thư mục theo CLB phải đi theo đúng tệp tổng của nó, không lẫn vào nhau
    assert lan_1["per_club_dir"] != lan_2["per_club_dir"]
    assert os.path.isdir(lan_1["per_club_dir"])
    assert os.path.isdir(lan_2["per_club_dir"])


def test_khong_tim_duoc_thu_muc_tai_ve_thi_lui_ve_canh_app_db(api_da_chay):
    """Không bao giờ để việc xuất kết quả THẤT BẠI chỉ vì chuyện chỗ để
    tệp. Không tìm được thư mục Tải xuống thì quay về hành vi cũ."""
    api_da_chay.thu_muc_xuat = "/khong/he/ton/tai/o/dau/ca"

    res = api_da_chay.export_csv("")
    assert res["ok"] is True, res["errors"]
    assert os.path.dirname(res["data"]["path"]) == os.path.dirname(api_da_chay.db_path)
    assert os.path.isfile(res["data"]["path"])


def test_khong_truyen_ten_file_van_xuat_duoc(tmp_path, api_da_chay):
    tai_ve = tmp_path / "TaiXuong"
    tai_ve.mkdir()
    api_da_chay.thu_muc_xuat = str(tai_ve)
    res = api_da_chay.export_csv()
    assert res["ok"] is True
    assert os.path.isfile(res["data"]["path"])


# ------------------------------------------------------------------ #
# TÁCH RIÊNG TỪNG CLB
# ------------------------------------------------------------------ #


def test_moi_club_mot_file_rieng_de_phat_cho_giao_vien_phu_trach(api_da_chay, tmp_path):
    out = str(tmp_path / "ket_qua.csv")
    res = api_da_chay.export_csv(out)
    thu_muc = res["data"]["per_club_dir"]
    assert os.path.isdir(thu_muc)

    ten_file = set(os.listdir(thu_muc))
    assert "clb_bongro.csv" in ten_file
    assert "clb_amnhac.csv" in ten_file

    rows = doc_csv(os.path.join(thu_muc, "clb_bongro.csv"))
    ma_hs = [r[0] for r in rows[1:]]
    # club Bóng rổ chỉ 2 suất -> đúng 2 em, và KHÔNG lẫn em của club khác
    assert len(ma_hs) == 2
    for sid in ma_hs:
        assert sid in ("HS001", "HS002")


def test_file_tung_club_co_ten_hoc_sinh(api_da_chay, tmp_path):
    out = str(tmp_path / "ket_qua.csv")
    res = api_da_chay.export_csv(out)
    rows = doc_csv(os.path.join(res["data"]["per_club_dir"], "clb_bongro.csv"))
    assert "Họ tên" in rows[0]
    assert any("Nguyễn Văn An" in r or "Trần Thị Bình" in r for r in rows[1:])


def test_hoc_sinh_chua_duoc_xep_co_file_rieng(api, tmp_path):
    """Nhà trường cần biết còn em nào chưa vào CLB nào để xử lý tiếp."""
    api.create_or_update_club("clb_bongro", "CLB Bóng rổ", 1, 0, "")
    api.import_preferences_csv(
        "student_id,name,pref_1\n"
        "HS001,Nguyễn Văn An,clb_bongro\n"
        "HS002,Trần Thị Bình,clb_bongro\n"
    )
    ds = api.get_club_applicants_for_scoring("clb_bongro")["data"]["applicants"]
    api.submit_club_scores(
        "clb_bongro",
        [{"student_id": u["student_id"], "score": 9.0 - i} for i, u in enumerate(ds)],
    )
    api.run_pipeline(seed=42)

    res = api.export_csv(str(tmp_path / "ket_qua.csv"))
    thu_muc = res["data"]["per_club_dir"]
    chua_xep = os.path.join(thu_muc, "_chua_duoc_xep.csv")
    assert os.path.isfile(chua_xep), os.listdir(thu_muc)
    assert len(doc_csv(chua_xep)) - 1 == 1  # đúng 1 em trượt


def test_club_id_co_ky_tu_duong_dan_khong_ghi_file_ra_ngoai_thu_muc(api, tmp_path):
    """club_id do trường tự đặt và KHÔNG bị giới hạn ký tự (xem
    create_or_update_club). Một mã như '../ngoai' không được phép làm
    file rơi ra ngoài thư mục kết quả."""
    api.create_or_update_club("../ngoai", "CLB Lạ", 5, 0, "")
    api.import_preferences_csv("student_id,name,pref_1\nHS001,Nguyễn Văn An,../ngoai\n")
    ds = api.get_club_applicants_for_scoring("../ngoai")["data"]["applicants"]
    api.submit_club_scores("../ngoai", [{"student_id": "HS001", "score": 8.0}])
    api.run_pipeline(seed=42)

    res = api.export_csv(str(tmp_path / "ket_qua.csv"))
    assert res["ok"] is True
    thu_muc = os.path.realpath(res["data"]["per_club_dir"])
    for ten in os.listdir(thu_muc):
        that = os.path.realpath(os.path.join(thu_muc, ten))
        assert that.startswith(thu_muc + os.sep), f"{ten} thoát ra ngoài thư mục"
