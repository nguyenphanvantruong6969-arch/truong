"""
rbda_priority_pipeline.py
==========================
Module thuật toán cho hệ thống phân bổ Câu lạc bộ dùng
Reserve-Based Deferred Acceptance (RB-DA) với dự trữ mềm
(soft reserves, precedence ordering — Kominers & Sonmez 2016)
và Single Tie-Breaking (STB).

Module này giờ ĐÃ có I/O SQLite đầy đủ (init_db, load_from_sqlite,
write_match_results_to_sqlite) dựa trên DEFAULT_SCHEMA — ĐÃ ĐƯỢC
CHỐT LÀM SCHEMA CHÍNH THỨC (không có 02_schema.sql riêng biệt nào
khác — DEFAULT_SCHEMA trong file này LÀ nguồn sự thật duy nhất).

Định dạng dữ liệu trong bộ nhớ (khớp quy ước 03_reference_rbda.py
và output của 06_ms_forms_transform.py):

    students: dict[str, dict]
        { student_id: {"stb": int} }

    clubs: dict[str, dict]
        { club_id: {"capacity": int, "reserve_capacity": int} }

    tested_scores: dict[str, dict[str, float]]
        { club_id: { student_id: score } }
        -> chỉ chứa học sinh ĐÃ được chấm (Tier 1) cho club đó.
           Học sinh không xuất hiện ở đây nhưng có trong
           `applicants[club_id]` => thuộc Tier 2.

    applicants: dict[str, list[str]]
        { club_id: [student_id, ...] }
        -> toàn bộ học sinh đã tick chọn thi/xét club này
           (từ bước UI tick-box, tách biệt khỏi bước xếp hạng).

    preferences: dict[str, list[str]]
        { student_id: [club_id_rank1, club_id_rank2, ...] }
        -> danh sách nguyện vọng đã xếp hạng của học sinh
           (tối đa 10 club theo giới hạn Microsoft Forms Ranking).
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# BƯỚC A — HÀM ƯU TIÊN HAI TẦNG (compute_club_priority)
# ---------------------------------------------------------------------------

def compute_club_priority(
    club_id: str,
    applicants_for_club: list[str],
    tested_scores_for_club: dict[str, float],
    stb_lottery: dict[str, int],
) -> list[str]:
    """
    Tính thứ tự ưu tiên hai tầng cho MỘT club.

    Tầng 1 (đã được chấm điểm — tested):
        sắp giảm dần theo điểm; bằng điểm -> STB tăng dần.
    Tầng 2 (chưa được chấm — untested):
        sắp hoàn toàn theo STB tăng dần.
    Tầng 1 LUÔN đứng trước Tầng 2 toàn bộ (không xen kẽ).

    RÀNG BUỘC BẮT BUỘC (chống nội sinh / endogeneity):
        Hàm này KHÔNG được nhận bất kỳ tham số nào liên quan đến
        thứ hạng nguyện vọng (preference rank) của học sinh.
        Nếu sau này cần mở rộng, TUYỆT ĐỐI không truyền `preferences`
        vào hàm này dưới bất kỳ hình thức nào.

        `tested_scores_for_club` phải đến từ quy trình chấm mù
        (giám khảo không thấy STB / thứ hạng nguyện vọng khi chấm).
        Việc đảm bảo "mù" là ràng buộc ở tầng UI/quy trình nhập liệu,
        hàm này không (và không thể) tự kiểm tra được điều đó.

    Args:
        club_id: id của club (chỉ dùng để thông báo lỗi, không ảnh
            hưởng logic).
        applicants_for_club: toàn bộ student_id đã tick chọn club này.
        tested_scores_for_club: {student_id: score} — tập con của
            applicants_for_club đã được chấm điểm.
        stb_lottery: {student_id: số bốc thăm} toàn hệ thống (một số
            duy nhất/học sinh, dùng chung mọi club — Single
            Tie-Breaking).

    Returns:
        list[str]: student_id đã sắp theo thứ tự ưu tiên giảm dần
        (đầu danh sách = ưu tiên cao nhất).

    Raises:
        ValueError: nếu có applicant thiếu STB (dữ liệu không toàn vẹn).
    """
    missing_stb = [
        sid for sid in applicants_for_club if sid not in stb_lottery
    ]
    if missing_stb:
        raise ValueError(
            f"[{club_id}] Có {len(missing_stb)} học sinh thiếu số bốc "
            f"thăm STB: {missing_stb[:5]}{'...' if len(missing_stb) > 5 else ''}"
        )

    tier1 = [sid for sid in applicants_for_club if sid in tested_scores_for_club]
    tier2 = [sid for sid in applicants_for_club if sid not in tested_scores_for_club]

    tier1_sorted = sorted(
        tier1,
        key=lambda sid: (-tested_scores_for_club[sid], stb_lottery[sid]),
    )
    tier2_sorted = sorted(tier2, key=lambda sid: stb_lottery[sid])

    return tier1_sorted + tier2_sorted


# ---------------------------------------------------------------------------
# BƯỚC B — XỬ LÝ DỰ TRỮ MỀM (soft reserve, precedence ordering)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# BƯỚC B — HÀM LỰA CHỌN CỦA CLUB (choice function), TÍNH LẠI MỖI VÒNG
# ---------------------------------------------------------------------------
#
# LƯU Ý QUAN TRỌNG (bài học từ đối chiếu với 03_reference_rbda.py):
# Bản đầu tiên của em dùng build_processed_priority() để gộp reserve+general
# thành MỘT thứ tự ưu tiên tổng thể, tính MỘT LẦN cho toàn bộ applicant.
# ĐÂY LÀ LỖI: nếu học sinh eligible có ưu tiên cao nhất TOÀN CỤC lại
# KHÔNG xuất hiện trong pool thực tế của một vòng cụ thể (vd đã được giữ
# ở club khác), thứ tự tĩnh đó tính sai — nó để một học sinh KHÔNG eligible
# chen vào suất lẽ ra phải thuộc về học sinh eligible xếp hạng thấp hơn
# nhưng đang có mặt. Đã verify bằng test case cụ thể (xem
# compare_with_reference.py) và bằng cách đối chiếu trực tiếp với
# 03_reference_rbda.py — bản reference tính LẠI reserve pass + general pass
# từ ĐÚNG pool đang có mặt ở MỖI vòng, không dùng thứ tự tĩnh.
#
# club_choice_function() dưới đây thay thế build_processed_priority(),
# đúng theo logic reference: reserve pass trước (chỉ trong nội bộ pool
# hiện tại), general pass sau (phần dư reserve tự động chuyển sang).

def club_choice_function(
    pool: list[str],
    capacity: int,
    reserve_capacity: int,
    is_reserve_eligible_fn: Callable[[str], bool],
    rank: dict[str, int],
) -> tuple[list[str], dict[str, str]]:
    """
    Áp dụng hàm lựa chọn của MỘT club cho MỘT pool ứng viên cụ thể
    (đây chính là "reserve pass rồi general pass" — Kominers & Sonmez
    2016 — nhưng tính LẠI MỖI LẦN gọi, không dùng thứ tự tĩnh).

    Args:
        pool: danh sách student_id đang cạnh tranh vào club này NGAY
            LÚC NÀY (có thể là 1 vòng DA, hoặc dùng để kiểm chứng
            stability với pool = held ∪ {ứng viên nghi ngờ}).
        capacity: tổng sức chứa.
        reserve_capacity: số suất dự trữ (soft — không khoá cứng).
        is_reserve_eligible_fn: (student_id) -> bool, ĐÃ áp dụng sẵn
            club_id cụ thể (dùng closure/lambda khi gọi).
        rank: {student_id: int} thứ hạng ưu tiên NỀN (từ
            compute_club_priority) — số nhỏ hơn = ưu tiên cao hơn.
            Đây là thứ tự HỢP LỆ để dùng làm khoá sắp xếp cho BẤT KỲ
            tập con nào của applicant (vì compute_club_priority không
            phụ thuộc pool, chỉ phụ thuộc điểm/STB — sắp xếp con của
            một dãy đã sắp xếp vẫn đúng thứ tự). Cái DUY NHẤT phải
            tính lại mỗi vòng là VIỆC PHÂN NHÓM reserve/general, không
            phải bản thân thứ hạng ưu tiên.

    Returns:
        (accepted: list[str], tier_of: dict[str, "reserve"|"general"])
    """
    reserve_candidates = sorted(
        (s for s in pool if is_reserve_eligible_fn(s)),
        key=lambda s: rank.get(s, len(rank)),
    )
    reserve_held = reserve_candidates[:reserve_capacity]
    reserve_held_set = set(reserve_held)

    general_capacity = capacity - len(reserve_held)
    general_candidates = sorted(
        (s for s in pool if s not in reserve_held_set),
        key=lambda s: rank.get(s, len(rank)),
    )
    general_held = general_candidates[:general_capacity]

    tier_of = {s: "reserve" for s in reserve_held}
    tier_of.update({s: "general" for s in general_held})
    return reserve_held + general_held, tier_of


# ---------------------------------------------------------------------------
# BƯỚC C — VÒNG LẶP DEFERRED ACCEPTANCE (student-proposing)
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    assignment: dict[str, Optional[str]]  # student_id -> club_id | None
    rounds_run: int
    rejection_log: list[tuple[int, str, str]] = field(default_factory=list)
    # (round_number, student_id, club_id_rejected_from)
    base_rank: dict[str, dict[str, int]] = field(default_factory=dict)
    # club_id -> {student_id: rank} — thứ hạng ưu tiên NỀN (không phải
    # thứ tự đã xử lý dự trữ tĩnh — dùng cùng club_choice_function()
    # để kiểm tra stability đúng với hàm lựa chọn động).
    matched_tier: dict[str, str] = field(default_factory=dict)
    # student_id -> "reserve" | "general", chỉ có với học sinh đã match.
    rank_in_student_pref: dict[str, int] = field(default_factory=dict)
    # student_id -> thứ hạng nguyện vọng (1-indexed) đã được xếp.


def run_rbda(
    students: dict[str, dict],
    clubs: dict[str, dict],
    tested_scores: dict[str, dict[str, float]],
    applicants: dict[str, list[str]],
    preferences: dict[str, list[str]],
    stb_lottery: dict[str, int],
    is_reserve_eligible_fn: Callable[[str, str], bool],
    max_rounds: int = 1000,
) -> MatchResult:
    """
    Chạy thuật toán RB-DA đầy đủ (student-proposing deferred
    acceptance), reserve pass + general pass TÍNH LẠI mỗi vòng cho
    mỗi club (club_choice_function) — đã đối chiếu khớp 100% với
    03_reference_rbda.py trên nhiều bộ dữ liệu (xem compare_with_reference.py).

    Args:
        students: xem docstring đầu file.
        clubs: {club_id: {"capacity": int, "reserve_capacity": int}}
        tested_scores, applicants, preferences, stb_lottery: xem đầu file.
        is_reserve_eligible_fn: (student_id, club_id) -> bool.
        max_rounds: chặn vòng lặp vô hạn nếu có lỗi dữ liệu.

    Returns:
        MatchResult
    """
    held: dict[str, list[str]] = {cid: [] for cid in clubs}
    held_tier: dict[str, dict[str, str]] = {cid: {} for cid in clubs}
    next_choice_idx: dict[str, int] = {sid: 0 for sid in students}
    rejection_log: list[tuple[int, str, str]] = []

    # base_rank chỉ phụ thuộc điểm/STB, KHÔNG phụ thuộc pool -> tính
    # một lần là đúng (khác với việc phân nhóm reserve/general, PHẢI
    # tính lại mỗi vòng — xem club_choice_function ở trên).
    base_rank: dict[str, dict[str, int]] = {}
    for club_id in clubs:
        base_order = compute_club_priority(
            club_id=club_id,
            applicants_for_club=applicants.get(club_id, []),
            tested_scores_for_club=tested_scores.get(club_id, {}),
            stb_lottery=stb_lottery,
        )
        base_rank[club_id] = {sid: i for i, sid in enumerate(base_order)}

    unassigned = [
        sid
        for sid in students
        if next_choice_idx[sid] < len(preferences.get(sid, []))
    ]

    round_num = 0
    while unassigned and round_num < max_rounds:
        round_num += 1
        proposals: dict[str, list[str]] = {cid: [] for cid in clubs}

        still_unassigned = []
        for sid in unassigned:
            prefs = preferences.get(sid, [])
            idx = next_choice_idx[sid]
            if idx >= len(prefs):
                continue  # hết nguyện vọng -> không xếp được (unmatched)
            club_id = prefs[idx]
            if club_id not in clubs:
                # Nguyện vọng trỏ tới club không tồn tại -> bỏ qua, coi
                # như bị từ chối ngay, thử nguyện vọng kế tiếp vòng sau.
                next_choice_idx[sid] += 1
                still_unassigned.append(sid)
                continue
            proposals[club_id].append(sid)

        for club_id, new_applicants in proposals.items():
            pool = held[club_id] + new_applicants
            rank = base_rank[club_id]
            capacity = clubs[club_id]["capacity"]
            reserve_capacity = clubs[club_id]["reserve_capacity"]
            eligible_fn = lambda sid, _cid=club_id: is_reserve_eligible_fn(sid, _cid)

            accepted, tier_of = club_choice_function(
                pool, capacity, reserve_capacity, eligible_fn, rank
            )
            accepted_set = set(accepted)
            rejected = [s for s in pool if s not in accepted_set]

            held[club_id] = accepted
            held_tier[club_id] = tier_of
            for sid in rejected:
                rejection_log.append((round_num, sid, club_id))
                next_choice_idx[sid] += 1
                still_unassigned.append(sid)

        unassigned = [
            sid
            for sid in still_unassigned
            if next_choice_idx[sid] < len(preferences.get(sid, []))
        ]

    assignment: dict[str, Optional[str]] = {sid: None for sid in students}
    matched_tier: dict[str, str] = {}
    rank_in_pref: dict[str, int] = {}
    for club_id, held_students in held.items():
        for sid in held_students:
            assignment[sid] = club_id
            matched_tier[sid] = held_tier[club_id].get(sid, "general")
            rank_in_pref[sid] = next_choice_idx[sid] + 1

    return MatchResult(
        assignment=assignment,
        rounds_run=round_num,
        rejection_log=rejection_log,
        base_rank=base_rank,
        matched_tier=matched_tier,
        rank_in_student_pref=rank_in_pref,
    )


def verify_stability(
    result: MatchResult,
    clubs: dict[str, dict],
    preferences: dict[str, list[str]],
    is_reserve_eligible_fn: Callable[[str, str], bool],
) -> list[str]:
    """
    Kiểm chứng KHÔNG TỒN TẠI blocking pair, dùng ĐÚNG hàm lựa chọn
    động (club_choice_function) — tức là kiểm tra trực tiếp: "nếu
    thêm sid vào tập đang giữ của club cid, hàm lựa chọn của club đó
    CÓ nhận sid không?" Đây là định nghĩa stability tổng quát, đúng
    cho cả trường hợp choice function không phải một thứ tự tuyến
    tính cố định (như RB-DA) — khác với cách làm cũ (dùng
    processed_priority tĩnh) đã bị phát hiện SAI khi đối chiếu với
    03_reference_rbda.py.

    Định nghĩa blocking pair (student sid, club cid):
        sid thích cid hơn club hiện tại của mình (hoặc đang unmatched
        mà cid vẫn còn nguyện vọng), VÀ khi thêm sid vào
        held[cid] hiện tại rồi áp dụng lại club_choice_function,
        sid NẰM TRONG tập được chọn.

    Returns:
        list[str]: danh sách mô tả từng blocking pair tìm được.
        Rỗng = kết quả ổn định (đúng theo lý thuyết, đúng theo
        club_choice_function thật của cơ chế).
    """
    problems: list[str] = []
    assignment = result.assignment

    held_by_club: dict[str, list[str]] = {cid: [] for cid in clubs}
    for sid, cid in assignment.items():
        if cid is not None:
            held_by_club[cid].append(sid)

    for sid, prefs in preferences.items():
        current_club = assignment.get(sid)
        current_idx = prefs.index(current_club) if current_club in prefs else len(prefs)

        for candidate_cid in prefs[:current_idx]:
            if candidate_cid not in clubs:
                continue
            rank = result.base_rank.get(candidate_cid, {})
            if sid not in rank:
                continue  # sid không nằm trong applicant pool của club này -> không thể block

            capacity = clubs[candidate_cid]["capacity"]
            reserve_capacity = clubs[candidate_cid]["reserve_capacity"]
            holders = held_by_club[candidate_cid]
            eligible_fn = lambda s, _cid=candidate_cid: is_reserve_eligible_fn(s, _cid)

            trial_pool = holders + [sid]
            accepted, _ = club_choice_function(
                trial_pool, capacity, reserve_capacity, eligible_fn, rank
            )
            if sid in accepted:
                problems.append(
                    f"Blocking pair: {sid} thich {candidate_cid} hon "
                    f"{current_club!r}, va se duoc nhan neu ap dung lai "
                    f"club_choice_function (hien co {len(holders)}/{capacity} cho)"
                )

    return problems


# ---------------------------------------------------------------------------
# BƯỚC D — PIPELINE 5 BƯỚC (khung — cần khớp schema thật)
# ---------------------------------------------------------------------------

def validate_data_integrity(
    students: dict[str, dict],
    clubs: dict[str, dict],
    preferences: dict[str, list[str]],
    applicants: dict[str, list[str]],
) -> list[str]:
    """
    Trả về danh sách lỗi (rỗng = dữ liệu hợp lệ). Không raise exception
    để pipeline có thể báo cáo TOÀN BỘ lỗi một lần thay vì dừng ở lỗi đầu.
    """
    errors: list[str] = []

    for sid, prefs in preferences.items():
        if sid not in students:
            errors.append(f"Học sinh {sid} có nguyện vọng nhưng không có trong students")
        if len(prefs) != len(set(prefs)):
            errors.append(f"Học sinh {sid} có club trùng lặp trong danh sách nguyện vọng")
        if len(prefs) > 10:
            errors.append(f"Học sinh {sid} có hơn 10 nguyện vọng (vượt giới hạn Microsoft Forms)")
        for cid in prefs:
            if cid not in clubs:
                errors.append(f"Học sinh {sid} xếp hạng club không tồn tại: {cid}")

    for cid, info in clubs.items():
        if info["capacity"] <= 0:
            errors.append(f"Club {cid} có capacity <= 0")
        if info["reserve_capacity"] > info["capacity"]:
            errors.append(f"Club {cid} có reserve_capacity > capacity")

    for cid, applicant_list in applicants.items():
        if cid not in clubs:
            errors.append(f"applicants tham chiếu club không tồn tại: {cid}")
        for sid in applicant_list:
            if sid not in students:
                errors.append(f"applicants tham chiếu học sinh không tồn tại: {sid}")

    return errors


def generate_stb_lottery(student_ids: list[str], seed: int) -> dict[str, int]:
    """
    Sinh số bốc thăm (STB) — một số duy nhất/học sinh, dùng chung mọi
    club (Single Tie-Breaking). seed cố định để có thể tái lập kết quả
    khi cần kiểm tra/audit.
    """
    import random

    rng = random.Random(seed)
    shuffled = student_ids.copy()
    rng.shuffle(shuffled)
    return {sid: idx for idx, sid in enumerate(shuffled)}


def export_match_results(match_result: MatchResult, output_path: str) -> None:
    """
    Xuất kết quả ra CSV: student_id, club_id, matched_tier,
    rank_in_student_pref (club_id rỗng = unmatched). Cùng bộ cột với
    write_results_csv() trong 03_reference_rbda.py (trừ priority_score_used
    và run_seed, có thể thêm sau nếu cần đối chiếu trực tiếp).
    """
    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "club_id", "matched_tier", "rank_in_student_pref"])
        for sid, cid in sorted(match_result.assignment.items()):
            writer.writerow([
                sid,
                cid or "",
                match_result.matched_tier.get(sid, ""),
                match_result.rank_in_student_pref.get(sid, ""),
            ])


DEFAULT_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    stb_number INTEGER,
    reserve_group TEXT          -- vd: 'khoi10', 'chinh_sach', hoặc NULL
);

CREATE TABLE IF NOT EXISTS clubs (
    club_id TEXT PRIMARY KEY,
    name TEXT,
    capacity INTEGER NOT NULL,
    reserve_capacity INTEGER NOT NULL DEFAULT 0,
    reserve_group TEXT          -- nhóm được ưu tiên dự trữ cho club này, NULL = không có dự trữ
);

CREATE TABLE IF NOT EXISTS club_test_selection (
    student_id TEXT NOT NULL,
    club_id TEXT NOT NULL,
    PRIMARY KEY (student_id, club_id)
);

CREATE TABLE IF NOT EXISTS club_scores (
    student_id TEXT NOT NULL,
    club_id TEXT NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY (student_id, club_id)
);

CREATE TABLE IF NOT EXISTS preferences (
    student_id TEXT NOT NULL,
    club_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    PRIMARY KEY (student_id, club_id)
);

CREATE TABLE IF NOT EXISTS match_results (
    student_id TEXT PRIMARY KEY,
    club_id TEXT,               -- NULL = unmatched
    round_num INTEGER,
    matched_tier TEXT,          -- 'reserve' | 'general' | NULL
    rank_in_student_pref INTEGER  -- thu hang nguyen vong da duoc xep (1-indexed), NULL neu unmatched
);

CREATE TABLE IF NOT EXISTS run_meta (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- chi 1 dong duy nhat, luon ghi de (lan chay GAN NHAT)
    seed INTEGER,
    run_at TEXT,
    rounds_run INTEGER,
    n_matched INTEGER,
    n_total INTEGER
);

-- Nhat ky TOAN BO cac lan chay pipeline (khong bao gio xoa/ghi de) —
-- giai quyet van de "chay lan 2 xoa mat dau vet lan 1". match_results
-- van chi giu ban ghi MOI NHAT (vi la nguon cho UI Ket qua), nhung
-- run_history cho biet CO nhung lan chay nao, khi nao, ai lam, ket qua
-- tong quan the nao, phuc vu kiem toan (audit).
CREATE TABLE IF NOT EXISTS run_history (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed INTEGER,
    run_at TEXT,
    rounds_run INTEGER,
    n_matched INTEGER,
    n_total INTEGER,
    stb_redrawn INTEGER NOT NULL DEFAULT 0  -- 1 neu lan nay ve lai so bac tham, 0 neu tai su dung STB da khoa
);

-- Khoa so bac tham (STB). Chi 1 dong duy nhat. Khi da_khoa = 1, nut
-- "Chay pipeline" se KHONG duoc phep sinh lai stb_number cho hoc sinh
-- (tru khi nguoi dung chu dong go khoa qua xac nhan 2 buoc tren UI).
-- Day la co che chong "vo tinh bac tham lai" anh huong toi tinh minh
-- bach/audit trust cua ket qua da cong bo.
CREATE TABLE IF NOT EXISTS stb_lock (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    is_locked INTEGER NOT NULL DEFAULT 0,
    locked_at TEXT,
    unlocked_at TEXT
);
"""


def init_db(db_path: str) -> None:
    """Tạo app.db với schema mặc định nếu chưa tồn tại (idempotent)."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.executescript(DEFAULT_SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO stb_lock (id, is_locked, locked_at, unlocked_at) "
        "VALUES (1, 0, NULL, NULL)"
    )
    conn.commit()
    conn.close()


def default_reserve_eligible_fn(students: dict[str, dict], clubs: dict[str, dict]):
    """
    Diện dự trữ mặc định: học sinh eligible cho club X nếu
    students[sid]['reserve_group'] == clubs[X]['reserve_group']
    (và reserve_group của club khác NULL). Đơn giản, dễ đổi sau.
    """
    def fn(sid: str, cid: str) -> bool:
        club_group = clubs.get(cid, {}).get("reserve_group")
        if not club_group:
            return False
        return students.get(sid, {}).get("reserve_group") == club_group
    return fn


def load_from_sqlite(db_path: str):
    """
    Đọc toàn bộ dữ liệu cần thiết từ app.db theo DEFAULT_SCHEMA và
    trả về đúng format mà run_rbda() cần.

    Returns:
        (students, clubs, tested_scores, applicants, preferences)
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    students = {}
    for row in cur.execute("SELECT student_id, stb_number, reserve_group FROM students"):
        students[row["student_id"]] = {
            "stb": row["stb_number"],
            "reserve_group": row["reserve_group"],
        }

    clubs = {}
    for row in cur.execute(
        "SELECT club_id, capacity, reserve_capacity, reserve_group FROM clubs"
    ):
        clubs[row["club_id"]] = {
            "capacity": row["capacity"],
            "reserve_capacity": row["reserve_capacity"],
            "reserve_group": row["reserve_group"],
        }

    tested_scores: dict[str, dict[str, float]] = {cid: {} for cid in clubs}
    for row in cur.execute("SELECT student_id, club_id, score FROM club_scores"):
        tested_scores.setdefault(row["club_id"], {})[row["student_id"]] = row["score"]

    applicants: dict[str, list[str]] = {cid: [] for cid in clubs}
    for row in cur.execute("SELECT student_id, club_id FROM club_test_selection"):
        applicants.setdefault(row["club_id"], []).append(row["student_id"])
    # applicants cũng phải bao gồm học sinh KHÔNG test nhưng có xếp hạng
    # club đó trong preferences (Tier 2 vẫn được xét vào club không yêu
    # cầu thi). Bổ sung ở dưới sau khi đọc preferences.

    preferences_raw: dict[str, list[tuple[int, str]]] = {}
    for row in cur.execute(
        "SELECT student_id, club_id, rank FROM preferences ORDER BY student_id, rank"
    ):
        preferences_raw.setdefault(row["student_id"], []).append(
            (row["rank"], row["club_id"])
        )
    preferences = {
        sid: [cid for _, cid in sorted(entries)]
        for sid, entries in preferences_raw.items()
    }

    for sid, ranked_clubs in preferences.items():
        for cid in ranked_clubs:
            if cid in applicants and sid not in applicants[cid]:
                applicants[cid].append(sid)

    conn.close()
    stb_lottery = {sid: info["stb"] for sid, info in students.items()}
    return students, clubs, tested_scores, applicants, preferences, stb_lottery


def write_match_results_to_sqlite(
    db_path: str, match_result: MatchResult
) -> None:
    """Ghi kết quả vào bảng match_results (ghi đè toàn bộ), kèm tier và thứ hạng nguyện vọng."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM match_results")
    cur.executemany(
        "INSERT INTO match_results (student_id, club_id, round_num, matched_tier, rank_in_student_pref) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (
                sid, cid, match_result.rounds_run,
                match_result.matched_tier.get(sid),
                match_result.rank_in_student_pref.get(sid),
            )
            for sid, cid in match_result.assignment.items()
        ],
    )
    conn.commit()
    conn.close()


def run_full_pipeline(db_path: str, seed: int, output_csv_path: str) -> MatchResult:
    """
    Chạy trọn 5 bước: validate -> STB -> RB-DA -> ghi DB -> export CSV.
    Raise RuntimeError nếu validate_data_integrity() phát hiện lỗi.
    """
    init_db(db_path)
    students, clubs, tested_scores, applicants, preferences, _ = load_from_sqlite(
        db_path
    )

    errors = validate_data_integrity(students, clubs, preferences, applicants)
    if errors:
        raise RuntimeError("Loi du lieu:\n" + "\n".join(errors))

    stb_lottery = generate_stb_lottery(list(students.keys()), seed=seed)
    # Ghi STB vừa sinh ngược lại vào DB để tái sử dụng / audit.
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.executemany(
        "UPDATE students SET stb_number = ? WHERE student_id = ?",
        [(v, k) for k, v in stb_lottery.items()],
    )
    conn.commit()
    conn.close()

    reserve_fn = default_reserve_eligible_fn(students, clubs)
    result = run_rbda(
        students,
        clubs,
        tested_scores,
        applicants,
        preferences,
        stb_lottery,
        is_reserve_eligible_fn=reserve_fn,
    )

    write_match_results_to_sqlite(db_path, result)
    export_match_results(result, output_csv_path)
    return result


# ---------------------------------------------------------------------------
# BƯỚC E — SEED DỮ LIỆU MẪU (để chạy thử full pipeline end-to-end)
# ---------------------------------------------------------------------------

def seed_sample_data(
    db_path: str,
    n_students: int = 200,
    club_defs: Optional[list[tuple[str, int, int, Optional[str]]]] = None,
    seed: int = 7,
) -> None:
    """
    Sinh dữ liệu mẫu ngẫu nhiên nhưng thực tế (đúng ràng buộc: tối đa
    10 nguyện vọng, tick-box tách biệt khỏi xếp hạng, một phần học
    sinh được chấm điểm tier1) và ghi vào app.db.

    club_defs: list[(club_id, capacity, reserve_capacity, reserve_group)]
        Mặc định tạo 10 club nếu không truyền vào.
    """
    import random
    import sqlite3

    rng = random.Random(seed)
    init_db(db_path)

    if club_defs is None:
        club_defs = []
        for i in range(1, 11):
            reserve_cap = 2 if i % 3 == 0 else 0
            reserve_group = "chinh_sach" if reserve_cap else None
            club_defs.append((f"club_{i:02d}", 15, reserve_cap, reserve_group))

    student_ids = [f"stu_{i:04d}" for i in range(1, n_students + 1)]
    reserve_groups = ["chinh_sach", None, None, None]  # ~25% thuộc diện dự trữ

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM students")
    cur.execute("DELETE FROM clubs")
    cur.execute("DELETE FROM club_test_selection")
    cur.execute("DELETE FROM club_scores")
    cur.execute("DELETE FROM preferences")
    cur.execute("DELETE FROM match_results")

    cur.executemany(
        "INSERT INTO students (student_id, name, stb_number, reserve_group) VALUES (?, ?, ?, ?)",
        [
            (sid, sid, None, rng.choice(reserve_groups))
            for sid in student_ids
        ],
    )
    cur.executemany(
        "INSERT INTO clubs (club_id, name, capacity, reserve_capacity, reserve_group) VALUES (?, ?, ?, ?, ?)",
        [(cid, cid, cap, rcap, rgrp) for cid, cap, rcap, rgrp in club_defs],
    )

    club_ids = [c[0] for c in club_defs]
    test_rows, score_rows, pref_rows = [], [], []

    for sid in student_ids:
        n_prefs = rng.randint(4, 10)
        ranked_clubs = rng.sample(club_ids, n_prefs)
        for rank, cid in enumerate(ranked_clubs, start=1):
            pref_rows.append((sid, cid, rank))

        # Tick-box thi: chọn ngẫu nhiên 1-3 club trong số đã xếp hạng để "thi"
        n_tested = rng.randint(0, min(3, n_prefs))
        tested_clubs = rng.sample(ranked_clubs, n_tested)
        for cid in tested_clubs:
            test_rows.append((sid, cid))
            score_rows.append((sid, cid, round(rng.uniform(4.0, 10.0), 2)))

        # applicants (tick-box) cũng cần bao gồm mọi club đã xếp hạng,
        # kể cả club không thi (Tier 2) -> ghi vào club_test_selection
        # với vai trò "đã đăng ký xét" (không nhất thiết = đã thi).
        for cid in ranked_clubs:
            if (sid, cid) not in test_rows:
                test_rows.append((sid, cid))

    cur.executemany(
        "INSERT OR IGNORE INTO club_test_selection (student_id, club_id) VALUES (?, ?)",
        test_rows,
    )
    cur.executemany(
        "INSERT INTO club_scores (student_id, club_id, score) VALUES (?, ?, ?)",
        score_rows,
    )
    cur.executemany(
        "INSERT INTO preferences (student_id, club_id, rank) VALUES (?, ?, ?)",
        pref_rows,
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# BƯỚC F — KIỂM TRA TÍNH ĐÚNG ĐẮN (sanity checks, không thay expected_match_results.csv)
# ---------------------------------------------------------------------------

def sanity_check_result(
    result: MatchResult,
    clubs: dict[str, dict],
    preferences: dict[str, list[str]],
) -> list[str]:
    """
    Kiểm tra các bất biến bắt buộc của một kết quả matching hợp lệ
    (giống validate_results() trong 03_reference_rbda.py):
      1. Không club nào vượt capacity.
      2. Không club nào có số suất TIER DỰ TRỮ vượt reserve_capacity.
      3. Mỗi học sinh chỉ được xếp vào ĐÚNG 1 club (hoặc None).
      4. Club được gán phải nằm trong danh sách nguyện vọng của học sinh đó.
    Kiểm tra stability đầy đủ nằm ở verify_stability() (dùng
    club_choice_function thật, không phải suy luận tĩnh).
    """
    problems: list[str] = []

    club_counts: dict[str, int] = {}
    club_reserve_counts: dict[str, int] = {}
    for sid, cid in result.assignment.items():
        if cid is None:
            continue
        club_counts[cid] = club_counts.get(cid, 0) + 1
        if result.matched_tier.get(sid) == "reserve":
            club_reserve_counts[cid] = club_reserve_counts.get(cid, 0) + 1
        if cid not in preferences.get(sid, []):
            problems.append(f"{sid} được xếp vào {cid} nhưng không có trong nguyện vọng")

    for cid, count in club_counts.items():
        cap = clubs[cid]["capacity"]
        if count > cap:
            problems.append(f"Club {cid} vượt capacity: {count}/{cap}")

    for cid, count in club_reserve_counts.items():
        reserve_cap = clubs[cid]["reserve_capacity"]
        if count > reserve_cap:
            problems.append(f"Club {cid} vượt reserve_capacity ở tier dự trữ: {count}/{reserve_cap}")

    return problems


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "app.db"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    out_csv = sys.argv[3] if len(sys.argv) > 3 else "match_results.csv"
    result = run_full_pipeline(db_path, seed, out_csv)
    print(f"Xong. {sum(1 for v in result.assignment.values() if v)} / "
          f"{len(result.assignment)} hoc sinh duoc xep club. "
          f"So vong chay: {result.rounds_run}. Ket qua: {out_csv}")
