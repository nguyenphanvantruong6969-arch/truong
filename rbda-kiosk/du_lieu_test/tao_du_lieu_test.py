"""Sinh bộ DỮ LIỆU MÔ PHỎNG để chạy thử phần mềm ở quy mô thật.

    ./.venv/bin/python du_lieu_test/tao_du_lieu_test.py

⚠️  ĐÂY LÀ DỮ LIỆU BỊA, KHÔNG PHẢI HỌC SINH CÓ THẬT.
    Tên và mã đều do máy sinh ngẫu nhiên (có seed nên lần nào cũng ra
    đúng bộ đó). Trình bày như số liệu khảo sát thật là bịa đặt dữ liệu.

Sinh hai bộ:
  BỘ SẠCH   — 120 học sinh, 10 CLB, không lỗi. Dùng để chạy thử trọn
              quy trình từ nạp file tới xuất kết quả.
  BỘ CÓ LỖI — cố ý cài sẵn 5 tình huống sai, để kiểm tra phần mềm có
              thật sự cảnh báo hay không.
"""

import os
import random

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

THU_MUC = os.path.dirname(os.path.abspath(__file__))
SEED = 2026
XANH = PatternFill("solid", fgColor="DCE9E0")
VANG = PatternFill("solid", fgColor="F7EEDA")

# --------------------------------------------------------------- #
# 10 CLB — tổng 130 suất cho 120 em. Dư suất trên tổng, nhưng vì
# nguyện vọng dồn vào vài CLB nên các CLB hẹp vẫn chật: sẽ có em
# không được xếp, đủ để kiểm tra file _chua_duoc_xep.csv.
# --------------------------------------------------------------- #
CLB = [
    # (mã, tên, chỉ tiêu, chỉ tiêu dự trữ, nhóm dự trữ)
    ("clb_bongro",    "CLB Bóng rổ",           18, 0, ""),
    ("clb_bongda",    "CLB Bóng đá",           20, 0, ""),
    ("clb_tienganh",  "CLB Tiếng Anh",         16, 4, "chinh_sach"),
    ("clb_tinhoc",    "CLB Tin học",           12, 3, "chinh_sach"),
    ("clb_robotics",  "CLB Robotics",           8, 0, ""),
    ("clb_amnhac",    "CLB Âm nhạc",           14, 0, ""),
    ("clb_mythuat",   "CLB Mỹ thuật",          12, 3, "khoi_10"),
    ("clb_vanhoc",    "CLB Văn học",           10, 0, ""),
    ("clb_khoahoc",   "CLB Khoa học",           8, 2, "khoi_10"),
    ("clb_tinhnguyen","CLB Tình nguyện",       12, 0, ""),
]

HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ",
      "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
DEM_NAM = ["Văn", "Hữu", "Đức", "Minh", "Quang", "Thành", "Anh", "Bá"]
DEM_NU  = ["Thị", "Ngọc", "Thu", "Minh", "Phương", "Hoài", "Kim", "Diệu"]
TEN_NAM = ["An", "Bình", "Cường", "Dũng", "Đạt", "Giang", "Hải", "Hùng",
           "Khoa", "Long", "Minh", "Nam", "Phúc", "Quân", "Sơn", "Tuấn",
           "Việt", "Vinh", "Bảo", "Khang"]
TEN_NU  = ["Anh", "Chi", "Dung", "Hà", "Hạnh", "Hoa", "Hương", "Lan",
           "Linh", "Mai", "Nga", "Ngân", "Nhung", "Oanh", "Phương",
           "Quỳnh", "Thảo", "Trang", "Vân", "Yến"]


def sinh_ten(rng):
    nu = rng.random() < 0.5
    return "%s %s %s" % (
        rng.choice(HO),
        rng.choice(DEM_NU if nu else DEM_NAM),
        rng.choice(TEN_NU if nu else TEN_NAM),
    )


def ghi_sheet(ws, header, rows, to_mau=None):
    ws.append(header)
    for r in rows:
        ws.append(r)
    for i, ten_cot in enumerate(header, start=1):
        o = ws.cell(row=1, column=i)
        o.font = Font(bold=True)
        o.fill = to_mau or XANH
        o.alignment = Alignment(vertical="center")
        rong = max([len(str(ten_cot))] +
                   [len(str(r[i - 1])) for r in rows if i - 1 < len(r)])
        ws.column_dimensions[get_column_letter(i)].width = min(max(rong + 3, 12), 34)
    ws.freeze_panes = "A2"


def them_sheet_ghi_chu(wb, dong):
    hd = wb.create_sheet("Ghi chú")
    hd.column_dimensions["A"].width = 82
    hd.append(["DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI HỌC SINH CÓ THẬT"])
    hd["A1"].font = Font(bold=True, size=13, color="A63A2B")
    hd.append([""])
    for d in dong:
        hd.append([d])
    hd.append([""])
    hd.append(["Sinh bằng du_lieu_test/tao_du_lieu_test.py, seed = %d" % SEED])
    hd.append(["Chạy lại script luôn cho ra đúng bộ dữ liệu này."])


def luu(wb, ten):
    p = os.path.join(THU_MUC, ten)
    wb.save(p)
    print("  da tao %-42s" % ten)
    return p


# =============================================================== #
# BỘ SẠCH
# =============================================================== #
def bo_sach():
    rng = random.Random(SEED)
    ma_clb = [c[0] for c in CLB]

    hoc_sinh = []
    for i in range(1, 121):
        ma = "HS%03d" % i
        ten = sinh_ten(rng)
        # ~22% thuộc diện dự trữ, chia hai nhóm
        r = rng.random()
        nhom = "chinh_sach" if r < 0.13 else ("khoi_10" if r < 0.22 else "")
        hoc_sinh.append((ma, ten, nhom))

    # --- 1. Danh sách CLB ---
    wb = Workbook(); ws = wb.active; ws.title = "Danh sách CLB"
    ghi_sheet(ws,
              ["club_id", "name", "capacity", "reserve_capacity", "reserve_group"],
              [list(c) for c in CLB])
    them_sheet_ghi_chu(wb, [
        "10 câu lạc bộ, tổng 130 suất cho 120 học sinh.",
        "",
        "Ba CLB có suất dự trữ: Tiếng Anh và Tin học dành cho nhóm",
        "chinh_sach; Mỹ thuật và Khoa học dành cho nhóm khoi_10.",
        "",
        "NHẬP FILE NÀY TRƯỚC hai file học sinh — nếu không, mọi học sinh",
        "sẽ bị bỏ qua vì mã CLB chưa tồn tại.",
    ])
    luu(wb, "TEST_01_danh_sach_CLB.xlsx")

    # --- 2. Chọn CLB muốn thi + 3. Nguyện vọng ---
    dong_thi, dong_nv = [], []
    so_cot_thi = 4
    so_cot_nv = 5
    for ma, ten, nhom in hoc_sinh:
        # Mỗi em đăng ký thi 2-4 CLB
        thi = rng.sample(ma_clb, rng.randint(2, so_cot_thi))
        dong_thi.append([ma, ten, nhom] + thi + [""] * (so_cot_thi - len(thi)))

        # Nguyện vọng: chủ yếu nằm trong số đã thi (hợp lý), thỉnh
        # thoảng thêm một CLB chưa thi — vẫn hợp lệ, vì học sinh không
        # thi vẫn được xét vào CLB đó (Tier 2).
        nv = thi[:]
        rng.shuffle(nv)
        if rng.random() < 0.25:
            con_lai = [c for c in ma_clb if c not in nv]
            if con_lai:
                nv.append(rng.choice(con_lai))
        nv = nv[:so_cot_nv]
        dong_nv.append([ma, ten, nhom] + nv + [""] * (so_cot_nv - len(nv)))

    wb = Workbook(); ws = wb.active; ws.title = "Chọn CLB muốn thi"
    ghi_sheet(ws,
              ["student_id", "name", "reserve_group"] +
              ["test_club_%d" % i for i in range(1, so_cot_thi + 1)],
              dong_thi)
    them_sheet_ghi_chu(wb, [
        "120 học sinh, mỗi em đăng ký thi 2-4 CLB.",
        "",
        "Cột reserve_group: khoảng 22%% số em thuộc diện dự trữ",
        "(chinh_sach hoặc khoi_10), phần còn lại để trống.",
        "",
        "Ô trống ở các cột test_club_* là bình thường — không cần điền kín.",
    ])
    luu(wb, "TEST_02_chon_CLB_muon_thi.xlsx")

    wb = Workbook(); ws = wb.active; ws.title = "Xếp hạng nguyện vọng"
    ghi_sheet(ws,
              ["student_id", "name", "reserve_group"] +
              ["pref_%d" % i for i in range(1, so_cot_nv + 1)],
              dong_nv)
    them_sheet_ghi_chu(wb, [
        "Cùng 120 học sinh, xếp 2-5 nguyện vọng theo THỨ TỰ CỘT:",
        "pref_1 là nguyện vọng mong muốn nhất.",
        "",
        "Nguyện vọng chủ yếu nằm trong số CLB em đã đăng ký thi. Khoảng",
        "1/4 số em có thêm một nguyện vọng vào CLB chưa thi — vẫn hợp lệ,",
        "vì học sinh không thi vẫn được xét vào CLB đó.",
    ])
    luu(wb, "TEST_03_xep_hang_nguyen_vong.xlsx")
    return hoc_sinh


# =============================================================== #
# BỘ CÓ LỖI CỐ Ý
# =============================================================== #
def bo_co_loi():
    wb = Workbook(); ws = wb.active; ws.title = "Có lỗi cố ý"
    dong = [
        # (mã, tên, nhóm, nv1, nv2)  — kèm chú thích ở sheet sau
        ["HS201", "Nguyễn Văn Một",   "",            "clb_bongro",  "clb_amnhac"],
        ["HS202", "Trần Thị Hai",     "",            "clb_bongro",  ""],
        ["HS202", "Trần Thị Hai",     "",            "clb_amnhac",  ""],
        ["hs201", "Nguyễn Văn Một",   "",            "clb_vanhoc",  ""],
        ["HS204", "Lê Văn Bốn",       "chinh_sac",   "clb_tienganh",""],
        ["HS205", "Phạm Thị Năm",     "",            "clb_khong_co",""],
        ["0012345","Hoàng Văn Sáu",   "",            "clb_bongro",  ""],
        ["0012346","Vũ Thị Bảy",      "",            "clb_amnhac",  ""],
        ["0012347","Đỗ Văn Tám",      "",            "clb_vanhoc",  ""],
        ["12348",  "Bùi Thị Chín",    "",            "clb_bongro",  ""],
    ]
    ghi_sheet(ws, ["student_id", "name", "reserve_group", "pref_1", "pref_2"],
              dong, to_mau=VANG)
    them_sheet_ghi_chu(wb, [
        "File này CỐ Ý SAI, dùng để kiểm tra phần mềm có cảnh báo không.",
        "Nhập file TEST_01 (danh sách CLB) trước, rồi nhập file này.",
        "",
        "Năm lỗi đã cài sẵn, và cảnh báo tương ứng phải hiện ra:",
        "",
        "1. HS202 xuất hiện HAI DÒNG (dòng 3 và 4)",
        "   -> báo: mã HS202 xuất hiện 2 lần, chỉ dòng cuối được giữ",
        "",
        "2. hs201 chỉ khác chữ hoa/thường so với HS201",
        "   -> báo: đang coi là HAI học sinh khác nhau",
        "",
        "3. HS204 ghi nhóm dự trữ 'chinh_sac' (thiếu chữ h)",
        "   -> báo: không CLB nào nhận, gợi ý 'chinh_sach'",
        "",
        "4. HS205 xếp nguyện vọng vào 'clb_khong_co'",
        "   -> báo: club không tồn tại, BỎ QUA cả học sinh này",
        "",
        "5. Mã 12348 chỉ dài 5 chữ số trong khi các mã khác dài 7",
        "   -> báo: nghi Excel đã cắt mất số 0 ở đầu",
        "",
        "Nếu thiếu bất kỳ cảnh báo nào trong 5 cảnh báo trên, đó là lỗi",
        "của phần mềm — hãy báo lại.",
    ])
    luu(wb, "TEST_04_CO_LOI_CO_Y.xlsx")


if __name__ == "__main__":
    print("Sinh du lieu MO PHONG (seed=%d):" % SEED)
    hs = bo_sach()
    bo_co_loi()
    print("Xong: %d hoc sinh, %d CLB" % (len(hs), len(CLB)))
