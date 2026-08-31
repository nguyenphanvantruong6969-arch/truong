/* ==========================================================================
   app.js — logic frontend cho kiosk Phân bổ Câu lạc bộ (RB-DA)
   ==========================================================================
   Toàn bộ giao tiếp với Python đi qua window.pywebview.api.<ten_ham>(...),
   mỗi hàm trả về Promise<{ok, data, errors}> (quy ước thống nhất ở api.py).
   Không dùng alert()/confirm() ở bất cứ đâu — thay bằng toast + xác nhận
   2 bước ngay tại chỗ (đổi label nút, yêu cầu bấm lần 2).

   Song ngữ (vi/en): mọi chuỗi hiển thị đi qua I18N.t(key, params) (xem
   i18n.js) — không hardcode chuỗi tiếng Việt/Anh trực tiếp trong file
   này. Lỗi/chi tiết bước từ backend là {code, params} (xem api.py +
   i18n_errors.py) và được dịch bằng I18N.translateError(s).
   ========================================================================== */

(function () {
  "use strict";

  const t = window.I18N.t;
  const trErr = window.I18N.translateError;
  const trErrs = window.I18N.translateErrors;

  /* ------------------------------------------------------------------ *
   * 0. TIỆN ÍCH DÙNG CHUNG
   * ------------------------------------------------------------------ */

  function callApi(name, ...args) {
    if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api[name] !== "function") {
      return Promise.resolve({
        ok: false,
        data: null,
        errors: [`Backend not ready yet (${name})`],
      });
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
    const toastEl = document.createElement("div");
    toastEl.className = "toast" + (type === "error" ? " is-error" : type === "success" ? " is-success" : "");
    toastEl.textContent = message;
    stack.appendChild(toastEl);
    setTimeout(() => {
      toastEl.classList.add("is-leaving");
      setTimeout(() => toastEl.remove(), 200);
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
  // `getConfirmLabel` là hàm (không phải chuỗi cố định) và nhãn gốc được
  // đọc LẠI mỗi lần reset (qua data-i18n hoặc dataset.originalLabel) thay
  // vì chụp 1 lần lúc gắn sự kiện — để đổi ngôn ngữ giữa chừng không làm
  // nút "hồi" lại nhãn cũ khi bấm lần kế tiếp.
  function armTwoStepConfirm(button, getConfirmLabel, onConfirmed, windowMs) {
    let armed = false;
    let timer = null;

    function currentOriginalLabel() {
      const key = button.getAttribute("data-i18n");
      if (key) return t(key);
      return button.dataset.originalLabel || button.textContent;
    }

    button.addEventListener("click", () => {
      if (!armed) {
        armed = true;
        button.textContent = typeof getConfirmLabel === "function" ? getConfirmLabel() : getConfirmLabel;
        button.classList.add("is-confirming");
        timer = setTimeout(() => {
          armed = false;
          button.textContent = currentOriginalLabel();
          button.classList.remove("is-confirming");
        }, windowMs || 4000);
      } else {
        clearTimeout(timer);
        armed = false;
        button.textContent = currentOriginalLabel();
        button.classList.remove("is-confirming");
        onConfirmed();
      }
    });
  }

  function debounce(fn, ms) {
    let timer = null;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
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

  function currentTabName() {
    const active = document.querySelector(".nav-item.is-active");
    return active ? active.dataset.tab : "pipeline";
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
        line.textContent = t("last_run_line", {
          run_at: res.data.run_at,
          seed: res.data.seed,
          n_matched: res.data.n_matched,
          n_total: res.data.n_total,
        });
      } else {
        line.textContent = t("never_run");
      }
    });
    el("dbStatusLine").textContent = t("db_connected");
    /* Noi thang app dang ve cua so bang duong nao. Khong co dong nay thi
       phai mo Task Manager moi biet — va khi khong biet thi khong ai sua. */
    const oCheDo = el("cheDoHienThi");
    if (oCheDo) {
      const duPhong = window.__CHE_DO_HIEN_THI === "trinh_duyet";
      oCheDo.textContent = t(duPhong ? "display_browser" : "display_native");
      oCheDo.classList.toggle("is-fallback", duPhong);
    }
  }

  /* ------------------------------------------------------------------ *
   * 3. TAB 1 — VẬN HÀNH PIPELINE
   * ------------------------------------------------------------------ */

  /* Hang doi file da tha, cho nhap. Moi phan tu:
     { ten, text, kind, format, confident, candidates, xong, ketQua, loi } */
  let importQueue = [];

  // Bộ nhớ lần render gần nhất của stepper/log — dùng để dịch lại đúng
  // nội dung khi người dùng đổi ngôn ngữ giữa chừng (không gọi lại API).
  let lastRenderedSteps = null;
  let lastRenderedTopErrors = null;

  function loadPipelineTab() {
    refreshDashboardStats();
    refreshStbLockLine();
    refreshSidebarStatus();
    loadHealthReport();
  }

  /* ---- Cảnh báo sức khoẻ dữ liệu (pre-flight) ---- */

  function loadHealthReport() {
    callApi("get_data_health_report").then((res) => {
      const summary = el("healthSummary");
      const list = el("healthList");
      clear(list);

      if (!res.ok) {
        summary.className = "health-summary is-warn";
        summary.textContent = trErrs(res.errors).join("; ");
        return;
      }

      const d = res.data;
      if (!d.n_warnings) {
        summary.className = "health-summary is-clean";
        summary.textContent = t("health_clean");
        return;
      }

      summary.className = "health-summary is-warn";
      summary.textContent = t("health_summary", { n: d.n_warnings, n_high: d.n_high });

      const SEV_LABEL = {
        high: "health_sev_high",
        medium: "health_sev_medium",
        info: "health_sev_info",
      };
      // nghiêm trọng lên trước — người vận hành đọc từ trên xuống
      const order = { high: 0, medium: 1, info: 2 };
      d.warnings
        .slice()
        .sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9))
        .forEach((w) => {
          const row = document.createElement("div");
          row.className = "health-item sev-" + (w.severity || "info");
          const sev = document.createElement("span");
          sev.className = "health-sev";
          sev.textContent = t(SEV_LABEL[w.severity] || "health_sev_info");
          const msg = document.createElement("span");
          msg.textContent = trErr(w);
          row.appendChild(sev);
          row.appendChild(msg);
          list.appendChild(row);
        });
    });
  }

  function refreshDashboardStats() {
    callApi("get_dashboard_status").then((res) => {
      if (!res.ok) {
        showToast(t("toast_dashboard_read_failed", { errors: trErrs(res.errors).join("; ") }), "error");
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
        ? t("stb_locked_label", { locked_at: res.data.locked_at })
        : t("stb_unlocked_label");
      line.appendChild(label);

      if (res.data.is_locked) {
        const redrawBtn = document.createElement("button");
        redrawBtn.className = "redraw-toggle";
        redrawBtn.textContent = t("btn_redraw_stb");
        redrawBtn.addEventListener("click", () => promptForceRedraw());
        line.appendChild(redrawBtn);
      }
    });
  }

  let forceRedrawArmed = false;

  function promptForceRedraw() {
    if (!forceRedrawArmed) {
      forceRedrawArmed = true;
      showToast(t("toast_redraw_armed"), "error");
      setTimeout(() => {
        forceRedrawArmed = false;
      }, 20000);
    } else {
      forceRedrawArmed = false;
    }
  }

  function renderSteps(steps) {
    lastRenderedSteps = steps;
    const stepper = el("stepper");
    steps.forEach((s) => {
      const li = stepper.querySelector(`.step[data-step="${s.step}"]`);
      if (!li) return;
      li.dataset.status = s.status;
      const detail = li.querySelector(".step-detail");
      if (s.status === "running") detail.textContent = t("step_running");
      else if (s.status === "done") detail.textContent = s.detail ? trErr(s.detail) : t("step_done_default");
      else if (s.status === "error")
        detail.textContent = Array.isArray(s.detail) ? trErrs(s.detail).join(" | ") : (s.detail ? trErr(s.detail) : t("generic_error"));
    });
  }

  function resetSteps() {
    lastRenderedSteps = null;
    document.querySelectorAll("#stepper .step").forEach((li) => {
      li.dataset.status = "";
      li.querySelector(".step-detail").textContent = t("step_not_run_yet");
    });
  }

  function showLog(errors) {
    lastRenderedTopErrors = errors;
    const panel = el("logPanel");
    const box = el("logBox");
    if (!errors || !errors.length) {
      panel.hidden = true;
      box.textContent = "";
      return;
    }
    panel.hidden = false;
    box.textContent = trErrs(errors).join("\n");
  }

  function initPipelineHandlers() {
    el("btnValidate").addEventListener("click", () => {
      el("btnValidate").disabled = true;
      callApi("check_data_integrity").then((res) => {
        el("btnValidate").disabled = false;
        if (res.ok) {
          showToast(t("toast_data_valid", { n_students: res.data.n_students, n_clubs: res.data.n_clubs }), "success");
          showLog(null);
        } else {
          showToast(t("toast_data_invalid"), "error");
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

    el("btnHealthRecheck").addEventListener("click", () => loadHealthReport());

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
      msg.textContent = wantsRedraw ? t("confirm_redraw_run") : t("confirm_overwrite_run");
      bar.appendChild(msg);
      const confirmBtn = document.createElement("button");
      confirmBtn.className = "btn btn-primary";
      confirmBtn.textContent = t("btn_confirm_run");
      confirmBtn.addEventListener("click", () => {
        bar.remove();
        forceRedrawArmed = false;
        executeRun(seed, wantsRedraw);
      });
      const cancelBtn = document.createElement("button");
      cancelBtn.className = "btn btn-ghost";
      cancelBtn.textContent = t("btn_cancel");
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
          t("toast_run_success", {
            n_matched: res.data.n_matched,
            n_total: res.data.n_total,
            rounds: res.data.rounds_run,
          }),
          "success"
        );
        showLog(null);
        refreshDashboardStats();
        refreshStbLockLine();
        refreshSidebarStatus();
        if (!el("historyTable").hidden) loadRunHistory();
      } else {
        const errs = Array.isArray(res.errors) ? res.errors : res.errors && res.errors.errors ? res.errors.errors : [String(res.errors)];
        showToast(t("toast_run_failed"), "error");
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
        td.textContent = t("history_empty");
        tr.appendChild(td);
        body.appendChild(tr);
        return;
      }
      res.data.forEach((r) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          `<td>${esc(r.run_id)}</td><td>${esc(r.run_at)}</td><td>${esc(r.seed)}</td>` +
          `<td>${esc(r.rounds_run)}</td><td>${esc(r.n_matched)}</td><td>${esc(r.n_total)}</td>` +
          `<td>${r.stb_redrawn ? esc(t("yes")) : esc(t("no"))}</td>`;
        body.appendChild(tr);
      });
    });
  }

  /* ---- Nạp CSV: một vùng kéo-thả, tự nhận diện loại file ----
   *
   * Giao diện cũ có HAI ô riêng và bắt người dùng tự chọn đúng ô. Kéo
   * nhầm ô KHÔNG báo lỗi: file nguyện vọng dạng dài khớp đủ cột của ô
   * "chọn CLB muốn thi", nên nó ghi vào sai bảng và vẫn báo thành công.
   * Giờ backend tự đọc dòng tiêu đề (detect_csv_kind). Chỉ khi tiêu đề
   * KHÔNG đủ kết luận thì mới hỏi lại — không bao giờ đoán.
   */

  /* Thứ tự nhập BẮT BUỘC: CLB trước. Học sinh tham chiếu tới club_id,
     nạp học sinh khi CLB chưa có thì cả học sinh bị bỏ qua. Người dùng
     thả một lúc cả ba file thì phần mềm tự xếp đúng thứ tự này. */
  const THU_TU_NHAP = { clubs: 0, test_selection: 1, preferences: 2 };

  function initCsvImportHandlers() {
    const zone = el("dropZone");
    const input = el("fileAny");
    if (!zone || !input) return;

    zone.addEventListener("click", () => input.click());
    zone.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); input.click(); }
    });
    input.addEventListener("change", (ev) => {
      themFileVaoHangDoi(ev.target.files);
      input.value = ""; // cho phep tha lai dung file do
    });

    ["dragenter", "dragover"].forEach((e) =>
      zone.addEventListener(e, (ev) => {
        ev.preventDefault();
        zone.classList.add("is-dragover");
      })
    );
    ["dragleave", "drop"].forEach((e) =>
      zone.addEventListener(e, (ev) => {
        ev.preventDefault();
        zone.classList.remove("is-dragover");
      })
    );
    zone.addEventListener("drop", (ev) => {
      themFileVaoHangDoi(ev.dataTransfer && ev.dataTransfer.files);
    });

    el("btnImportAll").addEventListener("click", nhapTatCa);
    el("btnClearQueue").addEventListener("click", () => {
      importQueue = [];
      /* Xoa luon phan hoi va canh bao cua lan nhap truoc — de lai thi
         nguoi dung tuong ket qua do la cua danh sach dang co. */
      feedback(el("feedbackImportAll"), "", false);
      clear(el("importWarnings"));
      el("importWarnings").hidden = true;
      veHangDoi();
    });
  }

  /* Chuyen ArrayBuffer -> base64 de gui file nhi phan qua cau noi JS/Python.
     Phai cat khuc: String.fromCharCode.apply co gioi han so doi so, file
     vai tram KB la tran ngan xep. */
  function bufferSangBase64(buf) {
    const bytes = new Uint8Array(buf);
    const KHUC = 0x8000;
    let chuoi = "";
    for (let i = 0; i < bytes.length; i += KHUC) {
      chuoi += String.fromCharCode.apply(null, bytes.subarray(i, i + KHUC));
    }
    return btoa(chuoi);
  }

  function laFileExcel(ten) {
    return /\.(xlsx|xlsm)$/i.test(ten || "");
  }

  /* Doc mot file thanh TEXT CSV, du no la .csv hay .xlsx.
     Microsoft Forms xuat ra .xlsx — truoc day nguoi dung phai tu mo Excel
     va Save As CSV UTF-8, ma do lai la buoc de sai nhat (chon nham dinh
     dang thi hong het dau tieng Viet). */
  function docFileThanhCsv(file) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      if (laFileExcel(file.name)) {
        reader.onload = () => {
          callApi("xlsx_to_csv_text", bufferSangBase64(reader.result), "").then(
            (res) => {
              if (!res.ok) resolve({ loi: trErrs(res.errors).join("; ") });
              else resolve({ text: res.data.csv_text });
            }
          );
        };
        reader.onerror = () => resolve({ loi: String(reader.error || "") });
        reader.readAsArrayBuffer(file);
      } else {
        reader.onload = () => resolve({ text: String(reader.result || "") });
        reader.onerror = () => resolve({ loi: String(reader.error || "") });
        /* UTF-8 doc duoc ca file co BOM cua Excel — backend cat BOM. */
        reader.readAsText(file, "UTF-8");
      }
    });
  }

  function themFileVaoHangDoi(fileList) {
    const files = Array.prototype.slice.call(fileList || []);
    if (!files.length) return;
    files.forEach((file) => {
      docFileThanhCsv(file).then((doc) => {
        if (doc.loi) {
          importQueue.push({
            ten: file.name, text: "", kind: "", confident: false,
            candidates: [], loi: doc.loi,
          });
          veHangDoi();
          return;
        }
        callApi("detect_csv_kind", doc.text).then((res) => {
          if (!res.ok) {
            importQueue.push({
              ten: file.name, text: doc.text, kind: "", confident: false,
              candidates: [], loi: trErrs(res.errors).join("; "),
            });
          } else {
            const d = res.data;
            importQueue.push({
              ten: file.name, text: doc.text, kind: d.kind, format: d.format,
              confident: d.confident, candidates: d.candidates || [],
            });
          }
          veHangDoi();
        });
      });
    });
  }

  function tenLoai(kind) {
    return {
      clubs: t("csv_kind_clubs"),
      test_selection: t("csv_kind_test_selection"),
      preferences: t("csv_kind_preferences"),
    }[kind] || t("csv_kind_unknown_label");
  }

  function veHangDoi() {
    const box = el("importQueue");
    const actions = el("importActions");
    clear(box);
    box.hidden = importQueue.length === 0;
    actions.hidden = importQueue.length === 0;
    if (!importQueue.length) return;

    importQueue.forEach((muc, idx) => {
      const row = document.createElement("div");
      row.className = "queue-row";
      if (muc.xong) row.classList.add("is-done");
      else if (muc.loi || muc.kind === "unknown") row.classList.add("is-unknown");
      else if (!muc.confident) row.classList.add("is-ambiguous");

      const trai = document.createElement("div");
      const ten = document.createElement("div");
      ten.className = "queue-file";
      ten.textContent = muc.ten;
      const chiTiet = document.createElement("div");
      chiTiet.className = "queue-detail";
      if (muc.xong) chiTiet.textContent = muc.ketQua;
      else if (muc.loi) chiTiet.textContent = muc.loi;
      else if (muc.kind === "unknown") chiTiet.textContent = t("queue_unknown");
      else if (!muc.confident) chiTiet.textContent = t("queue_ambiguous");
      else chiTiet.textContent = t("queue_detected", { kind: tenLoai(muc.kind) });
      trai.appendChild(ten);
      trai.appendChild(chiTiet);
      row.appendChild(trai);

      /* Mo ho -> cho chon, KHONG tu doan giup. */
      if (!muc.xong && !muc.confident && muc.candidates && muc.candidates.length) {
        const sel = document.createElement("select");
        sel.className = "queue-kind-select";
        const rong = document.createElement("option");
        rong.value = "";
        rong.textContent = t("queue_pick_kind");
        sel.appendChild(rong);
        muc.candidates.forEach((c) => {
          const o = document.createElement("option");
          o.value = c;
          o.textContent = tenLoai(c);
          sel.appendChild(o);
        });
        sel.value = muc.kind || "";
        sel.addEventListener("change", () => {
          importQueue[idx].kind = sel.value;
          importQueue[idx].confident = !!sel.value;
          veHangDoi();
        });
        row.appendChild(sel);
      }
      box.appendChild(row);
    });
  }

  function nhapTatCa() {
    const canNhap = importQueue.filter(
      (m) => !m.xong && !m.loi && m.kind && m.kind !== "unknown"
    );
    if (!canNhap.length) {
      feedback(el("feedbackImportAll"), t("feedback_no_file_selected"), true);
      return;
    }
    /* CLB truoc, roi moi den hoc sinh — xem THU_TU_NHAP. */
    canNhap.sort((a, b) => (THU_TU_NHAP[a.kind] ?? 9) - (THU_TU_NHAP[b.kind] ?? 9));

    const btn = el("btnImportAll");
    btn.disabled = true;
    clear(el("importWarnings"));
    el("importWarnings").hidden = true;
    const canhBao = [];

    /* Nhap TUAN TU, khong song song: file CLB phai ghi xong truoc khi
       file hoc sinh doc bang clubs de kiem tra club_id. */
    canNhap
      .reduce(
        (chuoi, muc) =>
          chuoi.then(() =>
            callApi("import_csv_auto", muc.text, muc.kind).then((res) => {
              if (!res.ok) {
                muc.loi = trErrs(res.errors).join("; ");
                return;
              }
              const d = res.data;
              muc.xong = true;
              muc.ketQua =
                d.kind === "clubs"
                  ? t("queue_result_clubs", {
                      n_created: d.n_clubs_created, n_updated: d.n_clubs_updated,
                      n_skipped: d.n_rows_skipped,
                    })
                  : t("queue_result_students", {
                      n_written:
                        d.n_students_with_preferences_written ??
                        d.n_students_with_selection_written ?? 0,
                      n_created: d.n_students_created,
                      n_skipped: d.n_students_skipped,
                    });
              (d.warnings || []).forEach((w) => canhBao.push(w));
            })
          ),
        Promise.resolve()
      )
      .then(() => {
        btn.disabled = false;
        veHangDoi();
        const soXong = importQueue.filter((m) => m.xong).length;
        feedback(el("feedbackImportAll"), t("feedback_import_done", { n: soXong }), false);
        showToast(t("feedback_import_done", { n: soXong }), "success");

        const warnBox = el("importWarnings");
        if (canhBao.length) {
          warnBox.hidden = false;
          canhBao.forEach((w) => {
            const div = document.createElement("div");
            div.textContent = "• " + trErr(w);
            warnBox.appendChild(div);
          });
        }
        refreshDashboardStats();
        loadHealthReport(); // du lieu vua doi -> canh bao co the da khac
      });
  }

  /* ------------------------------------------------------------------ *
   * 4. TAB 2 — KẾT QUẢ
   * ------------------------------------------------------------------ */

  function loadResultsTab() {
    loadClubFillStats();
    loadMatchResults(el("resultsSearch") ? el("resultsSearch").value : "");
  }

  function loadClubFillStats() {
    callApi("get_club_fill_stats").then((res) => {
      const box = el("clubFillList");
      clear(box);
      if (!res.ok || !res.data.length) {
        box.innerHTML = '<div class="empty-state"></div>';
        box.firstChild.textContent = t("admin_club_empty");
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
          : `<span class="club-tag is-empty">${esc(t("not_matched_label"))}</span>`;
        if (!r.club_id) nUnmatched++;
        const tierLabel =
          r.matched_tier === "reserve" ? t("tier_reserve") : r.matched_tier === "general" ? t("tier_general") : "—";
        tr.innerHTML =
          `<td>${esc(r.student_id)}</td><td>${esc(r.name)}</td><td>${clubCell}</td>` +
          `<td>${esc(tierLabel)}</td><td>${esc(r.rank_in_student_pref ?? "—")}</td>`;
        body.appendChild(tr);
      });

      if (nUnmatched > 0) {
        badge.hidden = false;
        badge.textContent = t("unmatched_badge", { n: nUnmatched });
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
      /* Khong truyen ten file -> backend tu dat CANH app.db va tra ve
         duong dan DAY DU, de nguoi dung biet file nam o dau. */
      callApi("export_csv", "").then((res) => {
        if (res.ok) showToast(t("toast_export_success", {
          n_rows: res.data.n_rows, path: res.data.path,
          n_club_files: res.data.n_club_files,
        }), "success");
        else showToast(t("toast_export_failed", { errors: trErrs(res.errors).join("; ") }), "error");
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
        showToast(t("toast_need_id_and_name"), "error");
        return;
      }
      callApi("create_student_if_missing", id, name).then((res) => {
        if (!res.ok) {
          showToast(t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), "error");
          return;
        }
        showToast(res.data.created ? t("toast_student_created") : t("toast_student_exists"), "success");
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
        if (res.ok) feedback(el("testSelectionFeedback"), t("feedback_test_selection_saved", { n: res.data.n_selected }), false);
        else feedback(el("testSelectionFeedback"), t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), true);
      });
    });

    el("btnClearRanking").addEventListener("click", () => {
      currentRanking = [];
      renderRankingList();
    });

    el("btnSubmitPreferences").addEventListener("click", () => {
      if (!currentFallbackStudent) return;
      if (!currentRanking.length) {
        feedback(el("preferencesFeedback"), trErr({ code: "must_rank_at_least_one", params: {} }), true);
        return;
      }
      callApi("submit_preferences", currentFallbackStudent, currentRanking).then((res) => {
        if (res.ok) feedback(el("preferencesFeedback"), t("feedback_preferences_saved", { n: res.data.n_ranked }), false);
        else feedback(el("preferencesFeedback"), t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), true);
      });
    });

    armTwoStepConfirm(el("btnResetStudentEntry"), () => t("confirm_reset_entry"), () => {
      if (!currentFallbackStudent) return;
      callApi("reset_student_entry", currentFallbackStudent).then((res) => {
        if (res.ok) {
          showToast(t("toast_reset_done"), "success");
          selectFallbackStudent(currentFallbackStudent);
        } else {
          showToast(t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), "error");
        }
      });
    });

    armTwoStepConfirm(el("btnDeleteStudent"), () => t("confirm_delete_student"), () => {
      if (!currentFallbackStudent) return;
      const studentId = currentFallbackStudent;
      callApi("delete_student", studentId).then((res) => {
        if (res.ok) {
          showToast(t("toast_student_deleted", { student_id: studentId }), "success");
          currentFallbackStudent = null;
          el("fallbackWorkArea").hidden = true;
          el("studentSearchInput").value = "";
          clear(el("studentSearchResults"));
        } else {
          showToast(t("toast_delete_failed_prefix", { errors: trErrs(res.errors).join("; ") }), "error");
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
        box.innerHTML = '<div class="empty-state"></div>';
        box.firstChild.textContent = t("search_no_students_found");
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
        showToast(t("feedback_error_prefix", { errors: trErrs(stateRes.errors).join("; ") }), "error");
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
          showToast(trErr({ code: "duplicate_preference_in_list", params: {} }), "error");
          return;
        }
        if (currentRanking.length >= 10) {
          showToast(trErr({ code: "max_10_preferences", params: {} }), "error");
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
      removeBtn.textContent = t("btn_remove_ranked");
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
        delBtn.dataset.originalLabel = t("btn_delete");
        delBtn.textContent = delBtn.dataset.originalLabel;
        armTwoStepConfirm(delBtn, () => t("confirm_delete_generic"), () => {
          callApi("delete_club", c.club_id).then((delRes) => {
            if (delRes.ok) {
              showToast(t("toast_club_deleted", { club_id: c.club_id }), "success");
              loadAdminClubs();
              loadReserveGroupOptions();
            } else {
              showToast(t("toast_delete_failed_prefix", { errors: trErrs(delRes.errors).join("; ") }), "error");
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

      el("adminPaginationLabel").textContent = t("pagination_label", {
        page: res.data.page,
        total_pages: res.data.total_pages,
        total: res.data.total,
      });
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
        feedback(el("clubFormFeedback"), t("feedback_club_form_required"), true);
        return;
      }
      callApi("create_or_update_club", id, name, capacity, reserveCapacity, reserveGroup).then((res) => {
        if (res.ok) {
          feedback(el("clubFormFeedback"), t("feedback_club_saved", { club_id: id }), false);
          el("clubFormId").value = "";
          el("clubFormName").value = "";
          el("clubFormCapacity").value = "";
          el("clubFormReserveCapacity").value = "0";
          el("clubFormReserveGroup").value = "";
          loadAdminClubs();
          loadReserveGroupOptions();
        } else {
          feedback(el("clubFormFeedback"), t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), true);
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
        showToast(t("toast_no_students_ticked"), "error");
        return;
      }
      callApi("bulk_set_reserve_group", ids, group).then((res) => {
        if (res.ok) {
          showToast(t("toast_bulk_assign_success", { n: res.data.n_updated }), "success");
          loadAdminStudents();
          loadReserveGroupOptions();
        } else {
          showToast(t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), "error");
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
        btn.textContent = t("btn_score_link");
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
        showToast(t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), "error");
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
          feedback(el("scoringFeedback"), t("feedback_scores_saved", { n: res.data.n_saved }), false);
          if (res.data.warnings && res.data.warnings.length) {
            showToast(trErr(res.data.warnings[0]), "error");
          }
          loadScoringOverview();
        } else {
          feedback(el("scoringFeedback"), t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), true);
        }
      });
    });
  }

  /* ------------------------------------------------------------------ *
   * 8. NGÔN NGỮ (vi/en)
   * ------------------------------------------------------------------ */

  function initLangToggle() {
    const btn = el("btnLangToggle");
    if (!btn) return;
    btn.addEventListener("click", () => {
      window.I18N.setLang(window.I18N.getLang() === "vi" ? "en" : "vi");
    });
  }

  // Nội dung tĩnh (data-i18n) tự cập nhật qua applyStaticText(). Nội dung
  // ĐỘNG (đã render dựa trên ngôn ngữ cũ) cần được yêu cầu vẽ lại — dùng
  // lại loader của tab đang mở (đọc từ SQLite, rẻ) thay vì lưu cache toàn
  // bộ dữ liệu. stepper/log không gắn với tab nào nên xử lý riêng.
  function reapplyDynamicTextForLangChange() {
    // The run-confirmation bar (runPipelineFlow) is a safety-critical
    // dialog for an irreversible action (overwrite results / redraw STB)
    // built once from plain textContent, not data-i18n — leaving it up
    // would show a stale-language confirmation next to a freshly
    // retranslated page. Dismiss it (same as Cancel) rather than risk a
    // mismatched-language safety prompt; the user just re-clicks "Run".
    const confirmBar = el("runConfirmBar");
    if (confirmBar) {
      confirmBar.remove();
      forceRedrawArmed = false;
    }

    refreshSidebarStatus();
    if (lastRenderedSteps) renderSteps(lastRenderedSteps);
    if (lastRenderedTopErrors) showLog(lastRenderedTopErrors);

    const tab = currentTabName();
    if (tab === "pipeline") {
      refreshDashboardStats();
      refreshStbLockLine();
      loadHealthReport();
      if (!el("historyTable").hidden) loadRunHistory();
    } else if (tab === "results") {
      loadResultsTab();
    } else if (tab === "admin") {
      loadAdminTab();
    } else if (tab === "scoring") {
      loadScoringOverview();
      if (currentScoringClub) openScoringClub(currentScoringClub);
    }
    // Tab "fallback": nhãn tĩnh đã tự cập nhật; các lưới club dùng tên
    // club do trường nhập (dữ liệu, không phải chuỗi giao diện) nên
    // không cần vẽ lại.
  }

  /* ------------------------------------------------------------------ *
   * 9. KHỞI ĐỘNG
   * ------------------------------------------------------------------ */

  function init() {
    window.I18N.applyStaticText();
    initLangToggle();
    window.addEventListener("langchange", reapplyDynamicTextForLangChange);
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
