"""
i18n_errors.py
==============
Shared bilingual (vi/en) error-message catalog. api.py and
rbda_priority_pipeline.py build error entries as {"code": ..., "params":
{...}} instead of pre-formatted prose, so the frontend (app.js has its own
matching copy of this catalog) can render either language without a
round-trip to Python. `format_message`/`format_all` render plain text for
callers that don't go through the JSON API (the CLI entry point, logs).

IMPORTANT: keep this file's keys in sync with the ERROR_MESSAGES object in
app.js — a test in tests/test_api.py asserts every code the API can emit
has an entry here with both "vi" and "en".
"""

DEFAULT_LANG = "vi"

MESSAGES = {
    # --- generic / unexpected exceptions (detail = str(exception), left untranslated) ---
    "error_reading_last_run": {
        "vi": "Lỗi đọc thông tin lần chạy gần nhất: {detail}",
        "en": "Error reading last run info: {detail}",
    },
    "error_reading_dashboard": {
        "vi": "Lỗi đọc trạng thái tổng quan: {detail}",
        "en": "Error reading dashboard status: {detail}",
    },
    "error_checking_integrity": {
        "vi": "Lỗi khi kiểm tra dữ liệu: {detail}",
        "en": "Error checking data integrity: {detail}",
    },
    "error_checking_run_warning": {
        "vi": "Lỗi kiểm tra trạng thái trước khi chạy: {detail}",
        "en": "Error checking pre-run status: {detail}",
    },
    "error_reading_stb_lock": {
        "vi": "Lỗi đọc trạng thái khoá STB: {detail}",
        "en": "Error reading STB lock status: {detail}",
    },
    "error_reading_run_history": {
        "vi": "Lỗi đọc nhật ký chạy: {detail}",
        "en": "Error reading run history: {detail}",
    },
    "error_running_pipeline": {
        "vi": "Lỗi không xác định khi chạy pipeline: {detail}",
        "en": "Unexpected error while running the pipeline: {detail}",
    },
    "error_reading_csv_preview": {
        "vi": "Lỗi đọc trước CSV: {detail}",
        "en": "Error previewing CSV: {detail}",
    },
    "error_importing_preferences_csv": {
        "vi": "Lỗi nhập CSV nguyện vọng: {detail}",
        "en": "Error importing preferences CSV: {detail}",
    },
    "error_importing_test_selection_csv": {
        "vi": "Lỗi nhập CSV chọn club thi: {detail}",
        "en": "Error importing test-selection CSV: {detail}",
    },
    "error_reading_scoring_overview": {
        "vi": "Lỗi đọc tổng quan chấm điểm: {detail}",
        "en": "Error reading scoring overview: {detail}",
    },
    "error_reading_scoring_list": {
        "vi": "Lỗi đọc danh sách chấm điểm: {detail}",
        "en": "Error reading scoring list: {detail}",
    },
    "error_saving_scores": {
        "vi": "Lỗi lưu điểm: {detail}",
        "en": "Error saving scores: {detail}",
    },
    "error_reading_results": {
        "vi": "Lỗi đọc kết quả: {detail}",
        "en": "Error reading results: {detail}",
    },
    "error_detecting_csv_kind": {
        "vi": "Lỗi nhận diện loại file CSV: {detail}",
        "en": "Error detecting CSV kind: {detail}",
    },
    "error_importing_csv_auto": {
        "vi": "Lỗi nhập CSV: {detail}",
        "en": "CSV import failed: {detail}",
    },
    "error_importing_clubs_csv": {
        "vi": "Lỗi nhập CSV danh sách CLB: {detail}",
        "en": "Error importing club list CSV: {detail}",
    },
    "csv_kind_ambiguous": {
        "vi": "Chưa xác định được đây là file gì. Bộ cột {fieldnames} vừa có thể là chọn CLB muốn thi, vừa có thể là xếp hạng nguyện vọng. Hãy chọn giúp loại file, hoặc thêm cột rank nếu đây là nguyện vọng.",
        "en": "Cannot tell what this file is. The columns {fieldnames} could be either club test selection or ranked preferences. Please pick the kind, or add a rank column if these are preferences.",
    },
    "csv_kind_unknown": {
        "vi": "Không nhận ra định dạng file. Xem mau_csv/HUONG_DAN_CSV.md để biết các cột phần mềm đọc được.",
        "en": "Unrecognised file format. See mau_csv/HUONG_DAN_CSV.md for the columns the app can read.",
    },
    "csv_club_row_invalid": {
        "vi": "Dòng {line}: bỏ qua vì {reason} không hợp lệ (chỉ tiêu phải lớn hơn 0 và chỉ tiêu dự trữ không được vượt quá tổng chỉ tiêu).",
        "en": "Line {line}: skipped because {reason} is invalid (capacity must be above 0 and reserve capacity cannot exceed capacity).",
    },
    "xlsx_read_failed": {
        "vi": "Không đọc được file Excel: {detail}. Kiểm tra lại xem đúng là file .xlsx không, hoặc lưu lại rồi thử lần nữa.",
        "en": "Could not read the Excel file: {detail}. Check it really is an .xlsx file, or re-save it and try again.",
    },
    "xlsx_empty": {
        "vi": "File Excel không có dữ liệu nào.",
        "en": "The Excel file has no data.",
    },
    "xlsx_support_missing": {
        "vi": "Bản cài này thiếu thư viện đọc Excel (openpyxl). Hãy lưu file sang định dạng CSV UTF-8 rồi nạp lại.",
        "en": "This build is missing the Excel reader (openpyxl). Save the file as CSV UTF-8 and try again.",
    },
    "csv_reserve_group_unknown": {
        "vi": "Nhãn dự trữ {reserve_group} ({n} học sinh) không CLB nào nhận — các em này sẽ KHÔNG được xét diện dự trữ. Có phải bạn định ghi {goi_y}?",
        "en": "Reserve label {reserve_group} ({n} student(s)) is not used by any club — they will NOT be considered for reserve places. Did you mean {goi_y}?",
    },
    "csv_duplicate_student_rows": {
        "vi": "Mã {student_id} xuất hiện {n} lần trong file — chỉ dòng CUỐI được giữ, các dòng trước bị ghi đè. Kiểm tra lại nếu đó không phải ý bạn.",
        "en": "Student {student_id} appears {n} times in the file — only the LAST row is kept and the earlier ones are overwritten. Check this is intended.",
    },
    "csv_student_id_case_conflict": {
        "vi": "Mã {student_id} chỉ khác chữ hoa/thường so với mã {da_co} đã có — phần mềm đang coi đây là HAI học sinh khác nhau. Nếu là một người, hãy sửa cho hai file dùng cùng một kiểu viết.",
        "en": "Student id {student_id} differs from the existing {da_co} only in case — these are being treated as TWO different students. If they are the same person, make both files use the same spelling.",
    },
    "csv_student_id_maybe_truncated": {
        "vi": "Mã {student_id} chỉ dài {do_dai} chữ số, trong khi phần lớn mã trong file dài {do_dai_pho_bien} — nhiều khả năng Excel đã cắt mất số 0 ở đầu. Mở file gốc, đặt định dạng cột mã là Text rồi nhập lại.",
        "en": "Student id {student_id} has only {do_dai} digits while most ids in the file have {do_dai_pho_bien} — Excel has most likely stripped leading zeros. Reopen the source file, set the id column to Text, and re-import.",
    },
    "error_reading_club_stats": {
        "vi": "Lỗi đọc thống kê club: {detail}",
        "en": "Error reading club stats: {detail}",
    },
    "error_exporting_csv": {
        "vi": "Lỗi xuất CSV: {detail}",
        "en": "Error exporting CSV: {detail}",
    },
    "error_saving_club": {
        "vi": "Lỗi lưu club: {detail}",
        "en": "Error saving club: {detail}",
    },
    "error_deleting_club": {
        "vi": "Lỗi xoá club: {detail}",
        "en": "Error deleting club: {detail}",
    },
    "error_reading_reserve_groups": {
        "vi": "Lỗi đọc danh sách nhãn dự trữ: {detail}",
        "en": "Error reading reserve groups: {detail}",
    },
    "error_assigning_reserve_group": {
        "vi": "Lỗi gán nhãn dự trữ: {detail}",
        "en": "Error assigning reserve group: {detail}",
    },
    "error_bulk_assigning": {
        "vi": "Lỗi gán hàng loạt: {detail}",
        "en": "Error bulk-assigning: {detail}",
    },
    "error_reading_student_list": {
        "vi": "Lỗi đọc danh sách học sinh: {detail}",
        "en": "Error reading student list: {detail}",
    },
    "error_reading_club_list": {
        "vi": "Lỗi đọc danh sách club: {detail}",
        "en": "Error reading club list: {detail}",
    },
    "error_searching_students": {
        "vi": "Lỗi tìm học sinh: {detail}",
        "en": "Error searching students: {detail}",
    },
    "error_reading_student_state": {
        "vi": "Lỗi đọc trạng thái học sinh: {detail}",
        "en": "Error reading student state: {detail}",
    },
    "error_saving_test_selection": {
        "vi": "Lỗi ghi lựa chọn thi: {detail}",
        "en": "Error saving test selection: {detail}",
    },
    "error_saving_preferences": {
        "vi": "Lỗi ghi nguyện vọng: {detail}",
        "en": "Error saving preferences: {detail}",
    },
    "error_creating_student": {
        "vi": "Lỗi tạo học sinh: {detail}",
        "en": "Error creating student: {detail}",
    },
    "error_resetting_student_entry": {
        "vi": "Lỗi xoá lựa chọn để nhập lại: {detail}",
        "en": "Error resetting student entry: {detail}",
    },
    "error_deleting_student": {
        "vi": "Lỗi xoá học sinh: {detail}",
        "en": "Error deleting student: {detail}",
    },

    # --- CSV ---
    "csv_empty": {
        "vi": "File CSV rỗng hoặc không đọc được dòng nào.",
        "en": "The CSV file is empty, or no rows could be read.",
    },
    "csv_missing_columns": {
        "vi": "CSV dạng \"dài\" cần có cột student_id và club_id (cột hiện có: {fieldnames})",
        "en": "\"Long\" format CSV needs student_id and club_id columns (columns found: {fieldnames})",
    },

    # --- validation (surfaced directly to the kiosk operator) ---
    "capacity_must_be_positive": {
        "vi": "Tổng chỗ (capacity) phải > 0",
        "en": "Capacity must be greater than 0",
    },
    "reserve_capacity_exceeds_capacity": {
        "vi": "Suất dự trữ không được lớn hơn tổng chỗ",
        "en": "Reserve capacity cannot exceed total capacity",
    },
    "club_id_required": {
        "vi": "Cần nhập mã club",
        "en": "Club ID is required",
    },
    "cannot_delete_club_referenced": {
        "vi": "Không thể xoá: club {club_id} đã có {n_prefs} nguyện vọng và {n_matches} kết quả tham chiếu tới. Phải xử lý dữ liệu liên quan trước.",
        "en": "Cannot delete: club {club_id} is referenced by {n_prefs} preference(s) and {n_matches} match result(s). Handle the related data first.",
    },
    "student_not_found": {
        "vi": "Học sinh {student_id} không tồn tại",
        "en": "Student {student_id} does not exist",
    },
    "club_not_found": {
        "vi": "Club {club_id} không tồn tại",
        "en": "Club {club_id} does not exist",
    },
    "unknown_clubs": {
        "vi": "Club không tồn tại: {club_ids}",
        "en": "Unknown club(s): {club_ids}",
    },
    "scores_must_be_nonempty_list": {
        "vi": "scores phải là danh sách không rỗng",
        "en": "scores must be a non-empty list",
    },
    "student_ids_must_be_nonempty_list": {
        "vi": "student_ids phải là danh sách không rỗng",
        "en": "student_ids must be a non-empty list",
    },
    "club_ids_must_be_list": {
        "vi": "club_ids phải là danh sách",
        "en": "club_ids must be a list",
    },
    "ordered_club_ids_must_be_list": {
        "vi": "ordered_club_ids phải là danh sách",
        "en": "ordered_club_ids must be a list",
    },
    "must_rank_at_least_one": {
        "vi": "Phải xếp hạng ít nhất 1 nguyện vọng",
        "en": "You must rank at least 1 preference",
    },
    "max_10_preferences": {
        "vi": "Tối đa 10 nguyện vọng",
        "en": "Maximum 10 preferences",
    },
    "duplicate_preference_in_list": {
        "vi": "Danh sách nguyện vọng có club trùng lặp",
        "en": "The preference list has a duplicate club",
    },
    "cannot_delete_student_matched": {
        "vi": "Không thể xoá: học sinh {student_id} đã có trong kết quả của lần chạy pipeline gần nhất. Hãy chạy lại pipeline sau khi xử lý.",
        "en": "Cannot delete: student {student_id} is already in the results of the latest pipeline run. Re-run the pipeline after handling this.",
    },

    # --- pipeline step details (shown in the stepper, not just errors) ---
    "stb_redrawn_and_locked": {
        "vi": "Đã vẽ mới STB cho {n} học sinh và khoá lại.",
        "en": "Drew new STB numbers for {n} student(s) and locked them.",
    },
    "stb_supplemented": {
        "vi": "STB đã khoá — giữ nguyên số cũ, chỉ vẽ bổ sung cho {n} học sinh mới chưa có số.",
        "en": "STB already locked — kept existing numbers, drew supplemental numbers for {n} new student(s) only.",
    },
    "stb_reused": {
        "vi": "STB đã khoá — tái sử dụng toàn bộ số cũ, không vẽ lại.",
        "en": "STB already locked — reused all existing numbers, no redraw.",
    },
    "rbda_done": {
        "vi": "{rounds} vòng lặp, không lỗi",
        "en": "{rounds} round(s), no errors",
    },
    "db_backed_up": {
        "vi": "Đã sao lưu app.db trước khi chạy: {backup_name}",
        "en": "Backed up app.db before running: {backup_name}",
    },
    "db_backup_failed": {
        "vi": "Không sao lưu được app.db (pipeline vẫn tiếp tục chạy): {detail}",
        "en": "Could not back up app.db (pipeline still continues): {detail}",
    },
    "pipeline_rolled_back": {
        "vi": "Đã huỷ toàn bộ thay đổi của lần chạy này (kể cả số STB vừa vẽ, nếu có) do lỗi giữa chừng — dữ liệu quay lại đúng trạng thái trước khi bấm chạy.",
        "en": "Rolled back every change from this run (including any freshly drawn STB numbers) because of a mid-run error — data is back to exactly the state before you clicked run.",
    },

    # --- validate_data_integrity (rbda_priority_pipeline.py) ---
    "pref_student_not_in_students": {
        "vi": "Học sinh {student_id} có nguyện vọng nhưng không có trong students",
        "en": "Student {student_id} has preferences but is not in students",
    },
    "pref_duplicate_club": {
        "vi": "Học sinh {student_id} có club trùng lặp trong danh sách nguyện vọng",
        "en": "Student {student_id} has a duplicate club in their preference list",
    },
    "pref_too_many": {
        "vi": "Học sinh {student_id} có hơn 10 nguyện vọng (vượt giới hạn Microsoft Forms)",
        "en": "Student {student_id} has more than 10 preferences (exceeds the Microsoft Forms limit)",
    },
    "pref_unknown_club": {
        "vi": "Học sinh {student_id} xếp hạng club không tồn tại: {club_id}",
        "en": "Student {student_id} ranked a club that does not exist: {club_id}",
    },
    "club_capacity_not_positive": {
        "vi": "Club {club_id} có capacity <= 0",
        "en": "Club {club_id} has capacity <= 0",
    },
    "club_reserve_exceeds_capacity": {
        "vi": "Club {club_id} có reserve_capacity > capacity",
        "en": "Club {club_id} has reserve_capacity > capacity",
    },
    "applicants_unknown_club": {
        "vi": "applicants tham chiếu club không tồn tại: {club_id}",
        "en": "applicants references a club that does not exist: {club_id}",
    },
    "applicants_unknown_student": {
        "vi": "applicants tham chiếu học sinh không tồn tại: {student_id}",
        "en": "applicants references a student that does not exist: {student_id}",
    },

    # --- sanity_check_result ---
    "assignment_not_in_preferences": {
        "vi": "{student_id} được xếp vào {club_id} nhưng không có trong nguyện vọng",
        "en": "{student_id} was assigned to {club_id} but it is not in their preferences",
    },
    "club_over_capacity": {
        "vi": "Club {club_id} vượt capacity: {count}/{capacity}",
        "en": "Club {club_id} exceeds capacity: {count}/{capacity}",
    },
    "club_over_reserve_capacity": {
        "vi": "Club {club_id} vượt reserve_capacity ở tier dự trữ: {count}/{reserve_capacity}",
        "en": "Club {club_id} exceeds reserve_capacity in the reserve tier: {count}/{reserve_capacity}",
    },

    # --- verify_stability ---
    "blocking_pair": {
        "vi": "Blocking pair: {student_id} thích {club_id} hơn {current_club}, và sẽ được nhận nếu áp dụng lại club_choice_function (hiện có {n_holders}/{capacity} chỗ)",
        "en": "Blocking pair: {student_id} prefers {club_id} over {current_club}, and would be accepted if club_choice_function were re-applied (currently {n_holders}/{capacity} seats held)",
    },

    # --- CSV import row warnings (returned inside a successful "ok" response) ---
    "csv_pref_duplicate_deduped": {
        "vi": "{student_id}: có club trùng lặp trong nguyện vọng, đã tự động loại bỏ trùng.",
        "en": "{student_id}: had a duplicate club in preferences; duplicates were removed automatically.",
    },
    "csv_pref_too_many_skipped": {
        "vi": "{student_id}: có {count} nguyện vọng (>10), CHƯA nhập — bỏ qua học sinh này.",
        "en": "{student_id}: has {count} preferences (>10), NOT imported — this student was skipped.",
    },
    "csv_unknown_clubs_skipped": {
        "vi": "{student_id}: club không tồn tại {club_ids} — bỏ qua học sinh này.",
        "en": "{student_id}: unknown club(s) {club_ids} — this student was skipped.",
    },
    "csv_student_missing_skipped": {
        "vi": "{student_id}: chưa có trong hệ thống, bỏ qua (create_missing_students=False).",
        "en": "{student_id}: not yet in the system, skipped (create_missing_students=False).",
    },
    "score_not_applicant": {
        "vi": "{student_id}: không nằm trong danh sách thi/xét club này",
        "en": "{student_id}: is not registered to test/apply for this club",
    },
    "score_not_a_number": {
        "vi": "{student_id}: điểm '{score}' không phải số",
        "en": "{student_id}: score '{score}' is not a number",
    },

    # --- CẢNH BÁO SỨC KHOẺ DỮ LIỆU (get_data_health_report) ---
    # Đây KHÔNG phải lỗi — dữ liệu vẫn hợp lệ và pipeline vẫn chạy được.
    # Nhưng mỗi mục dưới đây đều làm KẾT QUẢ THAY ĐỔI theo cách người vận
    # hành không nhìn thấy, nên phải cảnh báo TRƯỚC khi chạy.
    "health_scoring_none": {
        "vi": "Club {club_id}: có {n_applicants} học sinh đăng ký thi nhưng CHƯA CHẤM ĐIỂM AI. Toàn bộ các em này sẽ rơi xuống Tầng 2 và chỉ được xét bằng số bốc thăm — vòng thi coi như không có tác dụng.",
        "en": "Club {club_id}: {n_applicants} student(s) registered for the tryout but NOBODY has been scored. All of them drop to Tier 2 and will be decided by lottery only — the tryout will have no effect.",
    },
    "health_scoring_partial": {
        "vi": "Club {club_id}: mới chấm {n_scored}/{n_applicants} học sinh. {n_missing} em chưa có điểm sẽ bị xếp dưới TẤT CẢ các em đã có điểm, kể cả em điểm thấp nhất.",
        "en": "Club {club_id}: only {n_scored} of {n_applicants} scored. The {n_missing} unscored student(s) will rank below EVERY scored student, including the lowest-scoring one.",
    },
    "health_tested_not_ranked": {
        "vi": "{n} lượt đăng ký thi sẽ bị bỏ phí: học sinh đã đăng ký thi một club nhưng không xếp club đó vào nguyện vọng, nên dù điểm cao vẫn không thể được xếp vào đó. Ví dụ: {sample}",
        "en": "{n} tryout registration(s) will be wasted: the student registered to test for a club but did not rank it, so no matter how well they score they cannot be placed there. For example: {sample}",
    },
    "health_student_no_preferences": {
        "vi": "{n} học sinh chưa xếp nguyện vọng nào — các em này chắc chắn không được xếp vào club nào. Ví dụ: {sample}",
        "en": "{n} student(s) have not ranked any preference — they cannot be placed in any club. For example: {sample}",
    },
    "health_orphan_student_group": {
        "vi": "Nhãn dự trữ \"{reserve_group}\" đang gán cho {n} học sinh nhưng KHÔNG club nào dùng nhãn này. Các em đó sẽ không được ưu tiên ở đâu cả — kiểm tra xem có gõ sai chính tả không.",
        "en": "Reserve label \"{reserve_group}\" is assigned to {n} student(s) but NO club uses it. Those students get no priority anywhere — check for a typo.",
    },
    "health_club_reserve_no_group": {
        "vi": "Club {club_id} có {reserve_capacity} suất dự trữ nhưng chưa đặt nhãn dự trữ. Các suất này sẽ âm thầm chuyển thành suất phổ thông.",
        "en": "Club {club_id} has {reserve_capacity} reserve seat(s) but no reserve label set. Those seats will silently become general seats.",
    },
    "health_club_group_no_students": {
        "vi": "Club {club_id} dành {reserve_capacity} suất cho nhãn \"{reserve_group}\", nhưng chưa học sinh nào mang nhãn đó. Suất dự trữ sẽ không dùng đến.",
        "en": "Club {club_id} reserves {reserve_capacity} seat(s) for label \"{reserve_group}\", but no student carries that label. The reserve seats will go unused.",
    },
    "health_oversubscribed": {
        "vi": "Tổng chỗ toàn hệ thống là {n_seats}, trong khi có {n_students} học sinh đã nộp nguyện vọng. Ít nhất {n_short} em chắc chắn không có chỗ.",
        "en": "Total seats across all clubs is {n_seats}, but {n_students} student(s) have submitted preferences. At least {n_short} student(s) cannot be placed.",
    },

    # --- recovery.py / recovery.html — màn hình phục hồi khi app.db
    # hỏng/mất và PipelineAPI không khởi tạo được (xem main.py) ---
    "recovery_no_backups": {
        "vi": "Không tìm thấy bản sao lưu nào — có thể chưa từng chạy pipeline lần nào trên máy này, hoặc thư mục sao lưu đã bị xoá.",
        "en": "No backups found — the pipeline may never have run on this machine, or the backup folder was deleted.",
    },
    "recovery_all_backups_corrupt": {
        "vi": "Đã thử cả {n_tried} bản sao lưu tìm thấy nhưng không bản nào đọc được nguyên vẹn.",
        "en": "Tried all {n_tried} backup(s) found, but none of them could be read intact.",
    },
    "recovery_restore_failed": {
        "vi": "Khôi phục thất bại: {detail}",
        "en": "Restore failed: {detail}",
    },
    "recovery_restored_from": {
        "vi": "Đã khôi phục từ bản sao lưu {backup_name}"
              " (bỏ qua {n_skipped} bản mới hơn vì đọc không được).",
        "en": "Restored from backup {backup_name}"
              " (skipped {n_skipped} newer backup(s) that could not be read).",
    },
    "recovery_fresh_created": {
        "vi": "Đã tạo app.db mới hoàn toàn trống. Tệp cũ được đổi tên (không xoá), nằm cùng thư mục.",
        "en": "Created a brand-new, empty app.db. The old file was renamed (not deleted) and is in the same folder.",
    },
}


def err(code: str, **params) -> dict:
    """Build one structured, translatable error/info entry."""
    return {"code": code, "params": params}


def format_message(code: str, params: dict | None = None, lang: str = DEFAULT_LANG) -> str:
    """Render one entry as plain text for callers outside the JSON API
    (CLI, logs) — the frontend renders {code, params} itself instead."""
    params = params or {}
    entry = MESSAGES.get(code)
    if not entry:
        return code
    template = entry.get(lang) or entry.get(DEFAULT_LANG) or code
    try:
        return template.format(**params)
    except Exception:
        return template


def format_all(errors, lang: str = DEFAULT_LANG) -> list:
    """Render a list of entries (structured dicts or plain strings) as
    plain-text lines, in order."""
    out = []
    for e in errors:
        if isinstance(e, dict) and "code" in e:
            out.append(format_message(e["code"], e.get("params"), lang))
        else:
            out.append(str(e))
    return out
