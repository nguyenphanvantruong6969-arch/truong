/* ==========================================================================
   app.js — logic frontend cho kiosk Phân bổ Câu lạc bộ (RB-DA)
   ==========================================================================
   Toàn bộ giao tiếp với Python đi qua window.pywebview.api.<ten_ham>(...),
   mỗi hàm trả về Promise<{ok, data, errors}> (quy ước thống nhất ở api.py).
   Không dùng alert()/confirm() ở bất cứ đâu — thay bằng toast + xác nhận
   2 bước ngay tại chỗ (đổi label nút, yêu cầu bấm lần 2).
   ========================================================================== */

(function () {
  "use strict";

  /* ------------------------------------------------------------------ *
   * 0. TIỆN ÍCH DÙNG CHUNG
   * ------------------------------------------------------------------ */

  function callApi(name, ...args) {
    if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api[name] !== "function") {
      return Promise.resolve({ ok: false, data: null, errors: [`Chưa sẵn sàng kết nối tới backend (${name})`] });
    }
    return window.pywebview.api[name](...args).catch((e) => ({
      ok: false,
      data: null,
      errors: [String(e)],
    }));
  }

  function el(id) {
    return document.getElementById(id);
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function showToast(message, type) {
    const stack = el("toastStack");
    const t = document.createElement("div");
    t.className = "toast" + (type === "error" ? " is-error" : type === "success" ? " is-success" : "");
    t.textContent = message;
    stack.appendChild(t);
    setTimeout(() => {
      t.classList.add("is-leaving");
      setTimeout(() => t.remove(), 200);
    }, 3600);
  }

  function feedback(node, message, isError) {
    node.textContent = message;
    node.className = "save-feedback " + (isError ? "is-error" : "is-success");
    if (message) {
      setTimeout(() => {
        if (node.textContent === message) node.textContent = "";
      }, 5000);
    }
  }

  // Nút xác nhận 2 bước (thay confirm() native) — bấm lần 1 đổi label +
  // class .is-confirming, bấm lần 2 trong vòng `windowMs` mới thật sự chạy.
  function armTwoStepConfirm(button, confirmLabel, onConfirmed, windowMs) {
    const original = button.textContent;
    let armed = false;
    let timer = null;
    button.addEventListener("click", () => {
      if (!armed) {
        armed = true;
        button.textContent = confirmLabel;
        button.classList.add("is-confirming");
        timer = setTimeout(() => {
          armed = false;
          button.textContent = original;
          button.classList.remove("is-confirming");
        }, windowMs || 4000);
      } else {
        clearTimeout(timer);
        armed = false;
        button.textContent = original;
        button.classList.remove("is-confirming");
        onConfirmed();
      }
    });
  }

  function debounce(fn, ms) {
    let t = null;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  /* ------------------------------------------------------------------ *
   * 1. ĐIỀU HƯỚNG TAB
   * ------------------------------------------------------------------ */

  const TAB_LOADERS = {
    pipeline: loadPipelineTab,
    results: loadResultsTab,
    fallback: loadFallbackTab,
    admin: loadAdminTab,
    scoring: loadScoringTab,
  };

  function initTabs() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach((btn) => {
      btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });
  }

  function switchTab(tabName) {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".view").forEach((view) => {
      view.classList.toggle("is-active", view.id === "view-" + tabName);
    });
    const loader = TAB_LOADERS[tabName];
    if (loader) loader();
  }

  /* ------------------------------------------------------------------ *
   * 2. SIDEBAR: TRẠNG THÁI DB / LẦN CHẠY GẦN NHẤT
   * ------------------------------------------------------------------ */

  function refreshSidebarStatus() {
    callApi("get_last_run_info").then((res) => {
      const line = el("lastRunLine");
      if (res.ok && res.data) {
        line.textContent = `Chạy gần nhất: ${res.data.run_at} (seed=${res.data.seed}, ${res.data.n_matched}/${res.data.n_total} xếp được)`;
      } else {
        line.textContent = "Chưa chạy pipeline lần nào";
      }
    });
    el("dbStatusLine").textContent = "Đã kết nối app.db";
  }

  /* ------------------------------------------------------------------ *
   * 3. TAB 1 — VẬN HÀNH PIPELINE
   * ------------------------------------------------------------------ */

  let importState = {
    testSelection: null, // { text, kind }
    preferences: null,
  };

  function loadPipelineTab() {
    refreshDashboardStats();
    refreshStbLockLine();
    refreshSidebarStatus();
  }

  function refreshDashboardStats() {
    callApi("get_dashboard_status").then((res) => {
      if (!res.ok) {
        showToast("Không đọc được trạng thái tổng quan: " + res.errors.join("; "), "error");
        return;
      }
      el("statStudents").textContent = res.data.n_students;
      el("statClubs").textContent = res.data.n_clubs;
      el("statPrefs").textContent = res.data.n_students_with_preferences;
      el("statMatched").textContent = res.data.n_matched;
    });
  }

  function refreshStbLockLine() {
    callApi("get_stb_lock_status").then((res) => {
      const line = el("stbLockLine");
      if (!res.ok) {
        line.textContent = "";
        return;
      }
      clear(line);
      const dot = document.createElement("span");
      dot.className = "lock-dot";
      line.className = "stb-lock-line" + (res.data.is_locked ? "" : " is-unlocked");
      line.appendChild(dot);
      const label = document.createElement("span");
      label.textContent = res.data.is_locked
        ? `Số bốc thăm (STB) ĐÃ KHOÁ từ ${res.data.locked_at} — các lần chạy tiếp theo sẽ tái sử dụng, không vẽ lại.`
        : "Số bốc thăm (STB) chưa từng được vẽ — lần chạy đầu tiên sẽ vẽ và tự động khoá lại.";
      line.appendChild(label);

      if (res.data.is_locked) {
        const redrawBtn = document.createElement("button");
        redrawBtn.className = "redraw-toggle";
        redrawBtn.textContent = "Vẽ lại STB…";
        redrawBtn.addEventListener("click", () => promptForceRedraw());
        line.appendChild(redrawBtn);
      }
    });
  }

  let forceRedrawArmed = false;

  function promptForceRedraw() {
    if (!forceRedrawArmed) {
      forceRedrawArmed = true;
      showToast("Bấm nút 'Chạy pipeline' để vẽ lại STB — sẽ cần xác nhận thêm 1 lần nữa trước khi chạy.", "error");
      setTimeout(() => {
        forceRedrawArmed = false;
      }, 20000);
    } else {
      forceRedrawArmed = false;
    }
  }

  function renderSteps(steps) {
    const stepper = el("stepper");
    steps.forEach((s) => {
      const li = stepper.querySelector(`.step[data-step="${s.step}"]`);
      if (!li) return;
      li.dataset.status = s.status;
      const detail = li.querySelector(".step-detail");
      if (s.status === "running") detail.textContent = "Đang chạy…";
      else if (s.status === "done") detail.textContent = s.detail || "Hoàn tất";
      else if (s.status === "error")
        detail.textContent = Array.isArray(s.detail) ? s.detail.join(" | ") : s.detail || "Lỗi";
    });
  }

  function resetSteps() {
    document.querySelectorAll("#stepper .step").forEach((li) => {
      li.dataset.status = "";
      li.querySelector(".step-detail").textContent = "Chưa chạy";
    });
  }

  function showLog(errors) {
    const panel = el("logPanel");
    const box = el("logBox");
    if (!errors || !errors.length) {
      panel.hidden = true;
      box.textContent = "";
      return;
    }
    panel.hidden = false;
    box.textContent = errors.map((e) => (typeof e === "string" ? e : JSON.stringify(e))).join("\n");
  }

  function initPipelineHandlers() {
    el("btnValidate").addEventListener("click", () => {
      el("btnValidate").disabled = true;
      callApi("check_data_integrity").then((res) => {
        el("btnValidate").disabled = false;
        if (res.ok) {
          showToast(`Dữ liệu hợp lệ — ${res.data.n_students} học sinh, ${res.data.n_clubs} club.`, "success");
          showLog(null);
        } else {
          showToast("Dữ liệu có lỗi — xem nhật ký bên dưới.", "error");
          showLog(res.errors);
        }
      });
    });

    el("btnRun").addEventListener("click", () => {
      runPipelineFlow();
    });

    el("btnToggleHistory").addEventListener("click", () => {
      const table = el("historyTable");
      table.hidden = !table.hidden;
      if (!table.hidden) loadRunHistory();
    });

    initCsvImportHandlers();
  }

  function runPipelineFlow() {
    callApi("get_pipeline_run_warning").then((warn) => {
      const seed = parseInt(el("seedInput").value, 10) || 42;
      const wantsRedraw = forceRedrawArmed;
      const needsConfirm = (warn.ok && warn.data.has_existing_results) || wantsRedraw;

      if (!needsConfirm) {
        executeRun(seed, false);
        return;
      }

      // Chèn thanh xác nhận ngay dưới nút, thay vì confirm() native.
      let bar = el("runConfirmBar");
      if (bar) bar.remove();
      bar = document.createElement("div");
      bar.id = "runConfirmBar";
      bar.className = "run-confirm-bar";
      const msg = document.createElement("span");
      msg.textContent = wantsRedraw
        ? "Xác nhận: VẼ LẠI toàn bộ số bốc thăm và chạy lại pipeline (ghi đè kết quả hiện tại)?"
        : "Đã có kết quả cũ — chạy lại sẽ GHI ĐÈ (vẫn lưu vào lịch sử để kiểm toán). Xác nhận?";
      bar.appendChild(msg);
      const confirmBtn = document.createElement("button");
      confirmBtn.className = "btn btn-primary";
      confirmBtn.textContent = "Xác nhận chạy";
      confirmBtn.addEventListener("click", () => {
        bar.remove();
        forceRedrawArmed = false;
        executeRun(seed, wantsRedraw);
      });
      const cancelBtn = document.createElement("button");
      cancelBtn.className = "btn btn-ghost";
      cancelBtn.textContent = "Huỷ";
      cancelBtn.addEventListener("click", () => {
        bar.remove();
        forceRedrawArmed = false;
      });
      bar.appendChild(confirmBtn);
      bar.appendChild(cancelBtn);
      el("stepper").insertAdjacentElement("beforebegin", bar);
    });
  }

  function executeRun(seed, forceRedraw) {
    resetSteps();
    showLog(null);
    el("btnRun").disabled = true;
    el("btnValidate").disabled = true;

    callApi("run_pipeline", seed, forceRedraw).then((res) => {
      el("btnRun").disabled = false;
      el("btnValidate").disabled = false;
      const steps = (res.data && res.data.steps) || (res.errors && res.errors.steps) || [];
      renderSteps(steps);

      if (res.ok) {
        showToast(
          `Chạy pipeline thành công — ${res.data.n_matched}/${res.data.n_total} học sinh đã xếp club, ${res.data.rounds_run} vòng lặp.`,
          "success"
        );
        showLog(null);
        refreshDashboardStats();
        refreshStbLockLine();
        refreshSidebarStatus();
        if (!el("historyTable").hidden) loadRunHistory();
      } else {
        const errs = Array.isArray(res.errors) ? res.errors : res.errors && res.errors.errors ? res.errors.errors : [String(res.errors)];
        showToast("Chạy pipeline thất bại — xem nhật ký lỗi.", "error");
        showLog(errs);
      }
    });
  }

  function loadRunHistory() {
    callApi("get_run_history", 20).then((res) => {
      const body = el("historyTableBody");
      clear(body);
      if (!res.ok || !res.data.length) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 7;
        td.textContent = "Chưa có lần chạy nào.";
        tr.appendChild(td);
        body.appendChild(tr);
        return;
      }
      res.data.forEach((r) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          `<td>${esc(r.run_id)}</td><td>${esc(r.run_at)}</td><td>${esc(r.seed)}</td>` +
          `<td>${esc(r.rounds_run)}</td><td>${esc(r.n_matched)}</td><td>${esc(r.n_total)}</td>` +
          `<td>${r.stb_redrawn ? "Có" : "Không"}</td>`;
        body.appendChild(tr);
      });
    });
  }

  /* ---- Nhập CSV Microsoft Forms ---- */

  function initCsvImportHandlers() {
    wireCsvInput("fileTestSelection", "previewTestSelection", "btnImportTestSelection", "test_selection");
    wireCsvInput("filePreferences", "previewPreferences", "btnImportPreferences", "preferences");

    el("btnImportTestSelection").addEventListener("click", () => {
      doImport("test_selection", "import_test_selection_csv", el("feedbackImportTestSelection"));
    });
    el("btnImportPreferences").addEventListener("click", () => {
      doImport("preferences", "import_preferences_csv", el("feedbackImportPreferences"));
    });
  }

  function wireCsvInput(inputId, previewId, btnId, kind) {
    el(inputId).addEventListener("change", (ev) => {
      const file = ev.target.files && ev.target.files[0];
      const previewBox = el(previewId);
      const btn = el(btnId);
      if (!file) {
        previewBox.hidden = true;
        btn.disabled = true;
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const text = String(reader.result || "");
        callApi("preview_import_csv", text, kind).then((res) => {
          if (!res.ok) {
            previewBox.hidden = false;
            previewBox.textContent = "Lỗi đọc CSV: " + res.errors.join("; ");
            btn.disabled = true;
            return;
          }
          const d = res.data;
          previewBox.hidden = false;
          previewBox.innerHTML =
            `Định dạng nhận diện: <span class="preview-highlight">${d.format === "wide" ? "rộng (1 dòng/học sinh)" : "dài (nhiều dòng/học sinh)"}</span><br>` +
            `${d.n_rows} dòng dữ liệu — ${d.n_students_detected} học sinh, ` +
            `<span class="preview-highlight">${d.n_new_students} học sinh mới</span> sẽ được tạo.`;
          btn.disabled = false;
          if (kind === "test_selection") importState.testSelection = text;
          else importState.preferences = text;
        });
      };
      reader.readAsText(file, "UTF-8");
    });
  }

  function doImport(kind, apiFn, feedbackNode) {
    const text = kind === "test_selection" ? importState.testSelection : importState.preferences;
    if (!text) {
      feedback(feedbackNode, "Chưa chọn file.", true);
      return;
    }
    const btn = kind === "test_selection" ? el("btnImportTestSelection") : el("btnImportPreferences");
    btn.disabled = true;
    callApi(apiFn, text, true).then((res) => {
      btn.disabled = false;
      if (!res.ok) {
        feedback(feedbackNode, "Nhập thất bại.", true);
        showLog(Array.isArray(res.errors) ? res.errors : [String(res.errors)]);
        return;
      }
      const d = res.data;
      const nWritten = d.n_students_with_preferences_written ?? d.n_students_with_selection_written ?? 0;
      feedback(feedbackNode, `Đã nhập: ${nWritten} học sinh (${d.n_students_created} mới, ${d.n_students_skipped} bị bỏ qua).`, false);
      showToast(`Nhập CSV thành công — ${nWritten} học sinh.`, "success");

      const warnBox = el("importWarnings");
      if (d.warnings && d.warnings.length) {
        warnBox.hidden = false;
        clear(warnBox);
        d.warnings.forEach((w) => {
          const div = document.createElement("div");
          div.textContent = "• " + w;
          warnBox.appendChild(div);
        });
      } else {
        warnBox.hidden = true;
      }
      refreshDashboardStats();
    });
  }

  /* ------------------------------------------------------------------ *
   * 4. TAB 2 — KẾT QUẢ
   * ------------------------------------------------------------------ */

  function loadResultsTab() {
    loadClubFillStats();
    loadMatchResults("");
  }

  function loadClubFillStats() {
    callApi("get_club_fill_stats").then((res) => {
      const box = el("clubFillList");
      clear(box);
      if (!res.ok || !res.data.length) {
        box.innerHTML = '<div class="empty-state">Chưa có club nào.</div>';
        return;
      }
      res.data.forEach((c) => {
        const pct = c.capacity > 0 ? Math.min(100, Math.round((c.matched / c.capacity) * 100)) : 0;
        const reservePct = c.capacity > 0 ? Math.min(100, Math.round((c.reserve_capacity / c.capacity) * 100)) : 0;
        const row = document.createElement("div");
        row.className = "fill-row";
        row.innerHTML =
          `<span class="fill-name">${esc(c.name || c.club_id)}</span>` +
          `<span class="fill-track">` +
          `<span class="fill-bar" style="width:${pct}%"></span>` +
          (reservePct > 0
            ? `<span class="fill-bar is-reserve" style="width:${reservePct}%; position:absolute; left:0; top:0; opacity:0.55;"></span>`
            : "") +
          `</span>` +
          `<span class="fill-count">${c.matched}/${c.capacity}</span>`;
        row.querySelector(".fill-track").style.position = "relative";
        box.appendChild(row);
      });
    });
  }

  function loadMatchResults(search) {
    callApi("get_match_results", search || "").then((res) => {
      const body = el("resultsTableBody");
      const empty = el("resultsEmptyState");
      const badge = el("unmatchedBadge");
      clear(body);

      if (!res.ok || !res.data.length) {
        empty.hidden = false;
        badge.hidden = true;
        return;
      }
      empty.hidden = true;

      let nUnmatched = 0;
      res.data.forEach((r) => {
        const tr = document.createElement("tr");
        const clubCell = r.club_id
          ? `<span class="club-tag">${esc(r.club_name || r.club_id)}</span>`
          : `<span class="club-tag is-empty">Không xếp được</span>`;
        if (!r.club_id) nUnmatched++;
        tr.innerHTML =
          `<td>${esc(r.student_id)}</td><td>${esc(r.name)}</td><td>${clubCell}</td>` +
          `<td>${esc(r.matched_tier || "—")}</td><td>${esc(r.rank_in_student_pref ?? "—")}</td>`;
        body.appendChild(tr);
      });

      if (nUnmatched > 0) {
        badge.hidden = false;
        badge.textContent = `${nUnmatched} chưa xếp được club`;
      } else {
        badge.hidden = true;
      }
    });
  }

  function initResultsHandlers() {
    el("resultsSearch").addEventListener(
      "input",
      debounce((ev) => loadMatchResults(ev.target.value), 250)
    );
    el("btnExport").addEventListener("click", () => {
      callApi("export_csv", "match_results_export.csv").then((res) => {
        if (res.ok) showToast(`Đã xuất ${res.data.n_rows} dòng ra ${res.data.path}`, "success");
        else showToast("Xuất CSV thất bại: " + res.errors.join("; "), "error");
      });
    });
  }

  /* ------------------------------------------------------------------ *
   * 5. TAB 3 — NHẬP DỰ PHÒNG (KIOSK FALLBACK)
   * ------------------------------------------------------------------ */

  let currentFallbackStudent = null;
  let currentClubs = [];
  let currentRanking = [];

  function loadFallbackTab() {
    // không cần tải gì mặc định — chờ tìm/tạo học sinh
  }

  function initFallbackHandlers() {
    el("btnStudentSearch").addEventListener("click", doFallbackSearch);
    el("studentSearchInput").addEventListener(
      "input",
      debounce(() => doFallbackSearch(), 250)
    );
    el("btnCreateStudent").addEventListener("click", () => {
      const id = el("newStudentId").value.trim();
      const name = el("newStudentName").value.trim();
      if (!id || !name) {
        showToast("Cần nhập cả mã học sinh và họ tên.", "error");
        return;
      }
      callApi("create_student_if_missing", id, name).then((res) => {
        if (!res.ok) {
          showToast("Lỗi tạo học sinh: " + res.errors.join("; "), "error");
          return;
        }
        showToast(res.data.created ? "Đã tạo học sinh mới." : "Học sinh đã tồn tại — mở hồ sơ.", "success");
        el("newStudentId").value = "";
        el("newStudentName").value = "";
        selectFallbackStudent(id);
      });
    });

    el("btnSubmitTestSelection").addEventListener("click", () => {
      if (!currentFallbackStudent) return;
      const checked = Array.from(document.querySelectorAll("#testSelectionGrid .option-row.is-checked")).map(
        (row) => row.dataset.clubId
      );
      callApi("submit_test_selection", currentFallbackStudent, checked).then((res) => {
        if (res.ok) feedback(el("testSelectionFeedback"), `Đã lưu ${res.data.n_selected} lựa chọn.`, false);
        else feedback(el("testSelectionFeedback"), "Lỗi: " + res.errors.join("; "), true);
      });
    });

    el("btnClearRanking").addEventListener("click", () => {
      currentRanking = [];
      renderRankingList();
    });

    el("btnSubmitPreferences").addEventListener("click", () => {
      if (!currentFallbackStudent) return;
      if (!currentRanking.length) {
        feedback(el("preferencesFeedback"), "Cần xếp hạng ít nhất 1 nguyện vọng.", true);
        return;
      }
      callApi("submit_preferences", currentFallbackStudent, currentRanking).then((res) => {
        if (res.ok) feedback(el("preferencesFeedback"), `Đã lưu ${res.data.n_ranked} nguyện vọng.`, false);
        else feedback(el("preferencesFeedback"), "Lỗi: " + res.errors.join("; "), true);
      });
    });

    armTwoStepConfirm(el("btnResetStudentEntry"), "Bấm lần nữa để xoá hết & nhập lại", () => {
      if (!currentFallbackStudent) return;
      callApi("reset_student_entry", currentFallbackStudent).then((res) => {
        if (res.ok) {
          showToast("Đã xoá lựa chọn thi và nguyện vọng — nhập lại từ đầu.", "success");
          selectFallbackStudent(currentFallbackStudent);
        } else {
          showToast("Lỗi: " + res.errors.join("; "), "error");
        }
      });
    });

    armTwoStepConfirm(el("btnDeleteStudent"), "Bấm lần nữa để xoá học sinh", () => {
      if (!currentFallbackStudent) return;
      const studentId = currentFallbackStudent;
      callApi("delete_student", studentId).then((res) => {
        if (res.ok) {
          showToast(`Đã xoá học sinh ${studentId}.`, "success");
          currentFallbackStudent = null;
          el("fallbackWorkArea").hidden = true;
          el("studentSearchInput").value = "";
          clear(el("studentSearchResults"));
        } else {
          showToast("Không xoá được: " + res.errors.join("; "), "error");
        }
      });
    });
  }

  function doFallbackSearch() {
    const q = el("studentSearchInput").value.trim();
    if (!q) {
      clear(el("studentSearchResults"));
      return;
    }
    callApi("search_students", q).then((res) => {
      const box = el("studentSearchResults");
      clear(box);
      if (!res.ok || !res.data.length) {
        box.innerHTML = '<div class="empty-state">Không tìm thấy học sinh nào.</div>';
        return;
      }
      res.data.forEach((s) => {
        const row = document.createElement("div");
        row.className = "search-result-item";
        row.innerHTML = `<span>${esc(s.name)}</span><span class="search-result-id">${esc(s.student_id)}</span>`;
        row.addEventListener("click", () => selectFallbackStudent(s.student_id));
        box.appendChild(row);
      });
    });
  }

  function selectFallbackStudent(studentId) {
    Promise.all([callApi("get_student_entry_state", studentId), callApi("list_clubs")]).then(([stateRes, clubsRes]) => {
      if (!stateRes.ok) {
        showToast("Lỗi tải hồ sơ học sinh: " + stateRes.errors.join("; "), "error");
        return;
      }
      currentFallbackStudent = studentId;
      currentClubs = clubsRes.ok ? clubsRes.data : [];
      currentRanking = stateRes.data.ranked_clubs.slice();

      el("fallbackWorkArea").hidden = false;
      el("currentStudentLabel").textContent = `${stateRes.data.name} (${stateRes.data.student_id})`;

      renderTestSelectionGrid(stateRes.data.tested_clubs);
      renderRankingSourceGrid();
      renderRankingList();
    });
  }

  function renderTestSelectionGrid(testedClubIds) {
    const grid = el("testSelectionGrid");
    clear(grid);
    currentClubs.forEach((c) => {
      const row = document.createElement("div");
      row.className = "option-row" + (testedClubIds.includes(c.club_id) ? " is-checked" : "");
      row.dataset.clubId = c.club_id;
      row.innerHTML = `<span>${esc(c.name)}</span><span class="cb-club-id">${esc(c.club_id)}</span>`;
      row.addEventListener("click", () => row.classList.toggle("is-checked"));
      grid.appendChild(row);
    });
  }

  function renderRankingSourceGrid() {
    const grid = el("rankingSourceGrid");
    clear(grid);
    currentClubs.forEach((c) => {
      const row = document.createElement("div");
      row.className = "option-row";
      row.dataset.clubId = c.club_id;
      row.innerHTML = `<span>${esc(c.name)}</span><span class="cb-club-id">${esc(c.club_id)}</span>`;
      row.addEventListener("click", () => {
        if (currentRanking.includes(c.club_id)) {
          showToast("Club này đã có trong danh sách nguyện vọng.", "error");
          return;
        }
        if (currentRanking.length >= 10) {
          showToast("Tối đa 10 nguyện vọng.", "error");
          return;
        }
        currentRanking.push(c.club_id);
        renderRankingList();
      });
      grid.appendChild(row);
    });
  }

  function renderRankingList() {
    const list = el("rankingList");
    clear(list);
    currentRanking.forEach((cid, idx) => {
      const club = currentClubs.find((c) => c.club_id === cid);
      const li = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = `${club ? club.name : cid} (${cid})`;
      const removeBtn = document.createElement("button");
      removeBtn.textContent = "xoá";
      removeBtn.addEventListener("click", () => {
        currentRanking.splice(idx, 1);
        renderRankingList();
      });
      li.appendChild(label);
      li.appendChild(removeBtn);
      list.appendChild(li);
    });
  }

  /* ------------------------------------------------------------------ *
   * 6. TAB 4 — QUẢN LÝ CLUB & DỰ TRỮ
   * ------------------------------------------------------------------ */

  let adminStudentPage = 1;
  const ADMIN_PAGE_SIZE = 50;

  function loadAdminTab() {
    loadAdminClubs();
    loadReserveGroupOptions();
    adminStudentPage = 1;
    loadAdminStudents();
  }

  function loadAdminClubs() {
    callApi("list_clubs_admin").then((res) => {
      const body = el("adminClubTableBody");
      const emptyState = el("adminClubEmptyState");
      clear(body);
      if (!res.ok || !res.data.length) {
        emptyState.hidden = false;
        return;
      }
      emptyState.hidden = true;
      res.data.forEach((c) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          `<td>${esc(c.club_id)}</td><td>${esc(c.name)}</td><td>${esc(c.capacity)}</td>` +
          `<td>${esc(c.reserve_capacity)}</td><td>${esc(c.reserve_group || "—")}</td><td></td>`;
        const delBtn = document.createElement("button");
        delBtn.className = "btn-icon-danger";
        delBtn.textContent = "Xoá";
        armTwoStepConfirm(delBtn, "Bấm lần nữa để xoá", () => {
          callApi("delete_club", c.club_id).then((delRes) => {
            if (delRes.ok) {
              showToast("Đã xoá club " + c.club_id, "success");
              loadAdminClubs();
              loadReserveGroupOptions();
            } else {
              showToast("Không xoá được: " + delRes.errors.join("; "), "error");
            }
          });
        });
        tr.lastElementChild.appendChild(delBtn);
        body.appendChild(tr);
      });
    });
  }

  function loadReserveGroupOptions() {
    callApi("list_reserve_groups_in_use").then((res) => {
      const list = el("reserveGroupOptions");
      clear(list);
      if (res.ok) {
        res.data.forEach((g) => {
          const opt = document.createElement("option");
          opt.value = g;
          list.appendChild(opt);
        });
      }
    });
  }

  function loadAdminStudents() {
    const search = el("adminStudentSearch").value.trim();
    callApi("list_students_admin", search, adminStudentPage, ADMIN_PAGE_SIZE).then((res) => {
      const body = el("adminStudentTableBody");
      const emptyState = el("adminStudentEmptyState");
      const pagination = el("adminStudentPagination");
      clear(body);

      if (!res.ok || !res.data.rows.length) {
        emptyState.hidden = false;
        pagination.hidden = true;
        return;
      }
      emptyState.hidden = true;
      pagination.hidden = false;

      res.data.rows.forEach((s) => {
        const tr = document.createElement("tr");
        const tdCheck = document.createElement("td");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "admin-row-checkbox";
        cb.dataset.studentId = s.student_id;
        tdCheck.appendChild(cb);
        tr.appendChild(tdCheck);
        tr.innerHTML +=
          `<td>${esc(s.student_id)}</td><td>${esc(s.name)}</td><td>${esc(s.reserve_group || "—")}</td>`;
        body.appendChild(tr);
      });

      el("adminPaginationLabel").textContent =
        `Trang ${res.data.page}/${res.data.total_pages} — tổng ${res.data.total} học sinh`;
      el("btnAdminPrevPage").disabled = res.data.page <= 1;
      el("btnAdminNextPage").disabled = res.data.page >= res.data.total_pages;
    });
  }

  function initAdminHandlers() {
    el("btnSaveClub").addEventListener("click", () => {
      const id = el("clubFormId").value.trim();
      const name = el("clubFormName").value.trim();
      const capacity = el("clubFormCapacity").value;
      const reserveCapacity = el("clubFormReserveCapacity").value || 0;
      const reserveGroup = el("clubFormReserveGroup").value.trim();
      if (!id || !name || !capacity) {
        feedback(el("clubFormFeedback"), "Cần nhập mã club, tên, và tổng chỗ.", true);
        return;
      }
      callApi("create_or_update_club", id, name, capacity, reserveCapacity, reserveGroup).then((res) => {
        if (res.ok) {
          feedback(el("clubFormFeedback"), "Đã lưu club " + id, false);
          el("clubFormId").value = "";
          el("clubFormName").value = "";
          el("clubFormCapacity").value = "";
          el("clubFormReserveCapacity").value = "0";
          el("clubFormReserveGroup").value = "";
          loadAdminClubs();
          loadReserveGroupOptions();
        } else {
          feedback(el("clubFormFeedback"), "Lỗi: " + res.errors.join("; "), true);
        }
      });
    });

    el("adminStudentSearch").addEventListener(
      "input",
      debounce(() => {
        adminStudentPage = 1;
        loadAdminStudents();
      }, 250)
    );

    el("btnAdminPrevPage").addEventListener("click", () => {
      if (adminStudentPage > 1) {
        adminStudentPage -= 1;
        loadAdminStudents();
      }
    });
    el("btnAdminNextPage").addEventListener("click", () => {
      adminStudentPage += 1;
      loadAdminStudents();
    });

    el("btnBulkAssign").addEventListener("click", () => {
      const ids = Array.from(document.querySelectorAll(".admin-row-checkbox:checked")).map(
        (cb) => cb.dataset.studentId
      );
      const group = el("bulkReserveGroupInput").value.trim();
      if (!ids.length) {
        showToast("Chưa tick học sinh nào.", "error");
        return;
      }
      callApi("bulk_set_reserve_group", ids, group).then((res) => {
        if (res.ok) {
          showToast(`Đã gán cho ${res.data.n_updated} học sinh.`, "success");
          loadAdminStudents();
          loadReserveGroupOptions();
        } else {
          showToast("Lỗi gán hàng loạt: " + res.errors.join("; "), "error");
        }
      });
    });
  }

  /* ------------------------------------------------------------------ *
   * 7. TAB 5 — CHẤM ĐIỂM (MÙ)
   * ------------------------------------------------------------------ */

  let currentScoringClub = null;

  function loadScoringTab() {
    el("scoringWorkArea").hidden = true;
    currentScoringClub = null;
    loadScoringOverview();
  }

  function loadScoringOverview() {
    callApi("get_scoring_overview").then((res) => {
      const body = el("scoringOverviewBody");
      const emptyState = el("scoringOverviewEmpty");
      clear(body);
      const withApplicants = res.ok ? res.data.filter((c) => c.n_applicants > 0) : [];
      if (!res.ok || !withApplicants.length) {
        emptyState.hidden = false;
        return;
      }
      emptyState.hidden = true;
      withApplicants.forEach((c) => {
        const pct = c.n_applicants > 0 ? Math.round((c.n_scored / c.n_applicants) * 100) : 0;
        const tr = document.createElement("tr");
        const tdProgress = document.createElement("td");
        tdProgress.innerHTML =
          `<span class="scoring-progress-bar"><span class="scoring-progress-fill" style="width:${pct}%"></span></span>` +
          `${c.n_scored}/${c.n_applicants}`;
        tr.innerHTML = `<td>${esc(c.club_id)}</td><td>${esc(c.name)}</td><td>${esc(c.n_applicants)}</td>`;
        tr.appendChild(tdProgress);
        const tdAction = document.createElement("td");
        const btn = document.createElement("button");
        btn.className = "btn-row-link";
        btn.textContent = "Chấm →";
        btn.addEventListener("click", () => openScoringClub(c.club_id));
        tdAction.appendChild(btn);
        tr.appendChild(tdAction);
        body.appendChild(tr);
      });
    });
  }

  function openScoringClub(clubId) {
    callApi("get_club_applicants_for_scoring", clubId).then((res) => {
      if (!res.ok) {
        showToast("Lỗi tải danh sách chấm điểm: " + res.errors.join("; "), "error");
        return;
      }
      currentScoringClub = clubId;
      el("scoringWorkArea").hidden = false;
      el("scoringClubLabel").textContent = `${res.data.club_name} (${res.data.club_id})`;

      const body = el("scoringTableBody");
      clear(body);
      res.data.applicants.forEach((a) => {
        const tr = document.createElement("tr");
        const tdInput = document.createElement("td");
        const input = document.createElement("input");
        input.type = "number";
        input.step = "0.1";
        input.className = "score-input";
        input.dataset.studentId = a.student_id;
        if (a.score !== null && a.score !== undefined) input.value = a.score;
        tdInput.appendChild(input);
        tr.innerHTML = `<td>${esc(a.student_id)}</td><td>${esc(a.name)}</td>`;
        tr.appendChild(tdInput);
        body.appendChild(tr);
      });
    });
  }

  function initScoringHandlers() {
    el("btnSaveScores").addEventListener("click", () => {
      if (!currentScoringClub) return;
      const inputs = document.querySelectorAll("#scoringTableBody .score-input");
      const scores = Array.from(inputs).map((input) => ({
        student_id: input.dataset.studentId,
        score: input.value === "" ? null : input.value,
      }));
      callApi("submit_club_scores", currentScoringClub, scores).then((res) => {
        if (res.ok) {
          feedback(el("scoringFeedback"), `Đã lưu điểm cho ${res.data.n_saved} học sinh.`, false);
          if (res.data.warnings && res.data.warnings.length) {
            showToast(res.data.warnings[0], "error");
          }
          loadScoringOverview();
        } else {
          feedback(el("scoringFeedback"), "Lỗi lưu điểm: " + res.errors.join("; "), true);
        }
      });
    });
  }

  /* ------------------------------------------------------------------ *
   * 8. KHỞI ĐỘNG
   * ------------------------------------------------------------------ */

  function init() {
    initTabs();
    initPipelineHandlers();
    initResultsHandlers();
    initFallbackHandlers();
    initAdminHandlers();
    initScoringHandlers();
    loadPipelineTab(); // tab mặc định đang mở khi khởi động
  }

  if (window.pywebview) {
    init();
  } else {
    window.addEventListener("pywebviewready", init);
    // dự phòng nếu sự kiện đã bắn trước khi script này chạy
    setTimeout(() => {
      if (window.pywebview && !document.body.dataset.appInit) {
        document.body.dataset.appInit = "1";
        init();
      }
    }, 300);
  }
})();
