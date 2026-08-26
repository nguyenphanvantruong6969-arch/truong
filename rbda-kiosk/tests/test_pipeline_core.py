import pytest

from rbda_priority_pipeline import (
    club_choice_function,
    compute_club_priority,
    default_reserve_eligible_fn,
    generate_stb_lottery,
    load_from_sqlite,
    run_full_pipeline,
    run_rbda,
    sanity_check_result,
    seed_sample_data,
    validate_data_integrity,
    verify_stability,
    MatchResult,
)


def test_generate_stb_lottery_is_deterministic_and_a_bijection():
    ids = ["s1", "s2", "s3", "s4", "s5"]
    lot1 = generate_stb_lottery(ids, seed=1)
    lot2 = generate_stb_lottery(ids, seed=1)
    assert lot1 == lot2
    assert sorted(lot1.values()) == list(range(len(ids)))
    assert set(lot1.keys()) == set(ids)


def test_compute_club_priority_tier1_before_tier2_and_tiebreak_by_stb():
    applicants = ["a", "b", "c", "d"]
    tested_scores = {"a": 8.0, "b": 9.0}
    stb = {"a": 3, "b": 1, "c": 0, "d": 2}

    order = compute_club_priority("X", applicants, tested_scores, stb)

    # tier1 (tested) sorted by score desc: b (9.0) then a (8.0)
    # tier2 (untested) sorted by stb asc: c (0) then d (2)
    assert order == ["b", "a", "c", "d"]


def test_compute_club_priority_raises_on_missing_stb():
    with pytest.raises(ValueError):
        compute_club_priority("X", ["a", "b"], {}, {"a": 0})


def test_club_choice_function_fills_reserve_before_general():
    pool = ["s1", "s2", "s3", "s4"]
    rank = {"s1": 0, "s2": 1, "s3": 2, "s4": 3}

    def reserve_eligible(sid):
        return sid == "s2"

    accepted, tier_of = club_choice_function(
        pool, capacity=2, reserve_capacity=1,
        is_reserve_eligible_fn=reserve_eligible, rank=rank,
    )

    assert accepted == ["s2", "s1"]
    assert tier_of == {"s2": "reserve", "s1": "general"}


def test_club_choice_function_reserve_seat_stays_empty_if_no_eligible_candidate():
    pool = ["s1", "s3"]
    rank = {"s1": 0, "s3": 2}
    accepted, tier_of = club_choice_function(
        pool, capacity=2, reserve_capacity=1,
        is_reserve_eligible_fn=lambda sid: False, rank=rank,
    )
    # no one eligible for the reserved seat -> it rolls into the general pool
    assert accepted == ["s1", "s3"]
    assert tier_of == {"s1": "general", "s3": "general"}


def test_run_rbda_small_deterministic_scenario():
    students = {"s1": {}, "s2": {}, "s3": {}}
    clubs = {
        "A": {"capacity": 1, "reserve_capacity": 0},
        "B": {"capacity": 1, "reserve_capacity": 0},
    }
    tested_scores = {}
    applicants = {"A": ["s1", "s2"], "B": ["s2", "s3"]}
    preferences = {"s1": ["A"], "s2": ["A", "B"], "s3": ["B"]}
    stb_lottery = {"s1": 0, "s2": 1, "s3": 2}

    result = run_rbda(
        students, clubs, tested_scores, applicants, preferences, stb_lottery,
        is_reserve_eligible_fn=lambda sid, cid: False,
    )

    assert result.assignment == {"s1": "A", "s2": "B", "s3": None}
    assert result.rounds_run == 2
    assert result.rank_in_student_pref["s1"] == 1
    assert result.rank_in_student_pref["s2"] == 2

    assert sanity_check_result(result, clubs, preferences) == []
    assert verify_stability(result, clubs, preferences, lambda sid, cid: False) == []


def test_run_rbda_respects_capacity_and_reserve_with_soft_reserves():
    students = {sid: {} for sid in ["s1", "s2", "s3", "s4"]}
    clubs = {"A": {"capacity": 2, "reserve_capacity": 1}}
    # s2 is the only reserve-eligible student, and has the worst STB —
    # the reserved seat should still go to them over higher-priority
    # general students, because the reserve pass runs first.
    applicants = {"A": ["s1", "s2", "s3", "s4"]}
    preferences = {sid: ["A"] for sid in students}
    stb_lottery = {"s1": 0, "s2": 3, "s3": 1, "s4": 2}
    reserve_group = {"s2"}

    result = run_rbda(
        students, clubs, {}, applicants, preferences, stb_lottery,
        is_reserve_eligible_fn=lambda sid, cid: sid in reserve_group,
    )

    assert result.assignment["s2"] == "A"
    assert result.matched_tier["s2"] == "reserve"
    # general seat goes to best remaining STB: s1
    assert result.assignment["s1"] == "A"
    assert result.matched_tier["s1"] == "general"
    assert result.assignment["s3"] is None
    assert result.assignment["s4"] is None

    assert sanity_check_result(result, clubs, preferences) == []
    assert verify_stability(
        result, clubs, preferences, lambda sid, cid: sid in reserve_group
    ) == []


def _codes(entries):
    return [e["code"] for e in entries]


def test_validate_data_integrity_flags_duplicate_and_overflowing_preferences():
    students = {"s1": {}}
    clubs = {"A": {"capacity": 5, "reserve_capacity": 0}}
    preferences = {"s1": ["A", "A"]}
    errors = validate_data_integrity(students, clubs, preferences, {})
    assert "pref_duplicate_club" in _codes(errors)
    assert errors[_codes(errors).index("pref_duplicate_club")]["params"]["student_id"] == "s1"


def test_validate_data_integrity_flags_too_many_preferences():
    students = {"s1": {}}
    clubs = {f"c{i}": {"capacity": 5, "reserve_capacity": 0} for i in range(11)}
    preferences = {"s1": [f"c{i}" for i in range(11)]}
    errors = validate_data_integrity(students, clubs, preferences, {})
    assert "pref_too_many" in _codes(errors)


def test_validate_data_integrity_flags_unknown_club_and_student_refs():
    students = {}
    clubs = {}
    preferences = {"ghost": ["nowhere"]}
    applicants = {"nowhere": ["ghost"]}
    errors = validate_data_integrity(students, clubs, preferences, applicants)
    assert "pref_student_not_in_students" in _codes(errors)
    assert "pref_unknown_club" in _codes(errors)


def test_validate_data_integrity_flags_bad_club_capacities():
    students = {}
    clubs = {
        "zero_cap": {"capacity": 0, "reserve_capacity": 0},
        "over_reserve": {"capacity": 5, "reserve_capacity": 10},
    }
    errors = validate_data_integrity(students, clubs, {}, {})
    assert "club_capacity_not_positive" in _codes(errors)
    assert "club_reserve_exceeds_capacity" in _codes(errors)


def test_sanity_check_result_flags_over_capacity_and_out_of_preference_assignment():
    clubs = {"A": {"capacity": 1, "reserve_capacity": 0}}
    preferences = {"s1": ["A"], "s2": ["B"]}
    result = MatchResult(
        assignment={"s1": "A", "s2": "A"},  # over capacity, and A not in s2's prefs
        rounds_run=1,
    )
    problems = sanity_check_result(result, clubs, preferences)
    assert "club_over_capacity" in _codes(problems)
    assert "assignment_not_in_preferences" in _codes(problems)


def test_error_entries_are_translatable_to_both_languages():
    """Every {code, params} entry the algorithm can emit must render
    cleanly in both languages via i18n_errors.format_message — this is
    the regression guard for the bilingual UI."""
    from i18n_errors import format_message

    students = {"s1": {}}
    clubs = {
        "A": {"capacity": 5, "reserve_capacity": 0},
        "over_reserve": {"capacity": 0, "reserve_capacity": 10},
    }
    preferences = {"s1": ["A", "A", "ghost_club"]}
    applicants = {"ghost_club_2": ["ghost_student"]}
    errors = validate_data_integrity(students, clubs, preferences, applicants)
    assert errors, "expected this deliberately-broken data to produce errors"

    for entry in errors:
        for lang in ("vi", "en"):
            text = format_message(entry["code"], entry["params"], lang=lang)
            assert text != entry["code"], f"missing {lang} translation for {entry['code']}"
            assert "{" not in text, f"unfilled placeholder in {lang} text: {text!r}"


def test_full_pipeline_on_seeded_sample_data_has_no_integrity_problems(tmp_path):
    db_path = str(tmp_path / "app.db")
    csv_path = str(tmp_path / "match_results.csv")
    seed_sample_data(db_path, n_students=120, seed=7)

    result = run_full_pipeline(db_path, seed=42, output_csv_path=csv_path)

    students, clubs, tested_scores, applicants, preferences, stb_lottery = (
        load_from_sqlite(db_path)
    )

    assert sanity_check_result(result, clubs, preferences) == []
    assert verify_stability(
        result, clubs, preferences,
        default_reserve_eligible_fn(students, clubs),
    ) == []
    assert sum(1 for v in result.assignment.values() if v) > 0
