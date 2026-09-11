# -*- coding: utf-8 -*-
"""Test canh cho tính năng NHIỀU BUỔI SINH HOẠT trong tuần.

Mệnh đề trung tâm của cả tính năng: vì mỗi câu lạc bộ sinh hoạt đúng một
buổi, mỗi em tối đa một câu lạc bộ mỗi buổi, và không có trần số câu lạc bộ
mỗi tuần, nên **các buổi độc lập hoàn toàn**. Bài toán tuần là N bản sao độc
lập của bài toán đã giải, không phải một bài toán lớn hơn.

Tệp này canh đúng mệnh đề đó và các hệ quả của nó.

Nhóm test                  Canh mệnh đề nào
-------------------------  ---------------------------------------------
TestTrungKhit              MỘT buổi ⇒ kết quả Y HỆT phần mềm trước khi có
                           tính năng này. Đây là test QUAN TRỌNG NHẤT
TestRangBuocBuoi           ≤1 câu lạc bộ mỗi buổi · 0 cặp phá vỡ mỗi buổi
TestBaCachBocTham          ba cách cho kết quả KHÁC nhau, và cách nào cũng
                           tái lập được giữa hai tiến trình
TestDiTru                  cơ sở dữ liệu lược đồ cũ mở được, không mất gì
TestNhapDuLieu             cột `buoi`, bộ cột nguyện vọng theo buổi, và hai
                           phép soát cảnh báo
TestSoSanhKhongGhiGi       hàm xem thử không được ghi vào cơ sở dữ liệu
TestChayDayDu              đường chạy đầy đủ qua API, xuất thời khoá biểu

ĐÃ THỬ LÀM HỎNG ĐỂ XEM TEST CÓ BẮT ĐƯỢC KHÔNG
---------------------------------------------
| Phá cái gì | Kết quả |
|---|---|
| Bỏ lọc theo buổi trong `cat_du_lieu_theo_buoi` | **2 test đỏ** ở `TestRangBuocBuoi` |
| Cài `stb_ngay` thành `stb_tuan` (bỏ nhánh hoán vị) | **1 test đỏ** ở `TestBaCachBocTham` |
| Dùng `hash()` thay `zlib.crc32` trong `_seed_cua_buoi` | **1 test đỏ** — đúng test dựng riêng cho chuyện đó |

Hai chuyện học được khi làm phép thử này, cả hai đều đã sửa:

**Phép phá thứ nhất lúc đầu chỉ làm đỏ MỘT test.** Lý do: `run_rbda` vốn
đã bỏ qua nguyện vọng trỏ tới câu lạc bộ không có trong tập được truyền
vào, nên bỏ lọc đi thì chỗ xếp ai vào đâu vẫn đúng. Cái hỏng nằm chỗ khác
và im hơn nhiều: **thứ hạng nguyện vọng** bị đếm theo cả tuần thay vì
trong buổi, nên một em được đúng câu lạc bộ mình thích nhất buổi Thứ 5 lại
bị ghi là "nguyện vọng 3". Đã thêm
`test_thu_hang_nguyen_vong_tinh_TRONG_BUOI` để canh, và giờ phép phá đó
làm đỏ hai test.

**Phép phá thứ ba không hiện ra trong một lần chạy pytest.** `hash()` của
chuỗi bị ngẫu nhiên hoá theo từng tiến trình, nên mọi test trong cùng tiến
trình đều thấy cùng một giá trị và đều xanh. Chỉ phép so giữa HAI tiến
trình mới bắt được — đó là lý do test ấy phải gọi `subprocess` và ép
`PYTHONHASHSEED` khác nhau.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

import pytest

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)
sys.path.insert(0, os.path.join(GOC, "du_lieu_test"))

import rbda_priority_pipeline as loi  # noqa: E402
from api import PipelineAPI  # noqa: E402

BO_MAU = os.path.join(GOC, "du_lieu_test", "bo_nhieu_buoi")
TEP_MAU = [
    "NHIEUBUOI_01_danh_sach_CLB.csv",
    "NHIEUBUOI_02_chon_CLB_muon_thi.csv",
    "NHIEUBUOI_03_xep_hang_nguyen_vong.csv",
]


# ---------------------------------------------------------------------------
# FIXTURE
# ---------------------------------------------------------------------------

def _nap_bo_mau(api):
    for ten in TEP_MAU:
        with open(os.path.join(BO_MAU, ten), encoding="utf-8-sig") as f:
            kq = api.import_csv_auto(f.read())
        assert kq["ok"], kq


@pytest.fixture
def api_nhieu_buoi(tmp_path):
    """API đã nạp sẵn bộ dữ liệu mẫu 5 buổi."""
    api = PipelineAPI(str(tmp_path / "app.db"), thu_muc_xuat=str(tmp_path))
    _nap_bo_mau(api)
    return api


@pytest.fixture
def du_lieu_nhieu_buoi(api_nhieu_buoi):
    """(students, clubs, scores, applicants, preferences, stb, reserve_fn)."""
    api_nhieu_buoi.run_pipeline(seed=42)
    st, cl, sc, ap, pr, _ = loi.load_from_sqlite(api_nhieu_buoi.db_path)
    stb = {sid: info["stb"] for sid, info in st.items()}
    return st, cl, sc, ap, pr, stb, loi.default_reserve_eligible_fn(st, cl)


def _bo_mot_buoi(tmp_path, ten_bo):
    """Nạp một trong ba bộ dữ liệu CŨ (đều chỉ có một buổi)."""
    from do_anh_huong_seed import BO_DU_LIEU, nap_bo

    thu_muc = str(tmp_path / ten_bo)
    os.makedirs(thu_muc, exist_ok=True)
    duong = dict(
        (ten.strip().split()[0], files) for ten, files in BO_DU_LIEU
    )[ten_bo]
    db = nap_bo(thu_muc, duong)
    return loi.load_from_sqlite(db)


# ---------------------------------------------------------------------------
# 1 — TRÙNG KHÍT: MỘT BUỔI PHẢI RA ĐÚNG KẾT QUẢ CŨ
# ---------------------------------------------------------------------------

class TestTrungKhit:
    """Test quan trọng nhất của cả tệp.

    Toàn bộ `NGHIEN_CUU_TOI_UU.md` — 2 088 thể hiện vét cạn, 1 400 lượt thử
    khai gian, 392 phép thử nhiễu — đo trên dữ liệu MỘT buổi. Những con số
    đó chỉ còn nói về phần mềm đang chạy nếu đường mới cho ra đúng kết quả
    của đường cũ trên dữ liệu ấy. Nhóm test này là chỗ mệnh đề đó được canh.
    """

    @pytest.mark.parametrize("ten_bo", ["vi_du_huong_dan", "bo_sach", "TEST_0*"])
    def test_mot_buoi_cho_ket_qua_y_het_run_rbda(self, tmp_path, ten_bo):
        students, clubs, scores, app, prefs, _ = _bo_mot_buoi(tmp_path, ten_bo)
        elig = loi.default_reserve_eligible_fn(students, clubs)

        for seed in range(1, 21):
            stb = loi.generate_stb_lottery(sorted(students), seed)
            cu = loi.run_rbda(students, clubs, scores, app, prefs, stb, elig)
            moi = loi.run_rbda_nhieu_buoi(
                students, clubs, scores, app, prefs, stb, elig,
                che_do_boc_tham="stb_tuan", seed=seed,
            )
            assert moi.ds_buoi == [loi.BUOI_MAC_DINH]
            gop = {
                sid: theo_buoi[loi.BUOI_MAC_DINH]
                for sid, theo_buoi in moi.assignment.items()
            }
            assert gop == dict(cu.assignment), (
                "seed %d: duong nhieu buoi lech khoi run_rbda tren du lieu mot buoi"
                % seed
            )

    def test_mot_buoi_giu_nguyen_ca_tang_va_thu_hang(self, tmp_path):
        """Không chỉ 'vào câu lạc bộ nào' mà cả diện trúng tuyển và thứ hạng
        nguyện vọng cũng phải trùng — tệp xuất ra dùng cả ba cột đó."""
        students, clubs, scores, app, prefs, _ = _bo_mot_buoi(tmp_path, "bo_sach")
        elig = loi.default_reserve_eligible_fn(students, clubs)
        stb = loi.generate_stb_lottery(sorted(students), 42)

        cu = loi.run_rbda(students, clubs, scores, app, prefs, stb, elig)
        moi = loi.run_rbda_nhieu_buoi(
            students, clubs, scores, app, prefs, stb, elig, seed=42)
        mot = moi.per_buoi[loi.BUOI_MAC_DINH]

        assert mot.matched_tier == cu.matched_tier
        assert mot.rank_in_student_pref == cu.rank_in_student_pref
        assert mot.rounds_run == cu.rounds_run

    def test_mot_buoi_thi_ba_cach_boc_tham_cho_cung_ket_qua(self, tmp_path):
        """Một buổi thì không có gì để 'san đều qua các ngày' — ba cách phải
        trùng nhau. Khác nhau ở đây nghĩa là một cách nào đó đang tự bốc lại
        số ngoài tầm khoá bốc thăm."""
        students, clubs, scores, app, prefs, _ = _bo_mot_buoi(tmp_path, "bo_sach")
        elig = loi.default_reserve_eligible_fn(students, clubs)
        stb = loi.generate_stb_lottery(sorted(students), 42)

        kq = {
            cd: loi.run_rbda_nhieu_buoi(
                students, clubs, scores, app, prefs, stb, elig,
                che_do_boc_tham=cd, seed=42).assignment
            for cd in loi.CHE_DO_BOC_THAM
        }
        assert kq["stb_tuan"] == kq["stb_ngay"] == kq["stb_co_bu"]


# ---------------------------------------------------------------------------
# 2 — RÀNG BUỘC CỦA BÀI TOÁN NHIỀU BUỔI
# ---------------------------------------------------------------------------

class TestRangBuocBuoi:

    def test_khong_em_nao_co_hai_clb_cung_buoi(self, du_lieu_nhieu_buoi):
        st, cl, sc, ap, pr, stb, elig = du_lieu_nhieu_buoi
        kq = loi.run_rbda_nhieu_buoi(st, cl, sc, ap, pr, stb, elig, seed=42)
        cua = loi.buoi_cua_club(cl)
        for sid, theo_buoi in kq.assignment.items():
            da_dung = [cua[c] for c in theo_buoi.values() if c is not None]
            assert len(da_dung) == len(set(da_dung)), (
                "em %s bi xep hai CLB trung buoi: %r" % (sid, theo_buoi))

    def test_moi_buoi_deu_khong_co_cap_pha_vo(self, du_lieu_nhieu_buoi):
        st, cl, sc, ap, pr, stb, elig = du_lieu_nhieu_buoi
        for che_do in loi.CHE_DO_BOC_THAM:
            kq = loi.run_rbda_nhieu_buoi(
                st, cl, sc, ap, pr, stb, elig, che_do_boc_tham=che_do, seed=42)
            theo_buoi = loi.verify_stability_tuan(kq, cl, pr, elig)
            assert all(v == [] for v in theo_buoi.values()), (
                "%s: co cap pha vo %r" % (che_do, theo_buoi))

    def test_chi_xep_vao_clb_em_co_khai(self, du_lieu_nhieu_buoi):
        st, cl, sc, ap, pr, stb, elig = du_lieu_nhieu_buoi
        kq = loi.run_rbda_nhieu_buoi(st, cl, sc, ap, pr, stb, elig, seed=42)
        for sid, theo_buoi in kq.assignment.items():
            for cid in theo_buoi.values():
                if cid is not None:
                    assert cid in pr.get(sid, []), (
                        "em %s bi xep vao %s ma khong he khai" % (sid, cid))

    def test_cat_nguyen_vong_giu_nguyen_thu_tu(self):
        """Lọc theo buổi phải giữ thứ tự nguyện vọng gốc.

        Đây là chỗ cả thiết kế dựa vào: lọc một dãy đã sắp thì phần còn lại
        vẫn đúng thứ tự, nên không cần đánh số lại rank theo buổi, và dữ
        liệu nhập bằng bộ cột cũ vẫn chạy đúng.
        """
        clubs = {
            "a": {"capacity": 1, "reserve_capacity": 0, "buoi": "t3"},
            "b": {"capacity": 1, "reserve_capacity": 0, "buoi": "t5"},
            "c": {"capacity": 1, "reserve_capacity": 0, "buoi": "t3"},
            "d": {"capacity": 1, "reserve_capacity": 0, "buoi": "t5"},
        }
        prefs = {"s1": ["b", "a", "d", "c"]}
        _cl, _sc, _ap, pr_t3 = loi.cat_du_lieu_theo_buoi(
            "t3", ["a", "c"], clubs, {}, {}, prefs)
        _cl, _sc, _ap, pr_t5 = loi.cat_du_lieu_theo_buoi(
            "t5", ["b", "d"], clubs, {}, {}, prefs)
        assert pr_t3["s1"] == ["a", "c"]
        assert pr_t5["s1"] == ["b", "d"]

    def test_thu_hang_nguyen_vong_tinh_TRONG_BUOI(self):
        """Cột "Nguyện vọng thứ" phải đếm trong buổi, không đếm cả tuần.

        Em xếp Thứ 5 là nguyện vọng 1 của buổi Thứ 5 thì trên thời khoá
        biểu phải ghi "nguyện vọng 1", dù trong danh sách chung cả tuần nó
        đứng thứ ba. Ghi số toàn cục vào đó là nói với em rằng em tụt
        nguyện vọng trong khi thực ra em được đúng thứ mình muốn nhất ở
        buổi ấy — và nhà trường đọc bảng tổng kết cũng ra một bức tranh
        xấu hơn sự thật.
        """
        students = {"s1": {}}
        clubs = {
            "t3_a": {"capacity": 1, "reserve_capacity": 0, "buoi": "t3"},
            "t3_b": {"capacity": 1, "reserve_capacity": 0, "buoi": "t3"},
            "t5_a": {"capacity": 1, "reserve_capacity": 0, "buoi": "t5"},
        }
        app = {cid: ["s1"] for cid in clubs}
        # Trong danh sach chung, t5_a dung THU BA. Nhung trong buoi t5 no
        # la nguyen vong DAU TIEN.
        prefs = {"s1": ["t3_a", "t3_b", "t5_a"]}
        kq = loi.run_rbda_nhieu_buoi(
            students, clubs, {}, app, prefs, {"s1": 0},
            lambda s, c: False, seed=1)

        assert kq.assignment["s1"] == {"t3": "t3_a", "t5": "t5_a"}
        assert kq.per_buoi["t3"].rank_in_student_pref["s1"] == 1
        assert kq.per_buoi["t5"].rank_in_student_pref["s1"] == 1

    def test_clb_khong_khai_buoi_gom_vao_buoi_mac_dinh(self):
        clubs = {
            "a": {"capacity": 1, "reserve_capacity": 0, "buoi": None},
            "b": {"capacity": 1, "reserve_capacity": 0},
            "c": {"capacity": 1, "reserve_capacity": 0, "buoi": ""},
        }
        assert loi.nhom_theo_buoi(clubs) == {loi.BUOI_MAC_DINH: ["a", "b", "c"]}


# ---------------------------------------------------------------------------
# 3 — BA CÁCH BỐC THĂM
# ---------------------------------------------------------------------------

class TestBaCachBocTham:

    def test_ba_cach_cho_ket_qua_khac_nhau_khi_co_nhieu_buoi(self, du_lieu_nhieu_buoi):
        """Đối chứng ngược cho bộ chọn chế độ.

        Nếu ba cách cho kết quả giống hệt nhau trên dữ liệu NHIỀU buổi thì
        bộ chọn đang không có tác dụng gì, và bảng đối chiếu trên giao diện
        chỉ là ba bản sao của cùng một con số.
        """
        st, cl, sc, ap, pr, stb, elig = du_lieu_nhieu_buoi
        xep = {
            cd: loi.run_rbda_nhieu_buoi(
                st, cl, sc, ap, pr, stb, elig, che_do_boc_tham=cd, seed=42).assignment
            for cd in loi.CHE_DO_BOC_THAM
        }
        assert xep["stb_tuan"] != xep["stb_ngay"]
        assert xep["stb_tuan"] != xep["stb_co_bu"]

    def test_chay_lai_ra_dung_ket_qua_cu(self, du_lieu_nhieu_buoi):
        st, cl, sc, ap, pr, stb, elig = du_lieu_nhieu_buoi
        for cd in loi.CHE_DO_BOC_THAM:
            lan1 = loi.run_rbda_nhieu_buoi(
                st, cl, sc, ap, pr, stb, elig, che_do_boc_tham=cd, seed=42).assignment
            lan2 = loi.run_rbda_nhieu_buoi(
                st, cl, sc, ap, pr, stb, elig, che_do_boc_tham=cd, seed=42).assignment
            assert lan1 == lan2

    def test_seed_cua_buoi_tai_lap_duoc_giua_hai_tien_trinh(self):
        """Chặn `hash()` của Python lọt vào chỗ sinh seed.

        `hash()` của chuỗi bị ngẫu nhiên hoá theo từng tiến trình, nên lỗi
        này KHÔNG hiện ra trong một lần chạy pytest — mọi test trong cùng
        tiến trình đều thấy cùng giá trị. Phải so giữa HAI tiến trình, và
        phải ép PYTHONHASHSEED khác nhau để chắc chắn.
        """
        ma = (
            "import sys; sys.path.insert(0, %r); "
            "import rbda_priority_pipeline as loi; "
            "import json; print(json.dumps("
            "[loi._seed_cua_buoi(42, b) for b in ['thu_2','thu_3','thu_6']]))"
            % GOC
        )
        ket = []
        for hat in ("0", "1", "12345"):
            moi_truong = dict(os.environ, PYTHONHASHSEED=hat)
            ra = subprocess.run([sys.executable, "-c", ma], capture_output=True,
                                text=True, check=True, env=moi_truong)
            ket.append(json.loads(ra.stdout))
        assert ket[0] == ket[1] == ket[2], (
            "seed dan xuat doi giua cac tien trinh: %r — co phai dang dung hash()?"
            % ket
        )

    def test_stb_ngay_van_la_hoan_vi_hop_le(self, du_lieu_nhieu_buoi):
        """Mỗi buổi phải là một hoán vị đủ 0..n-1: không trùng số, không sót
        em nào. Trùng số là hai em hoà nhau ở chỗ lẽ ra phải phá hoà."""
        st, cl, sc, ap, pr, stb, elig = du_lieu_nhieu_buoi
        ds_buoi = list(loi.nhom_theo_buoi(cl))
        theo_buoi = loi.sinh_stb_theo_buoi(stb, ds_buoi, 42, "stb_ngay")
        for buoi, bo_so in theo_buoi.items():
            assert set(bo_so) == set(stb), "buoi %s thieu hoac thua hoc sinh" % buoi
            assert sorted(bo_so.values()) == list(range(len(stb)))

    def test_stb_co_bu_dua_em_trang_tay_len_truoc(self):
        """Em chưa có câu lạc bộ nào phải đứng trước em đã có, bất kể số bốc
        thăm gốc — đó là toàn bộ định nghĩa của cách bốc thăm có bù."""
        stb_goc = {"a": 0, "b": 1, "c": 2}
        moi = loi._stb_co_bu(stb_goc, {"a": 2, "b": 0, "c": 1})
        assert moi["b"] < moi["c"] < moi["a"]

    def test_che_do_la_thi_bao_loi_ngay(self, du_lieu_nhieu_buoi):
        st, cl, sc, ap, pr, stb, elig = du_lieu_nhieu_buoi
        with pytest.raises(ValueError):
            loi.run_rbda_nhieu_buoi(
                st, cl, sc, ap, pr, stb, elig, che_do_boc_tham="khong_co_that")


# ---------------------------------------------------------------------------
# 4 — DI TRÚ CƠ SỞ DỮ LIỆU CŨ
# ---------------------------------------------------------------------------

LUOC_DO_CU = """
CREATE TABLE students (student_id TEXT PRIMARY KEY, name TEXT,
                       stb_number INTEGER, reserve_group TEXT);
CREATE TABLE clubs (club_id TEXT PRIMARY KEY, name TEXT, capacity INTEGER NOT NULL,
                    reserve_capacity INTEGER NOT NULL DEFAULT 0, reserve_group TEXT);
CREATE TABLE match_results (student_id TEXT PRIMARY KEY, club_id TEXT,
                            round_num INTEGER, matched_tier TEXT,
                            rank_in_student_pref INTEGER);
CREATE TABLE run_meta (id INTEGER PRIMARY KEY CHECK (id = 1), seed INTEGER,
                       run_at TEXT, rounds_run INTEGER, n_matched INTEGER,
                       n_total INTEGER);
CREATE TABLE run_history (run_id INTEGER PRIMARY KEY AUTOINCREMENT, seed INTEGER,
                          run_at TEXT, rounds_run INTEGER, n_matched INTEGER,
                          n_total INTEGER, stb_redrawn INTEGER NOT NULL DEFAULT 0);
CREATE TABLE stb_lock (id INTEGER PRIMARY KEY CHECK (id = 1),
                       is_locked INTEGER NOT NULL DEFAULT 0,
                       locked_at TEXT, unlocked_at TEXT);
CREATE TABLE club_test_selection (student_id TEXT NOT NULL, club_id TEXT NOT NULL,
                                  PRIMARY KEY (student_id, club_id));
CREATE TABLE club_scores (student_id TEXT NOT NULL, club_id TEXT NOT NULL,
                          score REAL NOT NULL, PRIMARY KEY (student_id, club_id));
CREATE TABLE preferences (student_id TEXT NOT NULL, club_id TEXT NOT NULL,
                          rank INTEGER NOT NULL, PRIMARY KEY (student_id, club_id));
"""


@pytest.fixture
def db_luoc_do_cu(tmp_path):
    """Một app.db dựng đúng theo lược đồ TRƯỚC khi có tính năng nhiều buổi."""
    duong = str(tmp_path / "cu.db")
    conn = sqlite3.connect(duong)
    conn.executescript(LUOC_DO_CU)
    conn.execute("INSERT INTO stb_lock VALUES (1, 1, '2025-01-01', NULL)")
    conn.execute("INSERT INTO clubs VALUES ('clb_a', 'CLB A', 5, 1, 'khoi_10')")
    conn.execute("INSERT INTO students VALUES ('HS1', 'An', 0, NULL)")
    conn.execute("INSERT INTO students VALUES ('HS2', 'Binh', 1, 'khoi_10')")
    conn.execute("INSERT INTO match_results VALUES ('HS1', 'clb_a', 3, 'general', 1)")
    conn.execute("INSERT INTO match_results VALUES ('HS2', NULL, 3, NULL, NULL)")
    conn.executemany(
        "INSERT INTO run_history (seed, run_at, rounds_run, n_matched, n_total, stb_redrawn) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(42, "2025-01-01", 3, 1, 2, 1), (43, "2025-01-02", 3, 1, 2, 0)],
    )
    conn.commit()
    conn.close()
    return duong


class TestDiTru:

    def test_di_tru_giu_nguyen_ket_qua_cu(self, db_luoc_do_cu):
        da_lam = loi.di_tru_schema(db_luoc_do_cu)
        assert "match_results.buoi" in da_lam
        assert "clubs.buoi" in da_lam

        conn = sqlite3.connect(db_luoc_do_cu)
        rows = conn.execute(
            "SELECT student_id, buoi, club_id, matched_tier, rank_in_student_pref "
            "FROM match_results ORDER BY student_id"
        ).fetchall()
        conn.close()
        assert rows == [
            ("HS1", loi.BUOI_MAC_DINH, "clb_a", "general", 1),
            ("HS2", loi.BUOI_MAC_DINH, None, None, None),
        ]

    def test_di_tru_KHONG_DUNG_toi_nhat_ky_chay(self, db_luoc_do_cu):
        """`run_history` là dấu vết kiểm toán — đến chức năng xoá dữ liệu
        cũng không đụng tới nó. Di trú lại càng không."""
        conn = sqlite3.connect(db_luoc_do_cu)
        truoc = conn.execute(
            "SELECT run_id, seed, run_at, stb_redrawn FROM run_history ORDER BY run_id"
        ).fetchall()
        conn.close()

        loi.di_tru_schema(db_luoc_do_cu)

        conn = sqlite3.connect(db_luoc_do_cu)
        sau = conn.execute(
            "SELECT run_id, seed, run_at, stb_redrawn FROM run_history ORDER BY run_id"
        ).fetchall()
        conn.close()
        assert sau == truoc

    def test_di_tru_chay_lai_khong_lam_gi_them(self, db_luoc_do_cu):
        loi.di_tru_schema(db_luoc_do_cu)
        assert loi.di_tru_schema(db_luoc_do_cu) == []

    def test_csdl_cu_dung_duoc_ngay_sau_khi_di_tru(self, db_luoc_do_cu):
        """Không chỉ mở được mà phải CHẠY được — di trú xong là dùng tiếp."""
        api = PipelineAPI(db_luoc_do_cu)
        assert api.get_match_results()["ok"]
        assert api.get_thoi_khoa_bieu()["ok"]
        assert api.list_clubs_admin()["ok"]
        assert api.get_tai_theo_buoi()["ok"]


# ---------------------------------------------------------------------------
# 5 — NHẬP DỮ LIỆU CÓ BUỔI
# ---------------------------------------------------------------------------

class TestNhapDuLieu:

    def test_nhap_clb_co_cot_buoi(self, tmp_path):
        api = PipelineAPI(str(tmp_path / "app.db"))
        kq = api.import_clubs_csv(
            "club_id,name,capacity,buoi\nclb_a,CLB A,5,thu_3\nclb_b,CLB B,5,thu_5\n")
        assert kq["ok"] and kq["data"]["n_clubs_co_buoi"] == 2
        assert api.get_danh_sach_buoi()["data"]["ds_buoi"] == ["thu_3", "thu_5"]
        assert api.get_danh_sach_buoi()["data"]["nhieu_buoi"] is True

    def test_khong_khai_buoi_thi_KHONG_coi_la_nhieu_buoi(self, tmp_path):
        """Trường chưa dùng buổi thì giao diện phải trông y hệt bản cũ."""
        api = PipelineAPI(str(tmp_path / "app.db"))
        api.import_clubs_csv("club_id,name,capacity\nclb_a,CLB A,5\nclb_b,CLB B,5\n")
        assert api.get_danh_sach_buoi()["data"]["nhieu_buoi"] is False

    def test_tron_co_buoi_va_khong_buoi_thi_canh_bao(self, tmp_path):
        """Tình huống nguy hiểm nhất của bước nhập này: những CLB bỏ trống
        buổi bị gom hết vào một buổi, tức là bị coi là TRÙNG GIỜ với nhau,
        mà không có gì trên màn hình nói ra."""
        api = PipelineAPI(str(tmp_path / "app.db"))
        kq = api.import_clubs_csv(
            "club_id,name,capacity,buoi\nclb_a,CLB A,5,thu_3\nclb_b,CLB B,5,\n")
        ma = [w["code"] for w in kq["data"]["warnings"]]
        assert "clb_thieu_buoi" in ma

    def test_nhap_nguyen_vong_theo_tung_buoi(self, tmp_path):
        api = PipelineAPI(str(tmp_path / "app.db"))
        api.import_clubs_csv(
            "club_id,name,capacity,buoi\n"
            "clb_a,CLB A,5,thu_3\nclb_c,CLB C,5,thu_3\nclb_b,CLB B,5,thu_5\n")
        kq = api.import_preferences_csv(
            "student_id,name,thu_3_pref_1,thu_3_pref_2,thu_5_pref_1\n"
            "HS1,An,clb_a,clb_c,clb_b\n")
        assert kq["ok"] and kq["data"]["n_nguyen_vong_lech_buoi"] == 0

        _st, _cl, _sc, _ap, pr, _ = loi.load_from_sqlite(api.db_path)
        assert pr["HS1"] == ["clb_a", "clb_c", "clb_b"]

    def test_nguyen_vong_lech_buoi_bi_bao_va_bi_bo(self, tmp_path):
        """Ghi câu lạc bộ Thứ 5 vào cột Thứ 3 là lỗi gõ tay dễ xảy ra nhất.
        Im lặng nhận vào thì kết quả sai mà không ai biết vì sao."""
        api = PipelineAPI(str(tmp_path / "app.db"))
        api.import_clubs_csv(
            "club_id,name,capacity,buoi\nclb_a,CLB A,5,thu_3\nclb_b,CLB B,5,thu_5\n")
        kq = api.import_preferences_csv(
            "student_id,name,thu_3_pref_1,thu_5_pref_1\nHS1,An,clb_b,clb_a\n")
        assert kq["data"]["n_nguyen_vong_lech_buoi"] == 2
        ma = [w["code"] for w in kq["data"]["warnings"]]
        assert ma[0] == "nguyen_vong_lech_buoi"

        _st, _cl, _sc, _ap, pr, _ = loi.load_from_sqlite(api.db_path)
        assert pr.get("HS1", []) == []

    def test_tu_nhan_dien_duoc_bo_cot_theo_buoi(self, tmp_path):
        api = PipelineAPI(str(tmp_path / "app.db"))
        d = api.detect_csv_kind("student_id,thu_3_pref_1,thu_5_pref_1\nHS1,a,b\n")["data"]
        assert d["kind"] == "preferences" and d["confident"] is True

    def test_bo_cot_cu_van_nhan_dien_dung(self, tmp_path):
        """`pref_1` không được lẫn sang nhánh theo buổi."""
        api = PipelineAPI(str(tmp_path / "app.db"))
        d = api.detect_csv_kind("student_id,pref_1,pref_2\nHS1,a,b\n")["data"]
        assert (d["kind"], d["format"]) == ("preferences", "wide")

    def test_chuan_hoa_buoi_gom_cac_cach_viet_ve_mot(self, tmp_path):
        """"Thứ 3" và "thu 3" và "thu_3" phải ra cùng một buổi — không thì
        hai câu lạc bộ cùng giờ bị coi là hai buổi và học sinh trúng cả hai."""
        api = PipelineAPI(str(tmp_path / "app.db"))
        assert api.chuan_hoa_buoi("  Thu 3 ") == api.chuan_hoa_buoi("thu_3")
        assert api.chuan_hoa_buoi("") == ""


# ---------------------------------------------------------------------------
# 6 — XEM THỬ KHÔNG ĐƯỢC GHI GÌ
# ---------------------------------------------------------------------------

def _chup_csdl(duong):
    conn = sqlite3.connect(duong)
    try:
        return (
            conn.execute("SELECT COUNT(*) FROM match_results").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM run_history").fetchone()[0],
            conn.execute("SELECT is_locked, locked_at FROM stb_lock WHERE id=1").fetchone(),
            conn.execute(
                "SELECT student_id, stb_number FROM students ORDER BY student_id"
            ).fetchall(),
        )
    finally:
        conn.close()


class TestSoSanhKhongGhiGi:
    """`so_sanh_boc_tham` là nút "xem thử". Lỡ ghi xuống cơ sở dữ liệu thì
    nó vừa đổi kết quả đã công bố, vừa để lại một dòng nhật ký trông y hệt
    một lần chạy thật — hỏng cả kết quả lẫn dấu vết kiểm toán."""

    def test_khong_doi_gi_trong_csdl(self, api_nhieu_buoi):
        api_nhieu_buoi.run_pipeline(seed=42)
        truoc = _chup_csdl(api_nhieu_buoi.db_path)
        kq = api_nhieu_buoi.so_sanh_boc_tham(seed=7)
        assert kq["ok"], kq
        assert _chup_csdl(api_nhieu_buoi.db_path) == truoc

    def test_chay_duoc_ngay_ca_khi_chua_bao_gio_chay_phan_bo(self, api_nhieu_buoi):
        """Xem thử TRƯỚC khi chạy thật mới là lúc nó có ích nhất — mà lúc đó
        số bốc thăm còn chưa được vẽ."""
        truoc = _chup_csdl(api_nhieu_buoi.db_path)
        kq = api_nhieu_buoi.so_sanh_boc_tham(seed=42)
        assert kq["ok"], kq
        assert len(kq["data"]["bang"]) == len(loi.CHE_DO_BOC_THAM)
        assert _chup_csdl(api_nhieu_buoi.db_path) == truoc

    def test_bang_co_du_ba_cach_va_cot_khac_moc(self, api_nhieu_buoi):
        api_nhieu_buoi.run_pipeline(seed=42)
        d = api_nhieu_buoi.so_sanh_boc_tham(seed=42)["data"]
        assert [b["che_do"] for b in d["bang"]] == list(loi.CHE_DO_BOC_THAM)
        assert d["bang"][0]["so_o_khac_moc"] == 0          # chính nó là mốc
        # Ít nhất một cách khác phải lệch khỏi mốc, nếu không thì bảng đối
        # chiếu không đối chiếu được gì.
        assert any(b["so_o_khac_moc"] > 0 for b in d["bang"][1:])
        assert all(b["cap_pha_vo"] == 0 for b in d["bang"])


# ---------------------------------------------------------------------------
# 7 — ĐƯỜNG CHẠY ĐẦY ĐỦ QUA API
# ---------------------------------------------------------------------------

class TestChayDayDu:

    def test_chay_va_xuat_thoi_khoa_bieu(self, api_nhieu_buoi, tmp_path):
        kq = api_nhieu_buoi.run_pipeline(seed=42)
        assert kq["ok"], kq["errors"]

        tkb = api_nhieu_buoi.get_thoi_khoa_bieu()["data"]
        assert len(tkb["ds_buoi"]) == 5
        assert tkb["hoc_sinh"], "thoi khoa bieu rong"
        for em in tkb["hoc_sinh"]:
            assert set(em["theo_buoi"]) == set(tkb["ds_buoi"])

        xuat = api_nhieu_buoi.export_csv()["data"]
        assert xuat["nhieu_buoi"] is True
        assert os.path.exists(xuat["thoi_khoa_bieu_path"])
        assert os.path.isdir(os.path.splitext(xuat["path"])[0] + "_theo_buoi")

    def test_ghi_lai_cach_boc_tham_da_dung(self, api_nhieu_buoi):
        """Không ghi lại thì sau này không truy được kết quả cũ chạy bằng
        cách nào — mà ba cách cho kết quả khác nhau."""
        api_nhieu_buoi.run_pipeline(seed=42, che_do_boc_tham="stb_ngay")
        conn = sqlite3.connect(api_nhieu_buoi.db_path)
        try:
            assert conn.execute(
                "SELECT che_do_boc_tham, so_buoi FROM run_meta WHERE id=1"
            ).fetchone() == ("stb_ngay", 5)
            assert conn.execute(
                "SELECT che_do_boc_tham FROM run_history ORDER BY run_id DESC LIMIT 1"
            ).fetchone()[0] == "stb_ngay"
        finally:
            conn.close()

    def test_do_phu_dem_dung_em_trang_tay(self, api_nhieu_buoi):
        api_nhieu_buoi.run_pipeline(seed=42)
        d = api_nhieu_buoi.get_do_phu()["data"]
        assert d["so_em_trang_tay"] == d["phan_bo"][0]["so_em"]
        assert sum(p["so_em"] for p in d["phan_bo"]) == d["tong_hoc_sinh"]
        assert len(d["phan_bo"]) == len(d["ds_buoi"]) + 1

    def test_tai_theo_buoi_tinh_choi_theo_SO_HOC_SINH(self, api_nhieu_buoi):
        """Mỗi em chỉ lấy được một chỗ trong một buổi, nên mẫu số của tỉ lệ
        chọi phải là số học sinh, không phải số lượt nguyện vọng."""
        for t in api_nhieu_buoi.get_tai_theo_buoi()["data"]:
            if t["tong_cho"]:
                assert t["ti_le_choi"] == round(t["so_hoc_sinh"] / t["tong_cho"], 2)

    def test_che_do_la_bi_tu_choi(self, api_nhieu_buoi):
        kq = api_nhieu_buoi.run_pipeline(seed=42, che_do_boc_tham="lung_tung")
        assert not kq["ok"]
        assert kq["errors"][0]["code"] == "che_do_boc_tham_khong_hop_le"
