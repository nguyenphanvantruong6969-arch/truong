/* ==========================================================================
   i18n.js — bilingual (vi/en) text catalog + helpers for the kiosk UI.
   ==========================================================================
   ERROR_MESSAGES MUST stay in sync with MESSAGES in i18n_errors.py (a
   Python test asserts every code() the backend can emit exists here with
   both langs — but this file itself isn't covered by that test, so any
   edit here needs its mirror edited in i18n_errors.py too).
   UI_STRINGS covers every other string the app shows: static HTML text
   (via data-i18n[-placeholder|-html] attributes, applied by
   applyStaticText()) and dynamic text app.js builds at runtime (via
   I18N.t(key, params)).
   ========================================================================== */

(function (global) {
  "use strict";

  const ERROR_MESSAGES = {
    error_reading_last_run: {
      vi: "Lỗi đọc thông tin lần chạy gần nhất: {detail}",
      en: "Error reading last run info: {detail}",
    },
    error_reading_dashboard: {
      vi: "Lỗi đọc trạng thái tổng quan: {detail}",
      en: "Error reading dashboard status: {detail}",
    },
    error_checking_integrity: {
      vi: "Lỗi khi kiểm tra dữ liệu: {detail}",
      en: "Error checking data integrity: {detail}",
    },
    error_checking_run_warning: {
      vi: "Lỗi kiểm tra trạng thái trước khi chạy: {detail}",
      en: "Error checking pre-run status: {detail}",
    },
    error_reading_stb_lock: {
      vi: "Lỗi đọc trạng thái khoá số bốc thăm: {detail}",
      en: "Error reading STB lock status: {detail}",
    },
    error_reading_run_history: {
      vi: "Lỗi đọc nhật ký chạy: {detail}",
      en: "Error reading run history: {detail}",
    },
    error_running_pipeline: {
      vi: "Lỗi không xác định khi chạy phân bổ: {detail}",
      en: "Unexpected error while running the pipeline: {detail}",
    },
    error_reading_csv_preview: {
      vi: "Lỗi đọc trước CSV: {detail}",
      en: "Error previewing CSV: {detail}",
    },
    error_importing_preferences_csv: {
      vi: "Lỗi nhập CSV nguyện vọng: {detail}",
      en: "Error importing preferences CSV: {detail}",
    },
    error_importing_test_selection_csv: {
      vi: "Lỗi nhập CSV chọn CLB thi: {detail}",
      en: "Error importing test-selection CSV: {detail}",
    },
    error_reading_scoring_overview: {
      vi: "Lỗi đọc tổng quan chấm điểm: {detail}",
      en: "Error reading scoring overview: {detail}",
    },
    error_reading_scoring_list: {
      vi: "Lỗi đọc danh sách chấm điểm: {detail}",
      en: "Error reading scoring list: {detail}",
    },
    error_saving_scores: {
      vi: "Lỗi lưu điểm: {detail}",
      en: "Error saving scores: {detail}",
    },
    error_reading_results: {
      vi: "Lỗi đọc kết quả: {detail}",
      en: "Error reading results: {detail}",
    },
    error_detecting_csv_kind: {
      vi: "Lỗi nhận diện loại tệp CSV: {detail}",
      en: "Error detecting CSV kind: {detail}",
    },
    error_importing_csv_auto: {
      vi: "Lỗi nhập CSV: {detail}",
      en: "CSV import failed: {detail}",
    },
    error_importing_clubs_csv: {
      vi: "Lỗi nhập CSV danh sách CLB: {detail}",
      en: "Error importing club list CSV: {detail}",
    },
    csv_kind_ambiguous: {
      vi: "Chưa xác định được đây là tệp gì. Bộ cột {fieldnames} vừa có thể là chọn CLB muốn thi, vừa có thể là xếp hạng nguyện vọng. Hãy chọn giúp loại tệp, hoặc thêm cột rank nếu đây là nguyện vọng.",
      en: "Cannot tell what this file is. The columns {fieldnames} could be either club test selection or ranked preferences. Please pick the kind, or add a rank column if these are preferences.",
    },
    csv_kind_unknown: {
      vi: "Không nhận ra định dạng tệp. Xem mau_csv/HUONG_DAN_CSV.md để biết các cột phần mềm đọc được.",
      en: "Unrecognised file format. See mau_csv/HUONG_DAN_CSV.md for the columns the app can read.",
    },
    csv_club_row_invalid: {
      vi: "Dòng {line}: bỏ qua vì {reason} không hợp lệ (chỉ tiêu phải lớn hơn 0 và chỉ tiêu dự trữ không được vượt quá tổng chỉ tiêu).",
      en: "Line {line}: skipped because {reason} is invalid (capacity must be above 0 and reserve capacity cannot exceed capacity).",
    },
    xlsx_read_failed: {
      vi: "Không đọc được tệp Excel: {detail}. Kiểm tra lại xem đúng là tệp .xlsx không, hoặc lưu lại rồi thử lần nữa.",
      en: "Could not read the Excel file: {detail}. Check it really is an .xlsx file, or re-save it and try again.",
    },
    xlsx_empty: {
      vi: "Tệp Excel không có dữ liệu nào.",
      en: "The Excel file has no data.",
    },
    xlsx_support_missing: {
      vi: "Bản cài này thiếu thư viện đọc Excel (openpyxl). Hãy lưu tệp sang định dạng CSV UTF-8 rồi nạp lại.",
      en: "This build is missing the Excel reader (openpyxl). Save the file as CSV UTF-8 and try again.",
    },
    csv_reserve_group_unknown: {
      vi: "Nhãn dự trữ {reserve_group} ({n} học sinh) không CLB nào nhận — các em này sẽ KHÔNG được xét diện dự trữ. Có phải bạn định ghi {goi_y}?",
      en: "Reserve label {reserve_group} ({n} student(s)) is not used by any club — they will NOT be considered for reserve places. Did you mean {goi_y}?",
    },
    csv_duplicate_student_rows: {
      vi: "Mã {student_id} xuất hiện {n} lần trong tệp — chỉ dòng CUỐI được giữ, các dòng trước bị ghi đè. Kiểm tra lại nếu đó không phải ý bạn.",
      en: "Student {student_id} appears {n} times in the file — only the LAST row is kept and the earlier ones are overwritten. Check this is intended.",
    },
    csv_score_not_a_number: {
      vi: "Điểm “{score}” của học sinh {student_id} ở CLB {club_id} không phải số — ô điểm đó bị bỏ qua, các lựa chọn thi vẫn được giữ. Sửa lại rồi nạp lại tệp.",
      en: "Score “{score}” for student {student_id} at club {club_id} is not a number — that one score is skipped, the test selections are kept. Fix it and re-import.",
    },
    csv_score_negative: {
      vi: "Điểm “{score}” của học sinh {student_id} ở CLB {club_id} là số ÂM — gần như chắc chắn thừa dấu trừ. Ô điểm đó bị bỏ qua.",
      en: "Score “{score}” for student {student_id} at club {club_id} is NEGATIVE — almost certainly a stray minus sign. That score is skipped.",
    },
    csv_score_for_unselected_club: {
      vi: "Học sinh {student_id} có điểm cho CLB {club_id} nhưng KHÔNG đăng ký thi CLB đó — điểm bị bỏ qua. Kiểm tra xem có gõ nhầm mã CLB không.",
      en: "Student {student_id} has a score for club {club_id} but did not register to test for it — the score is skipped. Check for a mistyped club id.",
    },
    csv_score_without_club: {
      vi: "Học sinh {student_id} có điểm ở cột {cot} nhưng ô mã CLB cùng số thứ tự lại để trống — nhiều khả năng gõ lệch cột. Điểm đó bị bỏ qua.",
      en: "Student {student_id} has a score in column {cot} but the club column with the same number is empty — the columns are probably misaligned. That score is skipped.",
    },
    csv_scores_ignored_here: {
      vi: "Tệp này có cột điểm, nhưng đây là tệp XẾP HẠNG NGUYỆN VỌNG — điểm KHÔNG được nạp từ đây. Đưa cột điểm sang tệp chọn CLB muốn thi.",
      en: "This file has score columns, but it is a PREFERENCE ranking file — scores are NOT imported from here. Move the score columns into the club test-selection file.",
    },
    csv_student_id_case_conflict: {
      vi: "Mã {student_id} chỉ khác chữ hoa/thường so với mã {da_co} — phần mềm đang coi đây là HAI học sinh khác nhau. Nếu là một người, hãy sửa cho hai tệp dùng cùng một kiểu viết.",
      en: "Student id {student_id} differs from {da_co} only in case — these are being treated as TWO different students. If they are the same person, make both files use the same spelling.",
    },
    csv_student_id_maybe_truncated: {
      vi: "Mã {student_id} chỉ dài {do_dai} chữ số, trong khi phần lớn mã trong tệp dài {do_dai_pho_bien} — nhiều khả năng Excel đã cắt mất số 0 ở đầu. Mở tệp gốc, đặt định dạng cột mã là Text rồi nhập lại.",
      en: "Student id {student_id} has only {do_dai} digits while most ids in the file have {do_dai_pho_bien} — Excel has most likely stripped leading zeros. Reopen the source file, set the id column to Text, and re-import.",
    },
    error_reading_club_stats: {
      vi: "Lỗi đọc thống kê CLB: {detail}",
      en: "Error reading club stats: {detail}",
    },
    error_exporting_csv: {
      vi: "Lỗi xuất CSV: {detail}",
      en: "Error exporting CSV: {detail}",
    },
    error_saving_club: {
      vi: "Lỗi lưu CLB: {detail}",
      en: "Error saving club: {detail}",
    },
    error_deleting_club: {
      vi: "Lỗi xoá CLB: {detail}",
      en: "Error deleting club: {detail}",
    },
    error_reading_reserve_groups: {
      vi: "Lỗi đọc danh sách nhãn dự trữ: {detail}",
      en: "Error reading reserve groups: {detail}",
    },
    error_assigning_reserve_group: {
      vi: "Lỗi gán nhãn dự trữ: {detail}",
      en: "Error assigning reserve group: {detail}",
    },
    error_bulk_assigning: {
      vi: "Lỗi gán hàng loạt: {detail}",
      en: "Error bulk-assigning: {detail}",
    },
    error_reading_student_list: {
      vi: "Lỗi đọc danh sách học sinh: {detail}",
      en: "Error reading student list: {detail}",
    },
    error_reading_club_list: {
      vi: "Lỗi đọc danh sách CLB: {detail}",
      en: "Error reading club list: {detail}",
    },
    error_searching_students: {
      vi: "Lỗi tìm học sinh: {detail}",
      en: "Error searching students: {detail}",
    },
    error_reading_student_state: {
      vi: "Lỗi đọc trạng thái học sinh: {detail}",
      en: "Error reading student state: {detail}",
    },
    error_saving_test_selection: {
      vi: "Lỗi ghi lựa chọn thi: {detail}",
      en: "Error saving test selection: {detail}",
    },
    error_saving_preferences: {
      vi: "Lỗi ghi nguyện vọng: {detail}",
      en: "Error saving preferences: {detail}",
    },
    error_creating_student: {
      vi: "Lỗi tạo học sinh: {detail}",
      en: "Error creating student: {detail}",
    },
    error_resetting_student_entry: {
      vi: "Lỗi xoá lựa chọn để nhập lại: {detail}",
      en: "Error resetting student entry: {detail}",
    },
    error_deleting_student: {
      vi: "Lỗi xoá học sinh: {detail}",
      en: "Error deleting student: {detail}",
    },
    reset_confirmation_mismatch: {
      vi: "Chưa xoá gì cả — thiếu xác nhận. Muốn xoá thật thì phải gửi đúng chữ \"{can_go}\".",
      en: "Nothing was deleted — confirmation missing. A real reset must send exactly \"{can_go}\".",
    },
    reset_scope_unknown: {
      vi: "Chưa xoá gì cả — không hiểu phạm vi \"{pham_vi}\". Chỉ nhận: {hop_le}.",
      en: "Nothing was deleted — unknown scope \"{pham_vi}\". Accepted values: {hop_le}.",
    },
    error_resetting_data: {
      vi: "Lỗi khi xoá dữ liệu: {detail}. Bản sao lưu (nếu đã tạo) vẫn nằm cạnh app.db.",
      en: "Error resetting data: {detail}. The backup, if one was made, is still beside app.db.",
    },
    csv_empty: {
      vi: "Tệp CSV rỗng hoặc không đọc được dòng nào.",
      en: "The CSV file is empty, or no rows could be read.",
    },
    csv_missing_columns: {
      vi: "CSV dạng \"dài\" cần có cột student_id và club_id (cột hiện có: {fieldnames})",
      en: "\"Long\" format CSV needs student_id and club_id columns (columns found: {fieldnames})",
    },
    capacity_must_be_positive: {
      vi: "Tổng chỗ (capacity) phải > 0",
      en: "Capacity must be greater than 0",
    },
    reserve_capacity_exceeds_capacity: {
      vi: "Suất dự trữ không được lớn hơn tổng chỗ",
      en: "Reserve capacity cannot exceed total capacity",
    },
    club_id_required: {
      vi: "Cần nhập mã CLB",
      en: "Club ID is required",
    },
    cannot_delete_club_referenced: {
      vi: "Không thể xoá: CLB {club_id} đã có {n_prefs} nguyện vọng và {n_matches} kết quả tham chiếu tới. Phải xử lý dữ liệu liên quan trước.",
      en: "Cannot delete: club {club_id} is referenced by {n_prefs} preference(s) and {n_matches} match result(s). Handle the related data first.",
    },
    student_not_found: {
      vi: "Học sinh {student_id} không tồn tại",
      en: "Student {student_id} does not exist",
    },
    club_not_found: {
      vi: "CLB {club_id} không tồn tại",
      en: "Club {club_id} does not exist",
    },
    unknown_clubs: {
      vi: "CLB không tồn tại: {club_ids}",
      en: "Unknown club(s): {club_ids}",
    },
    scores_must_be_nonempty_list: {
      vi: "scores phải là danh sách không rỗng",
      en: "scores must be a non-empty list",
    },
    student_ids_must_be_nonempty_list: {
      vi: "student_ids phải là danh sách không rỗng",
      en: "student_ids must be a non-empty list",
    },
    club_ids_must_be_list: {
      vi: "club_ids phải là danh sách",
      en: "club_ids must be a list",
    },
    ordered_club_ids_must_be_list: {
      vi: "ordered_club_ids phải là danh sách",
      en: "ordered_club_ids must be a list",
    },
    must_rank_at_least_one: {
      vi: "Phải xếp hạng ít nhất 1 nguyện vọng",
      en: "You must rank at least 1 preference",
    },
    max_10_preferences: {
      vi: "Tối đa 10 nguyện vọng",
      en: "Maximum 10 preferences",
    },
    duplicate_preference_in_list: {
      vi: "Danh sách nguyện vọng có CLB trùng lặp",
      en: "The preference list has a duplicate club",
    },
    cannot_delete_student_matched: {
      vi: "Không thể xoá: học sinh {student_id} đã có trong kết quả của lần chạy phân bổ gần nhất. Hãy chạy lại phân bổ sau khi xử lý.",
      en: "Cannot delete: student {student_id} is already in the results of the latest pipeline run. Re-run the pipeline after handling this.",
    },
    stb_redrawn_and_locked: {
      vi: "Đã vẽ mới số bốc thăm (STB) cho {n} học sinh và khoá lại.",
      en: "Drew new STB numbers for {n} student(s) and locked them.",
    },
    stb_supplemented: {
      vi: "Số bốc thăm đã khoá — giữ nguyên thứ tự các em cũ, chèn ngẫu nhiên {n} học sinh mới vào dàn số.",
      en: "Lottery already locked — kept the existing students' relative order, inserted {n} new student(s) at random positions.",
    },
    stb_reused: {
      vi: "Số bốc thăm đã khoá — tái sử dụng toàn bộ số cũ, không vẽ lại.",
      en: "STB already locked — reused all existing numbers, no redraw.",
    },
    rbda_done: {
      vi: "{rounds} vòng lặp, không lỗi",
      en: "{rounds} round(s), no errors",
    },
    db_backed_up: {
      vi: "Đã sao lưu app.db trước khi chạy: {backup_name}",
      en: "Backed up app.db before running: {backup_name}",
    },
    db_backup_failed: {
      vi: "Không sao lưu được app.db (việc phân bổ vẫn tiếp tục chạy): {detail}",
      en: "Could not back up app.db (pipeline still continues): {detail}",
    },
    pipeline_rolled_back: {
      vi: "Đã huỷ toàn bộ thay đổi của lần chạy này (kể cả số bốc thăm vừa vẽ, nếu có) do lỗi giữa chừng — dữ liệu quay lại đúng trạng thái trước khi bấm chạy.",
      en: "Rolled back every change from this run (including any freshly drawn STB numbers) because of a mid-run error — data is back to exactly the state before you clicked run.",
    },
    pref_student_not_in_students: {
      vi: "Học sinh {student_id} có nguyện vọng nhưng không có trong students",
      en: "Student {student_id} has preferences but is not in students",
    },
    pref_duplicate_club: {
      vi: "Học sinh {student_id} có CLB trùng lặp trong danh sách nguyện vọng",
      en: "Student {student_id} has a duplicate club in their preference list",
    },
    pref_too_many: {
      vi: "Học sinh {student_id} có hơn 10 nguyện vọng (vượt giới hạn Microsoft Forms)",
      en: "Student {student_id} has more than 10 preferences (exceeds the Microsoft Forms limit)",
    },
    pref_unknown_club: {
      vi: "Học sinh {student_id} xếp hạng CLB không tồn tại: {club_id}",
      en: "Student {student_id} ranked a club that does not exist: {club_id}",
    },
    club_capacity_not_positive: {
      vi: "CLB {club_id} có capacity <= 0",
      en: "Club {club_id} has capacity <= 0",
    },
    club_reserve_exceeds_capacity: {
      vi: "CLB {club_id} có reserve_capacity > capacity",
      en: "Club {club_id} has reserve_capacity > capacity",
    },
    applicants_unknown_club: {
      vi: "Danh sách đăng ký thi tham chiếu tới CLB không tồn tại: {club_id}",
      en: "applicants references a club that does not exist: {club_id}",
    },
    applicants_unknown_student: {
      vi: "applicants tham chiếu học sinh không tồn tại: {student_id}",
      en: "applicants references a student that does not exist: {student_id}",
    },
    assignment_not_in_preferences: {
      vi: "{student_id} được xếp vào {club_id} nhưng không có trong nguyện vọng",
      en: "{student_id} was assigned to {club_id} but it is not in their preferences",
    },
    club_over_capacity: {
      vi: "CLB {club_id} vượt capacity: {count}/{capacity}",
      en: "Club {club_id} exceeds capacity: {count}/{capacity}",
    },
    club_over_reserve_capacity: {
      vi: "CLB {club_id} vượt reserve_capacity ở tier dự trữ: {count}/{reserve_capacity}",
      en: "Club {club_id} exceeds reserve_capacity in the reserve tier: {count}/{reserve_capacity}",
    },
    blocking_pair: {
      vi: "Blocking pair: {student_id} thích {club_id} hơn {current_club}, và sẽ được nhận nếu áp dụng lại club_choice_function (hiện có {n_holders}/{capacity} chỗ)",
      en: "Blocking pair: {student_id} prefers {club_id} over {current_club}, and would be accepted if club_choice_function were re-applied (currently {n_holders}/{capacity} seats held)",
    },
    csv_pref_duplicate_deduped: {
      vi: "{student_id}: có CLB trùng lặp trong nguyện vọng, đã tự động loại bỏ trùng.",
      en: "{student_id}: had a duplicate club in preferences; duplicates were removed automatically.",
    },
    csv_pref_too_many_skipped: {
      vi: "{student_id}: có {count} nguyện vọng (>10), CHƯA nhập — bỏ qua học sinh này.",
      en: "{student_id}: has {count} preferences (>10), NOT imported — this student was skipped.",
    },
    csv_unknown_clubs_skipped: {
      vi: "{student_id}: CLB không tồn tại {club_ids} — bỏ qua học sinh này.",
      en: "{student_id}: unknown club(s) {club_ids} — this student was skipped.",
    },
    csv_student_missing_skipped: {
      vi: "{student_id}: chưa có trong hệ thống, bỏ qua (create_missing_students=False).",
      en: "{student_id}: not yet in the system, skipped (create_missing_students=False).",
    },
    score_not_applicant: {
      vi: "{student_id}: không nằm trong danh sách thi/xét CLB này",
      en: "{student_id}: is not registered to test/apply for this club",
    },
    score_not_a_number: {
      vi: "{student_id}: điểm '{score}' không phải số",
      en: "{student_id}: score '{score}' is not a number",
    },
    score_negative: {
      vi: "{student_id}: điểm '{score}' là số ÂM — gần như chắc chắn thừa dấu trừ. Ô điểm đó KHÔNG được lưu.",
      en: "{student_id}: score '{score}' is NEGATIVE — almost certainly a stray minus sign. That score was NOT saved.",
    },
    health_scoring_none: {
      vi: "CLB {club_id}: có {n_applicants} học sinh đăng ký thi nhưng CHƯA CHẤM ĐIỂM AI. Toàn bộ các em này sẽ rơi xuống Tầng 2 và chỉ được xét bằng số bốc thăm — vòng thi coi như không có tác dụng.",
      en: "Club {club_id}: {n_applicants} student(s) registered for the tryout but NOBODY has been scored. All of them drop to Tier 2 and will be decided by lottery only — the tryout will have no effect.",
    },
    health_scoring_partial: {
      vi: "CLB {club_id}: mới chấm {n_scored}/{n_applicants} học sinh. {n_missing} em chưa có điểm sẽ bị xếp dưới TẤT CẢ các em đã có điểm, kể cả em điểm thấp nhất.",
      en: "Club {club_id}: only {n_scored} of {n_applicants} scored. The {n_missing} unscored student(s) will rank below EVERY scored student, including the lowest-scoring one.",
    },
    health_tested_not_ranked: {
      vi: "{n} lượt đăng ký thi sẽ bị bỏ phí: học sinh đã đăng ký thi một CLB nhưng không xếp CLB đó vào nguyện vọng, nên dù điểm cao vẫn không thể được xếp vào đó. Ví dụ: {sample}",
      en: "{n} tryout registration(s) will be wasted: the student registered to test for a club but did not rank it, so no matter how well they score they cannot be placed there. For example: {sample}",
    },
    health_student_no_preferences: {
      vi: "{n} học sinh chưa xếp nguyện vọng nào — các em này chắc chắn không được xếp vào CLB nào. Ví dụ: {sample}",
      en: "{n} student(s) have not ranked any preference — they cannot be placed in any club. For example: {sample}",
    },
    health_orphan_student_group: {
      vi: "Nhãn dự trữ \"{reserve_group}\" đang gán cho {n} học sinh nhưng KHÔNG CLB nào dùng nhãn này. Ví dụ: {sample}. Các em đó sẽ không được ưu tiên ở đâu cả — kiểm tra xem có gõ sai chính tả không. Sửa ở thẻ Quản lý: tìm mã em, đánh dấu, để trống ô nhãn rồi bấm \"Gán cho học sinh đã đánh dấu\".",
      en: "Reserve label \"{reserve_group}\" is assigned to {n} student(s) but NO club uses it. For example: {sample}. Those students get no priority anywhere — check for a typo. Fix it in the Admin tab: search for the student id, tick it, leave the label box empty and click \"Apply to ticked students\".",
    },
    health_club_reserve_no_group: {
      vi: "CLB {club_id} có {reserve_capacity} suất dự trữ nhưng chưa đặt nhãn dự trữ. Các suất này sẽ âm thầm chuyển thành suất phổ thông.",
      en: "Club {club_id} has {reserve_capacity} reserve seat(s) but no reserve label set. Those seats will silently become general seats.",
    },
    health_club_group_no_students: {
      vi: "CLB {club_id} dành {reserve_capacity} suất cho nhãn \"{reserve_group}\", nhưng chưa học sinh nào mang nhãn đó. Suất dự trữ sẽ không dùng đến.",
      en: "Club {club_id} reserves {reserve_capacity} seat(s) for label \"{reserve_group}\", but no student carries that label. The reserve seats will go unused.",
    },
    health_score_outlier: {
      vi: "CLB {club_id}: có {n} điểm lệch hẳn khỏi các điểm còn lại (trung vị của CLB này là {trung_vi}). Ví dụ: {sample}. Gõ 70 thay vì 7.0 là chuyện thường gặp, và điểm sai đẩy em đó lên đầu bảng — kéo theo cả những em khác tụt xuống. Kiểm tra lại ở thẻ Chấm điểm.",
      en: "Club {club_id}: {n} score(s) sit far outside the rest (this club's median is {trung_vi}). For example: {sample}. Typing 70 instead of 7.0 is a common slip, and a wrong score pushes that student to the top of the ranking — displacing others in turn. Check them on the Scoring tab.",
    },
    health_oversubscribed: {
      vi: "Tổng chỗ toàn hệ thống là {n_seats}, trong khi có {n_students} học sinh đã nộp nguyện vọng. Ít nhất {n_short} em chắc chắn không có chỗ.",
      en: "Total seats across all clubs is {n_seats}, but {n_students} student(s) have submitted preferences. At least {n_short} student(s) cannot be placed.",
    },
    recovery_no_backups: {
      vi: "Không tìm thấy bản sao lưu nào — có thể chưa từng chạy phân bổ lần nào trên máy này, hoặc thư mục sao lưu đã bị xoá.",
      en: "No backups found — the pipeline may never have run on this machine, or the backup folder was deleted.",
    },
    recovery_all_backups_corrupt: {
      vi: "Đã thử cả {n_tried} bản sao lưu tìm thấy nhưng không bản nào đọc được nguyên vẹn.",
      en: "Tried all {n_tried} backup(s) found, but none of them could be read intact.",
    },
    recovery_restore_failed: {
      vi: "Khôi phục thất bại: {detail}",
      en: "Restore failed: {detail}",
    },
    recovery_restored_from: {
      vi: "Đã khôi phục từ bản sao lưu {backup_name} (bỏ qua {n_skipped} bản mới hơn vì đọc không được).",
      en: "Restored from backup {backup_name} (skipped {n_skipped} newer backup(s) that could not be read).",
    },
    recovery_fresh_created: {
      vi: "Đã tạo app.db mới hoàn toàn trống. Tệp cũ được đổi tên (không xoá), nằm cùng thư mục.",
      en: "Created a brand-new, empty app.db. The old file was renamed (not deleted) and is in the same folder.",
    },
  };

  const UI_STRINGS = {
    vi: {
      page_title: "Phân bổ Câu lạc bộ — RB-DA",
      lang_toggle_label: "EN",
      brand_title: "Phân bổ CLB",
      brand_sub: "Reserve-Based DA",
      nav_pipeline: "Vận hành phân bổ",
      nav_results: "Kết quả",
      nav_fallback: "Nhập dự phòng",
      nav_admin: "Quản lý CLB & dự trữ",
      nav_scoring: "Chấm điểm (mù)",
      db_status_loading: "— đang tải —",
      db_connected: "Đã kết nối app.db",
      backend_dang_ket_noi: "Đang kết nối với phần lõi chương trình…",
      backend_khong_ket_noi: "Chưa kết nối được app.db",
      backend_qua_han: "Không kết nối được với phần lõi chương trình. Hãy đóng cửa sổ rồi mở lại chương trình. Nếu vẫn vậy, gửi tệp loi_khoi_dong.txt (nằm cùng thư mục với app.db) cho người phụ trách — tệp đó ghi rõ chương trình đã hỏng ở bước nào.",
      display_native: "Cửa sổ ứng dụng riêng",
      display_browser: "Chế độ dự phòng (trình duyệt)",
      last_run_line: "Chạy gần nhất: {run_at} (hạt giống {seed}, {n_matched}/{n_total} xếp được)",
      never_run: "Chưa chạy phân bổ lần nào",

      pipeline_title: "Vận hành phân bổ",
      pipeline_desc: "Kiểm tra dữ liệu, sinh số bốc thăm, chạy thuật toán RB-DA và xuất kết quả.",
      label_students: "học sinh",
      label_clubs: "CLB",
      label_submitted_prefs: "đã nộp nguyện vọng",
      label_matched: "đã xếp CLB",
      import_panel_title: "Nhập dữ liệu",
      import_hint_html: "Nhận tệp CSV đã chuẩn hoá bởi <code>06_ms_forms_transform.py</code>. Hệ thống tự nhận diện định dạng \"dài\" hoặc \"rộng\" — không cần chọn.",
      import_col_test_title: "CSV chọn CLB muốn thi/xét (Bước 1)",
      import_col_pref_title: "CSV xếp hạng nguyện vọng (Bước 2)",
      btn_import_confirm: "Nhập vào hệ thống",
      import_hint: "Kéo thả tệp Excel (.xlsx) hoặc CSV vào ô dưới — phần mềm tự biết đó là danh sách CLB, tệp chọn CLB muốn thi hay tệp xếp hạng nguyện vọng. Thả được nhiều tệp một lúc, và tự nhập theo đúng thứ tự.",
      drop_zone_main: "Kéo tệp Excel hoặc CSV vào đây",
      drop_zone_sub: "nhận .xlsx và .csv — bấm để chọn, có thể chọn nhiều tệp",
      btn_import_all: "Nhập tất cả",
      btn_clear_queue: "Bỏ danh sách",
      csv_kind_clubs: "Danh sách CLB",
      csv_kind_test_selection: "Chọn CLB muốn thi",
      csv_kind_preferences: "Xếp hạng nguyện vọng",
      csv_kind_unknown_label: "Chưa rõ",
      queue_detected: "Nhận diện: {kind}",
      queue_ambiguous: "Chưa chắc đây là tệp gì — bộ cột này hợp với cả hai loại. Chọn giúp ở ô bên phải.",
      queue_unknown: "Không nhận ra định dạng. Xem mau_csv/HUONG_DAN_CSV.md để biết các cột phần mềm đọc được.",
      queue_pick_kind: "— chọn loại tệp —",
      queue_result_clubs: "Xong: {n_created} CLB mới, {n_updated} cập nhật, {n_skipped} dòng bỏ qua",
      queue_result_students: "Xong: {n_written} học sinh ghi dữ liệu, {n_created} tạo mới, {n_skipped} bỏ qua",
      feedback_import_done: "Đã nhập xong {n} tệp",
      steps_panel_title: "5 bước xử lý",
      label_seed: "Hạt giống bốc thăm (seed)",
      btn_validate: "Kiểm tra dữ liệu",
      btn_run_pipeline: "Chạy phân bổ",
      step_title_validate: "Kiểm tra toàn vẹn dữ liệu",
      step_title_stb: "Sinh số bốc thăm (STB)",
      step_title_rbda: "Chạy vòng lặp RB-DA",
      step_title_write: "Ghi kết quả vào cơ sở dữ liệu",
      step_title_export: "Xuất tệp CSV",
      step_not_run_yet: "Chưa chạy",
      step_running: "Đang chạy…",
      step_done_default: "Hoàn tất",
      generic_error: "Lỗi",
      error_log_title: "Nhật ký lỗi",
      history_panel_title: "Lịch sử chạy phân bổ",
      btn_toggle: "Hiện/ẩn",
      th_time: "Thời điểm",
      th_seed: "Hạt giống",
      th_rounds: "Vòng lặp",
      th_matched_count: "Đã xếp",
      th_total: "Tổng",
      th_redrawn: "Bốc thăm lại?",
      history_empty: "Chưa có lần chạy nào.",
      yes: "Có",
      no: "Không",

      results_title: "Kết quả phân bổ",
      results_desc: "Danh sách học sinh đã được xếp CLB và tình trạng lấp đầy từng CLB.",
      fill_panel_title: "Tỉ lệ lấp đầy theo CLB",
      legend_general: "Tổng quát",
      legend_reserve: "Vào bằng suất dự trữ",
      results_list_title: "Danh sách xếp CLB",
      placeholder_results_search: "Tìm theo mã hoặc tên học sinh…",
      btn_export_csv: "Xuất CSV",
      th_student_id: "Mã học sinh",
      th_name: "Họ tên",
      th_club: "Câu lạc bộ",
      th_tier: "Diện",
      th_pref_rank: "Nguyện vọng",
      results_empty_state: "Chưa có kết quả — chạy phân bổ ở thẻ \"Vận hành phân bổ\" trước.",
      not_matched_label: "Không xếp được",
      unmatched_badge: "{n} chưa xếp được CLB",
      tier_general: "Tổng quát",
      tier_reserve: "Dự trữ",

      fallback_title: "Nhập dự phòng tại chỗ",
      fallback_desc: "Dùng khi học sinh không thể nộp qua Microsoft Forms. Hai bước tách biệt — chọn CLB để thi và xếp hạng nguyện vọng — không ảnh hưởng lẫn nhau.",
      fallback_step0_title: "Bước 0 — Tìm hoặc tạo học sinh",
      placeholder_fallback_search: "Nhập mã học sinh hoặc tên…",
      btn_search: "Tìm",
      placeholder_new_student_id: "Mã học sinh mới",
      placeholder_full_name: "Họ tên",
      btn_create_student: "Tạo học sinh mới",
      btn_reset_entry: "Sửa lại từ đầu",
      confirm_reset_entry: "Bấm lần nữa để xoá hết & nhập lại",
      btn_delete_student: "Xoá học sinh",
      confirm_delete_student: "Bấm lần nữa để xoá học sinh",
      fallback_step1_title: "Bước 1 — Chọn CLB muốn thi / xét (ô đánh dấu)",
      btn_save_test_selection: "Lưu lựa chọn thi",
      fallback_step2_title: "Bước 2 — Xếp hạng nguyện vọng (độc lập, tối đa 10 CLB)",
      fallback_step2_hint: "Bấm chọn CLB theo thứ tự ưu tiên giảm dần. Có thể xếp hạng CLB không nằm trong danh sách đã đánh dấu ở Bước 1.",
      ranking_current_label: "Thứ tự nguyện vọng hiện tại:",
      btn_clear_all: "Xoá hết",
      btn_save_preferences: "Lưu nguyện vọng",
      btn_remove_ranked: "xoá",
      search_no_students_found: "Không tìm thấy học sinh nào.",
      toast_need_id_and_name: "Cần nhập cả mã học sinh và họ tên.",
      toast_student_created: "Đã tạo học sinh mới.",
      toast_student_exists: "Học sinh đã tồn tại — mở hồ sơ.",
      feedback_test_selection_saved: "Đã lưu {n} lựa chọn.",
      feedback_preferences_saved: "Đã lưu {n} nguyện vọng.",
      toast_reset_done: "Đã xoá lựa chọn thi và nguyện vọng — nhập lại từ đầu.",
      toast_student_deleted: "Đã xoá học sinh {student_id}.",
      toast_delete_failed_prefix: "Không xoá được: {errors}",
      feedback_error_prefix: "Lỗi: {errors}",

      admin_title: "Quản lý CLB & diện dự trữ",
      admin_desc: "Tạo/sửa CLB và gán diện dự trữ cho học sinh. Tiêu chí dự trữ hoàn toàn do trường tự đặt — hệ thống chỉ so khớp nhãn (reserve_group) giữa CLB và học sinh, không cài cứng quy tắc nào.",
      admin_club_form_title: "Thêm / sửa CLB",
      placeholder_club_id: "Mã CLB (vd: clb_01)",
      placeholder_club_name: "Tên CLB",
      placeholder_capacity: "Tổng chỗ",
      placeholder_reserve_capacity: "Suất dự trữ",
      placeholder_reserve_group: "Nhãn dự trữ (bỏ trống nếu không có)",
      btn_save_club: "Lưu CLB",
      th_club_id: "Mã CLB",
      th_name_short: "Tên",
      th_capacity: "Tổng chỗ",
      th_reserve_capacity: "Suất dự trữ",
      th_reserve_group: "Nhãn dự trữ",
      admin_club_empty: "Chưa có CLB nào — thêm CLB đầu tiên bằng biểu mẫu ở trên.",
      admin_reserve_assign_title: "Gán diện dự trữ cho học sinh",
      placeholder_admin_student_search: "Tìm học sinh theo mã hoặc tên…",
      placeholder_reserve_group_apply: "Nhãn dự trữ áp dụng",
      btn_bulk_assign: "Gán cho học sinh đã đánh dấu",
      th_current_reserve_group: "Nhãn dự trữ hiện tại",
      admin_student_empty: "Chưa có học sinh nào trong hệ thống — thêm qua thẻ \"Nhập dự phòng\" hoặc nạp từ Microsoft Forms.",
      btn_prev_page: "‹ Trước",
      btn_next_page: "Sau ›",
      pagination_label: "Trang {page}/{total_pages} — tổng {total} học sinh",
      btn_delete: "Xoá",
      confirm_delete_generic: "Bấm lần nữa để xoá",
      toast_club_deleted: "Đã xoá CLB {club_id}",

      danger_zone_title: "Vùng nguy hiểm — xoá dữ liệu để làm lại từ đầu",
      danger_zone_desc: "Nạp tệp chỉ CỘNG THÊM học sinh, không xoá em cũ. Muốn chạy thử lại từ đầu với bộ dữ liệu khác thì xoá ở đây, nếu không học sinh của lần trước vẫn chiếm suất và làm lệch kết quả.",
      danger_zone_safety: "Cả hai nút đều TỰ SAO LƯU app.db trước khi xoá, và đều KHÔNG xoá nhật ký các lần chạy (run_history) — dấu vết kiểm toán được giữ nguyên.",
      btn_reset_students: "Xoá toàn bộ học sinh (giữ CLB)",
      btn_reset_all: "Xoá toàn bộ dữ liệu (cả CLB)",
      confirm_reset_students: "Bấm lần nữa để xoá TẤT CẢ học sinh",
      confirm_reset_all: "Bấm lần nữa để xoá TẤT CẢ dữ liệu",
      confirm_reset_students_has_results: "Bấm lần nữa — mất cả kết quả đã chạy",
      confirm_reset_all_has_results: "Bấm lần nữa — mất cả CLB và kết quả đã chạy",
      toast_reset_students_done: "Đã xoá {n_students} học sinh, giữ lại {n_clubs_left} CLB. Sao lưu: {backup_name}",
      toast_reset_all_done: "Đã xoá {n_students} học sinh và {n_clubs} CLB. Sao lưu: {backup_name}",
      feedback_club_form_required: "Cần nhập mã CLB, tên, và tổng chỗ.",
      feedback_club_saved: "Đã lưu CLB {club_id}",
      toast_no_students_ticked: "Chưa đánh dấu học sinh nào.",
      toast_bulk_assign_success: "Đã gán cho {n} học sinh.",

      scoring_title: "Chấm điểm (mù)",
      scoring_desc: "Chọn CLB để chấm. Danh sách chỉ hiện mã học sinh và họ tên — không hiện số bốc thăm hay thứ hạng nguyện vọng, đảm bảo người chấm không thể thiên vị theo ưu tiên đã biết trước.",
      scoring_overview_title: "Tiến độ theo CLB",
      th_n_applicants: "Số học sinh thi/xét",
      th_n_scored: "Đã chấm",
      scoring_overview_empty: "Chưa có CLB nào có học sinh đăng ký thi/xét.",
      btn_save_scores: "Lưu điểm",
      th_score: "Điểm",
      btn_score_link: "Chấm →",
      feedback_scores_saved: "Đã lưu điểm cho {n} học sinh.",

      toast_dashboard_read_failed: "Không đọc được trạng thái tổng quan: {errors}",
      stb_locked_label: "Số bốc thăm (STB) ĐÃ KHOÁ từ {locked_at} — các lần chạy sau giữ nguyên thứ tự các em đã có; học sinh mới được chèn ngẫu nhiên vào dàn số.",
      stb_unlocked_label: "Số bốc thăm (STB) chưa từng được vẽ — lần chạy đầu tiên sẽ vẽ và tự động khoá lại.",
      btn_redraw_stb: "Vẽ lại số bốc thăm…",
      toast_redraw_armed: "Bấm nút 'Chạy phân bổ' để vẽ lại số bốc thăm — sẽ cần xác nhận thêm 1 lần nữa trước khi chạy.",
      health_panel_title: "Cảnh báo dữ liệu",
      health_panel_hint: "Những thiếu sót vẫn cho chạy phân bổ được, nhưng âm thầm làm đổi kết quả. Kiểm tra trước khi chạy.",
      health_clean: "Không phát hiện vấn đề nào. Dữ liệu sẵn sàng để chạy.",
      health_summary: "{n} cảnh báo, trong đó {n_high} nghiêm trọng.",
      health_sev_high: "Nghiêm trọng",
      health_sev_medium: "Cần lưu ý",
      health_sev_info: "Thông tin",
      btn_health_recheck: "Kiểm tra lại",
      toast_data_valid: "Dữ liệu hợp lệ — {n_students} học sinh, {n_clubs} CLB.",
      toast_data_invalid: "Dữ liệu có lỗi — xem nhật ký bên dưới.",
      confirm_redraw_run: "Xác nhận: VẼ LẠI toàn bộ số bốc thăm và chạy lại phân bổ (ghi đè kết quả hiện tại)?",
      confirm_overwrite_run: "Đã có kết quả cũ — chạy lại sẽ GHI ĐÈ (vẫn lưu vào lịch sử để kiểm toán). Xác nhận?",
      btn_confirm_run: "Xác nhận chạy",
      btn_cancel: "Huỷ",
      toast_run_success: "Chạy phân bổ thành công — {n_matched}/{n_total} học sinh đã xếp CLB, {rounds} vòng lặp.",
      toast_run_failed: "Chạy phân bổ thất bại — xem nhật ký lỗi.",
      toast_csv_read_error_prefix: "Lỗi đọc CSV: {errors}",
      csv_format_wide: "rộng (1 dòng/học sinh)",
      csv_format_long: "dài (nhiều dòng/học sinh)",
      csv_preview_summary: "Định dạng nhận diện: <span class=\"preview-highlight\">{format}</span><br>{n_rows} dòng dữ liệu — {n_students_detected} học sinh, <span class=\"preview-highlight\">{n_new_students} học sinh mới</span> sẽ được tạo.",
      feedback_no_file_selected: "Chưa chọn tệp.",
      feedback_import_failed: "Nhập thất bại.",
      feedback_import_success: "Đã nhập: {n_written} học sinh ({n_created} mới, {n_skipped} bị bỏ qua).",
      toast_csv_import_success: "Nhập CSV thành công — {n_written} học sinh.",
      toast_export_success: "Đã xuất {n_rows} dòng ra {path} (kèm {n_club_files} tệp theo CLB)",
      toast_export_failed: "Xuất CSV thất bại: {errors}",

      recovery_title: "Phục hồi dữ liệu",
      recovery_heading: "Không thể mở cơ sở dữ liệu",
      recovery_intro: "Ứng dụng không khởi động được vì tệp app.db gặp sự cố. Dữ liệu chưa chắc đã mất — hãy thử các bước bên dưới trước khi liên hệ hỗ trợ.",
      recovery_error_detail_label: "Chi tiết lỗi kỹ thuật (để gửi cho người hỗ trợ nếu cần):",
      recovery_backups_label: "Các bản sao lưu tìm thấy trên máy này:",
      th_backup_name: "Tên tệp",
      th_backup_time: "Thời điểm sao lưu",
      th_backup_size: "Dung lượng",
      btn_restore_backup: "Khôi phục từ bản sao lưu gần nhất còn đọc được",
      btn_start_fresh: "Bắt đầu với cơ sở dữ liệu mới",
      confirm_start_fresh: "Bấm lần nữa để XÁC NHẬN — tệp hỏng sẽ được đổi tên, không mất hẳn",
      recovery_working: "Đang xử lý…",
      recovery_please_restart: "Vui lòng ĐÓNG và MỞ LẠI ứng dụng để tiếp tục.",
    },

    en: {
      page_title: "Club Allocation — RB-DA",
      lang_toggle_label: "VI",
      brand_title: "Club Allocation",
      brand_sub: "Reserve-Based DA",
      nav_pipeline: "Run pipeline",
      nav_results: "Results",
      nav_fallback: "Manual entry",
      nav_admin: "Clubs & reserves",
      nav_scoring: "Scoring (blind)",
      db_status_loading: "— loading —",
      db_connected: "Connected to app.db",
      backend_dang_ket_noi: "Connecting to the application core…",
      backend_khong_ket_noi: "app.db not connected yet",
      backend_qua_han: "Could not connect to the application core. Close the window and open the program again. If it still fails, send the file loi_khoi_dong.txt (next to app.db) to whoever maintains this — it records exactly which step failed.",
      display_native: "Native application window",
      display_browser: "Fallback mode (browser)",
      last_run_line: "Last run: {run_at} (seed={seed}, {n_matched}/{n_total} matched)",
      never_run: "Pipeline has never been run",

      pipeline_title: "Run pipeline",
      pipeline_desc: "Validate data, draw lottery numbers, run the RB-DA algorithm, and export results.",
      label_students: "students",
      label_clubs: "clubs",
      label_submitted_prefs: "submitted preferences",
      label_matched: "matched to a club",
      import_panel_title: "Import data",
      import_hint_html: "Accepts a CSV normalized by <code>06_ms_forms_transform.py</code>. The system auto-detects the \"long\" or \"wide\" format — no need to choose.",
      import_col_test_title: "CSV: clubs to test for (Step 1)",
      import_col_pref_title: "CSV: ranked preferences (Step 2)",
      btn_import_confirm: "Import into the system",
      import_hint: "Drop Excel (.xlsx) or CSV files below — the app works out whether each one is a club list, a club-test selection, or ranked preferences. Drop several at once; they are imported in the right order.",
      drop_zone_main: "Drop Excel or CSV files here",
      drop_zone_sub: "accepts .xlsx and .csv — click to choose, several at a time",
      btn_import_all: "Import all",
      btn_clear_queue: "Clear list",
      csv_kind_clubs: "Club list",
      csv_kind_test_selection: "Club test selection",
      csv_kind_preferences: "Ranked preferences",
      csv_kind_unknown_label: "Unclear",
      queue_detected: "Detected: {kind}",
      queue_ambiguous: "Cannot tell what this file is — these columns fit both kinds. Please pick one on the right.",
      queue_unknown: "Unrecognised format. See mau_csv/HUONG_DAN_CSV.md for the columns the app can read.",
      queue_pick_kind: "— pick file kind —",
      queue_result_clubs: "Done: {n_created} new club(s), {n_updated} updated, {n_skipped} row(s) skipped",
      queue_result_students: "Done: {n_written} student(s) written, {n_created} created, {n_skipped} skipped",
      feedback_import_done: "Imported {n} file(s)",
      steps_panel_title: "5-step process",
      label_seed: "Seed",
      btn_validate: "Validate data",
      btn_run_pipeline: "Run pipeline",
      step_title_validate: "Validate data integrity",
      step_title_stb: "Draw lottery numbers (STB)",
      step_title_rbda: "Run the RB-DA algorithm",
      step_title_write: "Write results to the database",
      step_title_export: "Export CSV file",
      step_not_run_yet: "Not run yet",
      step_running: "Running…",
      step_done_default: "Done",
      generic_error: "Error",
      error_log_title: "Error log",
      history_panel_title: "Pipeline run history",
      btn_toggle: "Show/hide",
      th_time: "Time",
      th_seed: "Seed",
      th_rounds: "Rounds",
      th_matched_count: "Matched",
      th_total: "Total",
      th_redrawn: "STB redrawn?",
      history_empty: "No runs yet.",
      yes: "Yes",
      no: "No",

      results_title: "Allocation results",
      results_desc: "Students matched to a club, and how full each club is.",
      fill_panel_title: "Fill rate by club",
      legend_general: "General",
      legend_reserve: "Admitted on a reserved seat",
      results_list_title: "Club assignments",
      placeholder_results_search: "Search by student ID or name…",
      btn_export_csv: "Export CSV",
      th_student_id: "Student ID",
      th_name: "Name",
      th_club: "Club",
      th_tier: "Tier",
      th_pref_rank: "Preference rank",
      results_empty_state: "No results yet — run the pipeline on the \"Run pipeline\" tab first.",
      not_matched_label: "Not matched",
      unmatched_badge: "{n} not matched",
      tier_general: "General",
      tier_reserve: "Reserve",

      fallback_title: "Manual entry at the kiosk",
      fallback_desc: "Use this when a student can't submit through Microsoft Forms. The two steps — clubs to test for, and ranked preferences — are independent and don't affect each other.",
      fallback_step0_title: "Step 0 — Find or create a student",
      placeholder_fallback_search: "Enter student ID or name…",
      btn_search: "Search",
      placeholder_new_student_id: "New student ID",
      placeholder_full_name: "Full name",
      btn_create_student: "Create new student",
      btn_reset_entry: "Start over",
      confirm_reset_entry: "Click again to clear & start over",
      btn_delete_student: "Delete student",
      confirm_delete_student: "Click again to delete this student",
      fallback_step1_title: "Step 1 — Clubs to test/apply for (checkboxes)",
      btn_save_test_selection: "Save test selection",
      fallback_step2_title: "Step 2 — Rank preferences (independent, up to 10 clubs)",
      fallback_step2_hint: "Click clubs in descending order of preference. You can rank a club that wasn't ticked in Step 1.",
      ranking_current_label: "Current preference order:",
      btn_clear_all: "Clear all",
      btn_save_preferences: "Save preferences",
      btn_remove_ranked: "remove",
      search_no_students_found: "No students found.",
      toast_need_id_and_name: "Both a student ID and a name are required.",
      toast_student_created: "New student created.",
      toast_student_exists: "Student already exists — opening their profile.",
      feedback_test_selection_saved: "Saved {n} selection(s).",
      feedback_preferences_saved: "Saved {n} preference(s).",
      toast_reset_done: "Cleared test selection and preferences — ready to re-enter.",
      toast_student_deleted: "Deleted student {student_id}.",
      toast_delete_failed_prefix: "Could not delete: {errors}",
      feedback_error_prefix: "Error: {errors}",

      admin_title: "Clubs & reserved seats",
      admin_desc: "Create/edit clubs and assign reserved status to students. Reserve criteria are entirely up to the school — the system only matches labels (reserve_group) between clubs and students, nothing is hardcoded.",
      admin_club_form_title: "Add / edit club",
      placeholder_club_id: "Club ID (e.g. club_01)",
      placeholder_club_name: "Club name",
      placeholder_capacity: "Total seats",
      placeholder_reserve_capacity: "Reserved seats",
      placeholder_reserve_group: "Reserve label (leave blank if none)",
      btn_save_club: "Save club",
      th_club_id: "Club ID",
      th_name_short: "Name",
      th_capacity: "Total seats",
      th_reserve_capacity: "Reserved seats",
      th_reserve_group: "Reserve label",
      admin_club_empty: "No clubs yet — add the first one using the form above.",
      admin_reserve_assign_title: "Assign reserved status to students",
      placeholder_admin_student_search: "Search students by ID or name…",
      placeholder_reserve_group_apply: "Reserve label to apply",
      btn_bulk_assign: "Assign to ticked students",
      th_current_reserve_group: "Current reserve label",
      admin_student_empty: "No students in the system yet — add them via the \"Manual entry\" tab or import from Microsoft Forms.",
      btn_prev_page: "‹ Prev",
      btn_next_page: "Next ›",
      pagination_label: "Page {page}/{total_pages} — {total} students total",
      btn_delete: "Delete",
      confirm_delete_generic: "Click again to delete",
      toast_club_deleted: "Deleted club {club_id}",

      danger_zone_title: "Danger zone — clear data to start over",
      danger_zone_desc: "Importing a file only ADDS students; it never removes the ones already here. To run a fresh trial with a different dataset, clear them here — otherwise the previous cohort still takes seats and skews the result.",
      danger_zone_safety: "Both buttons BACK UP app.db before deleting anything, and neither touches the run log (run_history) — the audit trail is kept.",
      btn_reset_students: "Delete all students (keep clubs)",
      btn_reset_all: "Delete all data (clubs too)",
      confirm_reset_students: "Click again to delete ALL students",
      confirm_reset_all: "Click again to delete ALL data",
      confirm_reset_students_has_results: "Click again — this also discards the run results",
      confirm_reset_all_has_results: "Click again — this discards the clubs and the run results",
      toast_reset_students_done: "Deleted {n_students} student(s); {n_clubs_left} club(s) kept. Backup: {backup_name}",
      toast_reset_all_done: "Deleted {n_students} student(s) and {n_clubs} club(s). Backup: {backup_name}",
      feedback_club_form_required: "Club ID, name, and total seats are required.",
      feedback_club_saved: "Saved club {club_id}",
      toast_no_students_ticked: "No students ticked.",
      toast_bulk_assign_success: "Assigned to {n} student(s).",

      scoring_title: "Scoring (blind)",
      scoring_desc: "Select a club to score. The list shows only student ID and name — never the lottery number or preference rank, so scorers can't be biased by known priority.",
      scoring_overview_title: "Progress by club",
      th_n_applicants: "Applicants",
      th_n_scored: "Scored",
      scoring_overview_empty: "No club has any applicants yet.",
      btn_save_scores: "Save scores",
      th_score: "Score",
      btn_score_link: "Score →",
      feedback_scores_saved: "Saved scores for {n} student(s).",

      toast_dashboard_read_failed: "Could not read dashboard status: {errors}",
      stb_locked_label: "Lottery numbers (STB) LOCKED since {locked_at} — future runs will reuse them, not redraw.",
      stb_unlocked_label: "Lottery numbers (STB) have never been drawn — the first run will draw them and lock automatically.",
      btn_redraw_stb: "Redraw STB…",
      toast_redraw_armed: "Click 'Run pipeline' to redraw STB — one more confirmation will be required before running.",
      health_panel_title: "Data warnings",
      health_panel_hint: "Gaps that still let the pipeline run, but silently change the outcome. Check these before running.",
      health_clean: "No issues found. The data is ready to run.",
      health_summary: "{n} warning(s), {n_high} of them serious.",
      health_sev_high: "Serious",
      health_sev_medium: "Worth checking",
      health_sev_info: "Information",
      btn_health_recheck: "Re-check",
      toast_data_valid: "Data is valid — {n_students} students, {n_clubs} clubs.",
      toast_data_invalid: "Data has errors — see the log below.",
      confirm_redraw_run: "Confirm: REDRAW all lottery numbers and re-run the pipeline (overwrites current results)?",
      confirm_overwrite_run: "Existing results found — running again will OVERWRITE them (still saved to history for audit). Confirm?",
      btn_confirm_run: "Confirm run",
      btn_cancel: "Cancel",
      toast_run_success: "Pipeline run succeeded — {n_matched}/{n_total} students matched, {rounds} round(s).",
      toast_run_failed: "Pipeline run failed — see the error log.",
      toast_csv_read_error_prefix: "Error reading CSV: {errors}",
      csv_format_wide: "wide (1 row per student)",
      csv_format_long: "long (multiple rows per student)",
      csv_preview_summary: "Detected format: <span class=\"preview-highlight\">{format}</span><br>{n_rows} data row(s) — {n_students_detected} students, <span class=\"preview-highlight\">{n_new_students} new student(s)</span> will be created.",
      feedback_no_file_selected: "No file selected.",
      feedback_import_failed: "Import failed.",
      feedback_import_success: "Imported: {n_written} student(s) ({n_created} new, {n_skipped} skipped).",
      toast_csv_import_success: "CSV import succeeded — {n_written} student(s).",
      toast_export_success: "Exported {n_rows} row(s) to {path} ({n_club_files} per-club file(s))",
      toast_export_failed: "CSV export failed: {errors}",

      recovery_title: "Data Recovery",
      recovery_heading: "Could not open the database",
      recovery_intro: "The app could not start because app.db has a problem. The data may not be lost — try the steps below before contacting support.",
      recovery_error_detail_label: "Technical error detail (for support if needed):",
      recovery_backups_label: "Backups found on this machine:",
      th_backup_name: "File name",
      th_backup_time: "Backed up at",
      th_backup_size: "Size",
      btn_restore_backup: "Restore from the most recent readable backup",
      btn_start_fresh: "Start with a new database",
      confirm_start_fresh: "Click again to CONFIRM — the corrupt file will be renamed, not deleted",
      recovery_working: "Working…",
      recovery_please_restart: "Please CLOSE and REOPEN the app to continue.",
    },
  };

  let currentLang = "vi";
  try {
    const stored = global.localStorage && global.localStorage.getItem("rbda_lang");
    if (stored === "vi" || stored === "en") currentLang = stored;
  } catch (e) {
    /* localStorage unavailable — default to vi */
  }

  function interpolate(template, params) {
    if (!params) return template;
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      if (!(key in params)) return match;
      const v = params[key];
      if (v === null || v === undefined) return "";
      return Array.isArray(v) ? v.join(", ") : String(v);
    });
  }

  function t(key, params) {
    const table = UI_STRINGS[currentLang] || UI_STRINGS.vi;
    const template = key in table ? table[key] : (UI_STRINGS.vi[key] || key);
    return interpolate(template, params);
  }

  function translateError(entry) {
    if (entry === null || entry === undefined) return "";
    if (typeof entry === "string") return entry;
    if (typeof entry === "object" && entry.code) {
      const table = ERROR_MESSAGES[entry.code];
      const template = table ? (table[currentLang] || table.vi) : entry.code;
      return interpolate(template, entry.params);
    }
    try {
      return JSON.stringify(entry);
    } catch (e) {
      return String(entry);
    }
  }

  function translateErrors(list) {
    if (!Array.isArray(list)) return [translateError(list)];
    return list.map(translateError);
  }

  function applyStaticText() {
    document.querySelectorAll("[data-i18n]").forEach((elm) => {
      // Skip a two-step-confirm button while it's armed (.is-confirming):
      // armTwoStepConfirm tracks "armed" state internally and only the
      // element's OWN reset logic may change its label back — overwriting
      // it here would desync visible state from internal state (button
      // would look freshly-unarmed while a single click still fires the
      // destructive action).
      if (elm.classList && elm.classList.contains("is-confirming")) return;
      elm.textContent = t(elm.getAttribute("data-i18n"));
    });
    document.querySelectorAll("[data-i18n-html]").forEach((elm) => {
      elm.innerHTML = t(elm.getAttribute("data-i18n-html"));
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((elm) => {
      elm.placeholder = t(elm.getAttribute("data-i18n-placeholder"));
    });
    document.title = t("page_title");
    const langBtn = document.getElementById("btnLangToggle");
    if (langBtn) langBtn.textContent = t("lang_toggle_label");
  }

  function getLang() {
    return currentLang;
  }

  function setLang(lang) {
    if (lang !== "vi" && lang !== "en") return;
    currentLang = lang;
    try {
      global.localStorage && global.localStorage.setItem("rbda_lang", lang);
    } catch (e) {
      /* ignore */
    }
    document.documentElement.lang = lang;
    applyStaticText();
    global.dispatchEvent(new Event("langchange"));
  }

  global.I18N = { t, translateError, translateErrors, getLang, setLang, applyStaticText };
})(window);
