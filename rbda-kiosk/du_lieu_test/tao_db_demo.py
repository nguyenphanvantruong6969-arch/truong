"""Dựng sẵn một cơ sở dữ liệu ĐÃ NẠP VÀ ĐÃ CHẤM ĐIỂM để demo.

    ./.venv/bin/python du_lieu_test/tao_db_demo.py

⚠️  DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI HỌC SINH CÓ THẬT.

VÌ SAO CẦN TỆP NÀY
Bộ dữ liệu 120 học sinh cần **356 ô điểm**. Gõ tay hết chỗ đó mất khoảng
18 phút — dài hơn toàn bộ thời gian demo trước giám khảo. Tệp này dựng
sẵn tới ngay trước bước cuối, để hôm demo chỉ còn bấm "Chạy phân bổ".

CỐ Ý DỪNG TRƯỚC KHI CHẠY PHÂN BỔ. Phần đáng xem nhất là lúc thuật toán
chạy và kết quả hiện ra — nếu dựng sẵn cả phần đó thì không còn gì để xem.
"""

import base64
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import PipelineAPI

THU_MUC = os.path.dirname(os.path.abspath(__file__))
DICH = os.path.join(THU_MUC, "app_DEMO_da_cham_diem.db")
SEED_DIEM = 2026

TEP = [
    "TEST_01_danh_sach_CLB.xlsx",
    "TEST_02_chon_CLB_muon_thi.xlsx",
    "TEST_03_xep_hang_nguyen_vong.xlsx",
]


def doc_xlsx(api, ten):
    with open(os.path.join(THU_MUC, ten), "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = api.xlsx_to_csv_text(b64)
    if not r["ok"]:
        raise SystemExit("khong doc duoc %s: %r" % (ten, r["errors"]))
    d = r["data"]
    return d["csv_text"] if isinstance(d, dict) else d


def main():
    if os.path.exists(DICH):
        os.remove(DICH)
    api = PipelineAPI(DICH)

    for ten in TEP:
        r = api.import_csv_auto(doc_xlsx(api, ten))
        if not r["ok"]:
            raise SystemExit("nhap that bai %s: %r" % (ten, r["errors"]))
        print("  nap  %-38s ok" % ten)

    # Diem mo phong, co seed nen lan nao dung lai cung ra dung bo do.
    rng = random.Random(SEED_DIEM)
    tong = 0
    for c in api.get_scoring_overview()["data"]:
        ds = api.get_club_applicants_for_scoring(c["club_id"])["data"]["applicants"]
        if not ds:
            continue
        r = api.submit_club_scores(c["club_id"], [
            {"student_id": u["student_id"], "score": round(rng.uniform(4.0, 10.0), 1)}
            for u in ds
        ])
        if not r["ok"]:
            raise SystemExit("cham diem that bai %s: %r" % (c["club_id"], r["errors"]))
        tong += r["data"]["n_saved"]
        print("  cham %-16s %3d em" % (c["club_id"], r["data"]["n_saved"]))

    hr = api.get_data_health_report()["data"]
    print("\nCanh bao du lieu con lai: %d (nghiem trong: %d)"
          % (hr["n_warnings"], hr["n_high"]))
    for w in hr["warnings"]:
        print("   %s" % w["code"])

    print("\nDa dung: %s" % DICH)
    print("Tong %d o diem. CHUA chay phan bo — de danh cho luc demo." % tong)


if __name__ == "__main__":
    main()
