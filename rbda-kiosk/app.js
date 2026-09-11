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

  /* Backend goi duoc CHUA? Tach rieng de cong khoi dong (muc 9) hoi CHINH
     dieu kien nay, chu khong viet mot luat thu hai.

     KHONG duoc chi hoi `window.pywebview`. pywebview dung doi tuong do
     TRUOC voi `api: {}` RONG (webview/js/api.js), roi mot lenh run_js THU
     HAI moi do ham vao va ban su kien (webview/js/finish.js) — hai lenh
     tach roi, tren mot luong rieng, co phan chieu Python xen giua
     (webview/util.py, generate_js_object). Trong khe ho do
     `window.pywebview` da that ma goi ham nao cung truot. Tren Windows
     viec nay con chay SAU khi trang da tai xong
     (webview/platforms/edgechromium.py, on_navigation_completed). */
  function apiSanSang(name) {
    return !!(window.pywebview && window.pywebview.api
              && typeof window.pywebview.api[name] === "function");
  }

  function callApi(name, ...args) {
    if (!apiSanSang(name)) {
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
  /* Danh sach ham "nha" cua MOI nut xac nhan 2 buoc dang song. Trang thai
     armed nam trong closure nen ben ngoai khong voi toi duoc — doi ngon
     ngu giua chung thi nut dang cho xac nhan ket lai o tieng cu. Dang ky
     ham nha vao day de nhaMoiNutXacNhan() goi duoc. */
  const nutXacNhanDangSong = [];

  function armTwoStepConfirm(button, getConfirmLabel, onConfirmed, windowMs) {
    let armed = false;
    let timer = null;

    function currentOriginalLabel() {
      const key = button.getAttribute("data-i18n");
      if (key) return t(key);
      return button.dataset.originalLabel || button.textContent;
    }

    /* Nha nhan VA nha trang thai. Nha moi nhan ma quen armed la bien nut
       hai buoc thanh nut MOT buoc — bam mot phat la xoa that. */
    function nha() {
      clearTimeout(timer);
      armed = false;
      button.textContent = currentOriginalLabel();
      button.classList.remove("is-confirming");
    }

    nutXacNhanDangSong.push({ button, nha });

    button.addEventListener("click", () => {
      if (!armed) {
        armed = true;
        button.textContent = typeof getConfirmLabel === "function" ? getConfirmLabel() : getConfirmLabel;
        button.classList.add("is-confirming");
        timer = setTimeout(nha, windowMs || 4000);
      } else {
        nha();
        onConfirmed();
      }
    });
  }

  function nhaMoiNutXacNhan() {
    /* Nut trong bang duoc tao lai moi lan ve — cai cu roi khoi DOM nhung
       van con trong mang. Bo chung di, dung goi nha() tren xac cu. */
    for (let i = nutXacNhanDangSong.length - 1; i >= 0; i--) {
      const muc = nutXacNhanDangSong[i];
      if (!muc.button.isConnected) {
        nutXacNhanDangSong.splice(i, 1);
        continue;
      }
      muc.nha();
    }
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
              if (!res.ok) resolve({ loiRaw: res.errors });
              else resolve({ text: res.data.csv_text });
            }
          );
        };
        // Loi cua chinh trinh duyet: khong co khoa i18n nao, giu nguyen chuoi.
        reader.onerror = () => resolve({ loiText: String(reader.error || "") });
        reader.readAsArrayBuffer(file);
      } else {
        reader.onload = () => resolve({ text: String(reader.result || "") });
        reader.onerror = () => resolve({ loiText: String(reader.error || "") });
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
        if (doc.loiRaw || doc.loiText) {
          importQueue.push({
            ten: file.name, text: "", kind: "", confident: false,
            candidates: [], loiRaw: doc.loiRaw, loiText: doc.loiText,
          });
          veHangDoi();
          return;
        }
        callApi("detect_csv_kind", doc.text).then((res) => {
          if (!res.ok) {
            importQueue.push({
              ten: file.name, text: doc.text, kind: "", confident: false,
              candidates: [], loiRaw: res.errors,
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

  /* Canh bao cua lan nhap gan nhat — giu DANG GOC (mang doi tuong loi),
     dich lai moi lan ve. Truoc day chung duoc dich mot lan roi nhet thang
     vao DOM, nen doi ngon ngu xong ca o canh bao ket lai o tieng cu. */
  let canhBaoNhapGanNhat = [];

  function veCanhBaoNhap() {
    const box = el("importWarnings");
    if (!box) return;
    clear(box);
    box.hidden = canhBaoNhapGanNhat.length === 0;
    canhBaoNhapGanNhat.forEach((w) => {
      const div = document.createElement("div");
      div.textContent = "• " + trErr(w);
      box.appendChild(div);
    });
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
      else if (muc.loiRaw || muc.loiText || muc.kind === "unknown") row.classList.add("is-unknown");
      else if (!muc.confident) row.classList.add("is-ambiguous");

      const trai = document.createElement("div");
      const ten = document.createElement("div");
      ten.className = "queue-file";
      ten.textContent = muc.ten;
      const chiTiet = document.createElement("div");
      chiTiet.className = "queue-detail";
      // Dich LUC VE, khong cat cau da dich. Cat cau da dich thi ve lai bao
      // nhieu lan cung ra nguyen tieng cu sau khi doi ngon ngu.
      if (muc.xong) chiTiet.textContent = t(muc.ketQuaKhoa, muc.ketQuaSo);
      else if (muc.loiRaw) chiTiet.textContent = trErrs(muc.loiRaw).join("; ");
      else if (muc.loiText) chiTiet.textContent = muc.loiText;
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
      (m) => !m.xong && !m.loiRaw && !m.loiText && m.kind && m.kind !== "unknown"
    );
    if (!canNhap.length) {
      feedback(el("feedbackImportAll"), t("feedback_no_file_selected"), true);
      return;
    }
    /* CLB truoc, roi moi den hoc sinh — xem THU_TU_NHAP. */
    canNhap.sort((a, b) => (THU_TU_NHAP[a.kind] ?? 9) - (THU_TU_NHAP[b.kind] ?? 9));

    const btn = el("btnImportAll");
    btn.disabled = true;
    canhBaoNhapGanNhat = [];
    veCanhBaoNhap();
    const canhBao = canhBaoNhapGanNhat;

    /* Nhap TUAN TU, khong song song: file CLB phai ghi xong truoc khi
       file hoc sinh doc bang clubs de kiem tra club_id. */
    canNhap
      .reduce(
        (chuoi, muc) =>
          chuoi.then(() =>
            callApi("import_csv_auto", muc.text, muc.kind).then((res) => {
              if (!res.ok) {
                muc.loiRaw = Array.isArray(res.errors) ? res.errors : [res.errors];
                return;
              }
              const d = res.data;
              muc.xong = true;
              // Cat KHOA + SO, khong cat cau da dich — xem veHangDoi().
              if (d.kind === "clubs") {
                muc.ketQuaKhoa = "queue_result_clubs";
                muc.ketQuaSo = {
                  n_created: d.n_clubs_created, n_updated: d.n_clubs_updated,
                  n_skipped: d.n_rows_skipped,
                };
              } else {
                muc.ketQuaKhoa = "queue_result_students";
                muc.ketQuaSo = {
                  n_written:
                    d.n_students_with_preferences_written ??
                    d.n_students_with_selection_written ?? 0,
                  n_created: d.n_students_created,
                  n_skipped: d.n_students_skipped,
                };
              }
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

        veCanhBaoNhap();
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
    loadDoPhu();
    loadThoiKhoaBieu(el("tkbSearch") ? el("tkbSearch").value : "");
    loadSoBocTham(el("thamSearch") ? el("thamSearch").value : "");
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
        /* Hai doan LIEN NHAU trong mot mang flex, khong chong mo len
           nhau: vang = so em vao BANG SUAT DU TRU, xanh = so em vao o
           chi tieu chung. Cong lai dung bang ti le lap day in ben phai,
           va khop voi cot "Dien trung tuyen" trong tep xuat ra.

           Ban cu ve doan vang theo reserve_capacity — tuc la chi tieu du
           tru cua CLB, mot thuoc tinh cua CLB chu khong phai dieu da xay
           ra. Chu giai ghi "Co suat du tru" nen doc len khong ai biet no
           dang noi ve cai nao. */
        const suc = c.capacity > 0 ? c.capacity : 0;
        const duTru = Math.min(c.matched_reserve || 0, c.matched);
        const chung = Math.max(0, c.matched - duTru);
        /* Tinh be rong tu SO GOC. Lam tron tung doan roi cong lai thi
           tong co the vuot 100%. */
        const phanTram = (n) => (suc > 0 ? Math.min(100, (n / suc) * 100) : 0);

        const row = document.createElement("div");
        row.className = "fill-row";
        row.innerHTML =
          `<span class="fill-name">${esc(c.name || c.club_id)}</span>` +
          `<span class="fill-track">` +
          (duTru > 0
            ? `<span class="fill-bar is-reserve" style="width:${phanTram(duTru)}%"></span>`
            : "") +
          (chung > 0
            ? `<span class="fill-bar" style="width:${phanTram(chung)}%"></span>`
            : "") +
          `</span>` +
          `<span class="fill-count">${c.matched}/${c.capacity}</span>`;
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

      /* NHIỀU BUỔI: một em có MỘT dòng cho MỖI buổi, kể cả buổi em không
         có suất. Giữ nguyên cách hiện thì bảng này phồng lên gấp số buổi
         (160 em × 5 buổi = 800 dòng, phần lớn là ô trống) và huy hiệu
         "chưa được xếp" đếm số Ô TRỐNG chứ không phải số EM trắng tay —
         593 thay vì 38, một con số vừa sai vừa đáng sợ.

         Nên ở chế độ nhiều buổi, bảng này chỉ liệt kê chỗ đã xếp THẬT, còn
         "em nào chưa có gì" đọc ở bảng Độ phủ ngay phía trên — chỗ con số
         đó có đúng nghĩa. */
      const dsBuoi = new Set(res.data.map((r) => r.buoi));
      const nhieuBuoi = dsBuoi.size > 1;
      const dong = nhieuBuoi ? res.data.filter((r) => r.club_id) : res.data;

      /* Cột "Buổi" chỉ có nghĩa khi trường dùng nhiều buổi. Một buổi mà
         vẫn hiện một cột toàn "Chưa chia buổi" là thêm việc đọc cho người
         dùng mà không thêm thông tin nào. */
      document.querySelectorAll("#view-results .cot-buoi").forEach((o) => {
        o.hidden = !nhieuBuoi;
      });

      let nUnmatched = 0;
      dong.forEach((r) => {
        const tr = document.createElement("tr");
        const clubCell = r.club_id
          ? `<span class="club-tag">${esc(r.club_name || r.club_id)}</span>`
          : `<span class="club-tag is-empty">${esc(t("not_matched_label"))}</span>`;
        if (!r.club_id) nUnmatched++;
        const tierLabel =
          r.matched_tier === "reserve" ? t("tier_reserve") : r.matched_tier === "general" ? t("tier_general") : "—";
        tr.innerHTML =
          `<td>${esc(r.student_id)}</td><td>${esc(r.name)}</td>` +
          `<td class="cot-buoi">${esc(nhanBuoi(r.buoi))}</td><td>${clubCell}</td>` +
          `<td>${esc(tierLabel)}</td><td>${esc(r.rank_in_student_pref ?? "—")}</td>`;
        body.appendChild(tr);
      });

      if (nhieuBuoi) {
        /* Huy hiệu phải nói SỐ EM không có CLB nào cả tuần. Lấy từ đúng
           nguồn đã tính điều đó thay vì suy ra từ bảng này. */
        callApi("get_do_phu").then((dp) => {
          const n = dp.ok ? dp.data.so_em_trang_tay : 0;
          badge.hidden = n <= 0;
          if (n > 0) badge.textContent = t("unmatched_badge", { n: n });
        });
      } else if (nUnmatched > 0) {
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
    if (el("tkbSearch")) {
      el("tkbSearch").addEventListener(
        "input",
        debounce((ev) => loadThoiKhoaBieu(ev.target.value), 250)
      );
    }
    if (el("thamSearch")) {
      el("thamSearch").addEventListener(
        "input",
        debounce((ev) => loadSoBocTham(ev.target.value), 250)
      );
    }
    el("btnExport").addEventListener("click", () => {
      /* Khong truyen ten file -> backend tu dat vao THU MUC TAI XUONG
         cua nguoi dung va tra ve duong dan DAY DU, de nguoi dung biet
         file nam o dau. Da co file cung ten thi them "(2)" nhu trinh
         duyet, khong ghi de. */
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
   * 5. TAB 3 — NHẬP TẠI CHỖ (KIOSK FALLBACK)
   * ------------------------------------------------------------------ */

  let currentFallbackStudent = null;
  let currentClubs = [];
  let currentRanking = [];
  let fallbackStudentPage = 1;
  const FALLBACK_PAGE_SIZE = 8;

  function loadFallbackTab() {
    fallbackStudentPage = 1;
    loadFallbackStudentList();
  }

  function initFallbackHandlers() {
    el("btnStudentSearch").addEventListener("click", () => {
      fallbackStudentPage = 1;
      loadFallbackStudentList();
    });
    el("studentSearchInput").addEventListener(
      "input",
      debounce(() => {
        fallbackStudentPage = 1;
        loadFallbackStudentList();
      }, 250)
    );
    el("btnFallbackPrevPage").addEventListener("click", () => {
      if (fallbackStudentPage > 1) {
        fallbackStudentPage -= 1;
        loadFallbackStudentList();
      }
    });
    el("btnFallbackNextPage").addEventListener("click", () => {
      fallbackStudentPage += 1;
      loadFallbackStudentList();
    });
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
        loadFallbackStudentList();
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
          loadFallbackStudentList();
        } else {
          showToast(t("toast_delete_failed_prefix", { errors: trErrs(res.errors).join("; ") }), "error");
        }
      });
    });
  }

  function loadFallbackStudentList() {
    const q = el("studentSearchInput").value.trim();
    callApi("list_students_admin", q, fallbackStudentPage, FALLBACK_PAGE_SIZE).then((res) => {
      const box = el("studentSearchResults");
      const pagination = el("fallbackStudentPagination");
      clear(box);
      if (!res.ok || !res.data.rows.length) {
        box.innerHTML = '<div class="empty-state"></div>';
        box.firstChild.textContent = t("search_no_students_found");
        pagination.hidden = true;
        return;
      }
      res.data.rows.forEach((s) => {
        const row = document.createElement("div");
        row.className = "search-result-item";
        const testedTag = `<span class="club-tag${s.n_tested ? "" : " is-empty"}">${t("fallback_tag_tested", { n: s.n_tested })}</span>`;
        const rankedTag = `<span class="club-tag${s.n_ranked ? "" : " is-empty"}">${t("fallback_tag_ranked", { n: s.n_ranked })}</span>`;
        row.innerHTML =
          `<span>${esc(s.name)}</span>` +
          `<span class="search-result-meta">${testedTag}${rankedTag}<span class="search-result-id">${esc(s.student_id)}</span></span>`;
        row.addEventListener("click", () => selectFallbackStudent(s.student_id));
        box.appendChild(row);
      });
      pagination.hidden = false;
      el("fallbackPaginationLabel").textContent = t("pagination_label", {
        page: res.data.page, total_pages: res.data.total_pages, total: res.data.total,
      });
      el("btnFallbackPrevPage").disabled = res.data.page <= 1;
      el("btnFallbackNextPage").disabled = res.data.page >= res.data.total_pages;
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
      buoiCuaClb = {};
      currentClubs.forEach((c) => { buoiCuaClb[c.club_id] = c.buoi; });
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
      /* Hien BUOI thay vi ma CLB khi truong dung nhieu buoi: o buoc nay
         hoc sinh dang quyet dinh "tuan minh kin chua", va buoi la thong
         tin giup quyet dinh — ma CLB thi khong. */
      const phu = c.buoi && c.buoi !== "__mac_dinh__" ? nhanBuoi(c.buoi) : c.club_id;
      row.innerHTML = `<span>${esc(c.name)}</span><span class="cb-club-id">${esc(phu)}</span>`;
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
    veChiBaoPhuBuoi(currentRanking);
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

  /* Da co ket qua chay chua — quyet dinh nhan xac nhan cua hai nut xoa
     noi ro "mat ca ket qua da chay" hay khong. Doc mot lan luc mo tab
     vi armTwoStepConfirm goi nhan dong bo, khong cho duoc promise. */
  let adminCoKetQua = false;

  /* ------------------------------------------------------------------ *
   * 8b. NHIỀU BUỔI SINH HOẠT TRONG TUẦN
   * ------------------------------------------------------------------ *
   * Toàn bộ phần này TỰ ẨN khi trường chưa khai buổi nào. Một trường chỉ
   * tổ chức một buổi phải thấy đúng màn hình như trước — không ai bị bắt
   * học một khái niệm mình chưa dùng tới.
   * ------------------------------------------------------------------ */

  /* Buổi mặc định là mã nội bộ, không phải chữ để đọc. Hiện nguyên
     "__mac_dinh__" lên màn hình thì người dùng phải đoán nó là gì. */
  function nhanBuoi(buoi) {
    if (!buoi || buoi === "__mac_dinh__") return t("buoi_chua_chia");
    return buoi;
  }

  /* Ba mức tải, cùng ngưỡng dùng cho cả bảng lẫn lịch tuần.
     Mốc nằm ở 1,0 vì tỉ lệ chọi là SỐ EM trên SỐ CHỖ: trên 1 là chắc chắn
     có em trượt, dưới 1 là chắc chắn có chỗ bỏ không. Dải 0,95–1,05 gọi là
     "vừa đủ" để một buổi cân bằng không bị tô cảnh báo chỉ vì lệch vài em.

     Ngưỡng đầu tiên viết là 0,8 — sai: một buổi 0,88× (12% số chỗ bỏ
     trống) bị gán nhãn "Vừa đủ", đúng lúc nó là buổi nên dời CLB sang. */
  function mucTai(tiLe) {
    if (tiLe === null || tiLe === undefined) return null;
    if (tiLe > 1.05) return { lop: "is-qua-tai", nhan: t("tai_buoi_qua_tai") };
    if (tiLe >= 0.95) return { lop: "is-vua-du", nhan: t("tai_buoi_vua_du") };
    return { lop: "is-con-trong", nhan: t("tai_buoi_con_trong") };
  }

  function loadBuoiOptions() {
    callApi("get_danh_sach_buoi").then((res) => {
      const list = el("buoiOptions");
      if (!list) return;
      clear(list);
      if (!res.ok) return;
      res.data.ds_buoi
        .filter((b) => b !== res.data.buoi_mac_dinh)
        .forEach((b) => {
          const opt = document.createElement("option");
          opt.value = b;
          list.appendChild(opt);
        });
    });
  }

  function loadTaiTheoBuoi() {
    const panel = el("taiBuoiPanel");
    if (!panel) return;
    callApi("get_tai_theo_buoi").then((res) => {
      const body = el("taiBuoiBody");
      clear(body);
      /* Một buổi thì bảng này không nói được gì: cả trường chỉ có một
         dòng, và "dời CLB sang buổi vắng" không còn là lời khuyên nào. */
      if (!res.ok || res.data.length < 2) {
        panel.hidden = true;
        return;
      }
      panel.hidden = false;
      res.data.forEach((r) => {
        const muc = mucTai(r.ti_le_choi);
        const tr = document.createElement("tr");
        tr.innerHTML =
          `<td>${esc(nhanBuoi(r.buoi))}</td>` +
          `<td class="num">${esc(r.so_clb)}</td>` +
          `<td class="num">${esc(r.tong_cho)}</td>` +
          `<td class="num">${esc(r.so_hoc_sinh)}</td>` +
          `<td class="num">${r.ti_le_choi === null ? "—" : esc(r.ti_le_choi) + "×"}</td>` +
          `<td>${muc ? `<span class="chip-tai ${muc.lop}">${esc(muc.nhan)}</span>` : ""}</td>`;
        body.appendChild(tr);
      });
    });
  }

  function loadLichTuan() {
    const panel = el("lichTuanPanel");
    if (!panel) return;
    Promise.all([
      callApi("get_tai_theo_buoi"),
      callApi("get_club_fill_stats"),
    ]).then(([tai, fill]) => {
      const box = el("lichTuan");
      clear(box);
      if (!tai.ok || tai.data.length < 2 || !fill.ok) {
        panel.hidden = true;
        return;
      }
      panel.hidden = false;

      const theoBuoi = {};
      fill.data.forEach((c) => {
        (theoBuoi[c.buoi] = theoBuoi[c.buoi] || []).push(c);
      });

      tai.data.forEach((b) => {
        const muc = mucTai(b.ti_le_choi);
        const cot = document.createElement("div");
        cot.className = "lich-cot";
        cot.innerHTML =
          `<div class="lich-dau ${muc && muc.lop === "is-qua-tai" ? "is-qua-tai" : ""}">` +
          `<span class="lich-buoi">${esc(nhanBuoi(b.buoi))}</span>` +
          `<span class="lich-phu">${esc(b.tong_cho)} · ${b.ti_le_choi === null ? "—" : esc(b.ti_le_choi) + "×"}</span>` +
          `</div>`;
        (theoBuoi[b.buoi] || []).forEach((c) => {
          const phanTram = c.capacity > 0
            ? Math.min(100, (c.matched / c.capacity) * 100)
            : 0;
          const o = document.createElement("div");
          o.className = "lich-o";
          o.innerHTML =
            `<span class="lich-ten">${esc(c.name || c.club_id)}</span>` +
            `<span class="lich-thanh"><span style="width:${phanTram}%"></span></span>`;
          o.title = `${c.matched}/${c.capacity}`;
          cot.appendChild(o);
        });
        box.appendChild(cot);
      });
    });
  }

  /* ---- Số bốc thăm theo buổi (thẻ Kết quả) ----

     Phần mềm xáo lại thứ tự ở MỖI buổi, nên sẽ có phụ huynh hỏi đúng câu
     "vì sao con tôi thứ Ba đứng thứ 30 mà thứ Sáu đứng thứ 120". Bảng này
     là câu trả lời — và nó không phá tính minh bạch: trường vẫn chỉ công bố
     MỘT bộ số đã khoá cộng hạt giống, thứ tự từng buổi suy ra tất định từ
     hai thứ đó nên ai cũng tính lại được. */

  function loadSoBocTham(search) {
    const panel = el("thamPanel");
    if (!panel) return;
    callApi("get_so_boc_tham_theo_buoi", search || "").then((res) => {
      /* Một buổi thì bảng này không nói thêm gì so với bộ số đã khoá; chưa
         chạy lần nào thì chưa có hạt giống nào để suy ra thứ tự. */
      if (!res.ok || !res.data.nhieu_buoi || !res.data.da_chay) {
        panel.hidden = true;
        return;
      }
      panel.hidden = false;
      const d = res.data;

      const canhBao = el("thamCachCu");
      if (canhBao) canhBao.hidden = !d.cach_cu;

      const head = el("thamHead");
      clear(head);
      head.innerHTML =
        `<th>${esc(t("th_student_id"))}</th><th>${esc(t("th_name"))}</th>` +
        d.ds_buoi.map((b) => `<th class="num">${esc(nhanBuoi(b))}</th>`).join("");

      const body = el("thamBody");
      clear(body);
      d.hoc_sinh.forEach((em) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          `<td>${esc(em.student_id)}</td><td>${esc(em.name || "")}</td>` +
          d.ds_buoi
            .map((b) => `<td class="num">${esc(em.so[b])}</td>`)
            .join("");
        body.appendChild(tr);
      });
    });
  }

  /* ---- Thời khoá biểu + độ phủ (thẻ Kết quả) ---- */

  function loadThoiKhoaBieu(search) {
    const panel = el("tkbPanel");
    if (!panel) return;
    callApi("get_thoi_khoa_bieu", search || "").then((res) => {
      if (!res.ok || res.data.ds_buoi.length < 2 || !res.data.hoc_sinh.length) {
        panel.hidden = true;
        return;
      }
      panel.hidden = false;
      const dsBuoi = res.data.ds_buoi;

      const head = el("tkbHead");
      clear(head);
      head.innerHTML =
        `<th>${esc(t("th_student_id"))}</th><th>${esc(t("th_name"))}</th>` +
        dsBuoi.map((b) => `<th>${esc(nhanBuoi(b))}</th>`).join("") +
        `<th class="num">${esc(t("tkb_so_clb"))}</th>`;

      const body = el("tkbBody");
      clear(body);
      res.data.hoc_sinh.forEach((em) => {
        const o = dsBuoi.map((b) => {
          const c = em.theo_buoi[b];
          if (!c || !c.club_id) {
            return `<td><span class="tkb-trong">—</span></td>`;
          }
          const lop = c.matched_tier === "reserve" ? " is-du-tru" : "";
          return `<td><span class="tkb-o${lop}">${esc(c.club_name || c.club_id)}</span></td>`;
        }).join("");
        const tr = document.createElement("tr");
        tr.innerHTML =
          `<td>${esc(em.student_id)}</td><td>${esc(em.name)}</td>` + o +
          `<td class="num">${esc(em.so_clb)}</td>`;
        body.appendChild(tr);
      });
    });
  }

  function loadDoPhu() {
    const panel = el("doPhuPanel");
    if (!panel) return;
    callApi("get_do_phu").then((res) => {
      if (!res.ok || res.data.ds_buoi.length < 2 || !res.data.tong_hoc_sinh) {
        panel.hidden = true;
        return;
      }
      panel.hidden = false;
      const d = res.data;
      el("doPhuTb").textContent = d.trung_binh_clb;
      el("doPhuTrangTay").textContent = d.so_em_trang_tay;

      const box = el("doPhuCot");
      clear(box);
      const lonNhat = Math.max(1, ...d.phan_bo.map((p) => p.so_em));
      d.phan_bo.forEach((p) => {
        const nhan =
          p.so_clb === 0 ? t("do_phu_0_clb")
          : p.so_clb === 1 ? t("do_phu_1_clb")
          : t("do_phu_x_clb", { n: p.so_clb });
        const dong = document.createElement("div");
        dong.className = "do-phu-dong" + (p.so_clb === 0 ? " is-trang-tay" : "");
        dong.innerHTML =
          `<span class="do-phu-nhan">${esc(nhan)}</span>` +
          `<span class="do-phu-track"><span class="do-phu-bar" ` +
          `style="width:${(p.so_em / lonNhat) * 100}%"></span></span>` +
          `<span class="do-phu-so-em">${esc(p.so_em)}</span>`;
        box.appendChild(dong);
      });
    });
  }

  /* ---- Chỉ báo phủ buổi ở màn nhập tại chỗ ---- */

  function veChiBaoPhuBuoi(dsClbDaXep) {
    const box = el("fallbackPhuBuoi");
    const hint = el("fallbackBuoiHint");
    if (!box) return;
    callApi("get_danh_sach_buoi").then((res) => {
      if (!res.ok || !res.data.nhieu_buoi) {
        box.hidden = true;
        if (hint) hint.hidden = true;
        return;
      }
      box.hidden = false;
      if (hint) hint.hidden = false;

      const dsBuoi = res.data.ds_buoi;
      const daCo = new Set(
        (dsClbDaXep || [])
          .map((cid) => buoiCuaClb[cid])
          .filter((b) => b !== undefined)
      );
      clear(box);
      dsBuoi.forEach((b) => {
        const chip = document.createElement("span");
        chip.className = "phu-buoi-chip" + (daCo.has(b) ? " is-co" : "");
        chip.textContent = nhanBuoi(b);
        box.appendChild(chip);
      });
      const tom = document.createElement("span");
      tom.className = "phu-buoi-tom";
      tom.textContent = t("fallback_phu_buoi", { n: daCo.size, tong: dsBuoi.length });
      box.appendChild(tom);
    });
  }

  /* Bảng tra club_id -> buổi, nạp cùng danh sách CLB ở màn nhập tại chỗ.
     Giữ riêng thay vì hỏi lại backend mỗi lần bấm, vì chỉ báo phủ buổi
     phải cập nhật ngay theo từng cú bấm xếp hạng. */
  let buoiCuaClb = {};

  function loadAdminTab() {
    loadAdminClubs();
    loadReserveGroupOptions();
    loadBuoiOptions();
    loadTaiTheoBuoi();
    loadLichTuan();
    adminStudentPage = 1;
    loadAdminStudents();
    callApi("get_last_run_info").then((res) => {
      adminCoKetQua = !!(res.ok && res.data);
    });
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
      const nhieuBuoi = new Set(res.data.map((c) => c.buoi || "__mac_dinh__")).size > 1;
      document.querySelectorAll("#view-admin .cot-buoi").forEach((o) => {
        o.hidden = !nhieuBuoi;
      });
      res.data.forEach((c) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          `<td>${esc(c.club_id)}</td><td>${esc(c.name)}</td><td>${esc(c.capacity)}</td>` +
          `<td>${esc(c.reserve_capacity)}</td><td>${esc(c.reserve_group || "—")}</td>` +
          `<td class="cot-buoi">${esc(nhanBuoi(c.buoi))}</td><td></td>`;
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
      const buoi = el("clubFormBuoi") ? el("clubFormBuoi").value.trim() : "";
      if (!id || !name || !capacity) {
        feedback(el("clubFormFeedback"), t("feedback_club_form_required"), true);
        return;
      }
      callApi("create_or_update_club", id, name, capacity, reserveCapacity, reserveGroup, buoi).then((res) => {
        if (res.ok) {
          feedback(el("clubFormFeedback"), t("feedback_club_saved", { club_id: id }), false);
          el("clubFormId").value = "";
          if (el("clubFormBuoi")) el("clubFormBuoi").value = "";
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

    /* --- Vung nguy hiem: xoa du lieu de lam lai tu dau --------------- *
       Chuoi "XOA" la xac nhan bat buoc o phia Python. No KHONG phai thu
       nguoi dung go — nut da co xac nhan hai buoc roi. No de mot lenh
       goi API nham (vd tu console) khong xoa duoc gi. */
    function noiNutXoa(idNut, phamVi, khoaNhanThuong, khoaNhanCoKetQua, khoaToast) {
      armTwoStepConfirm(
        el(idNut),
        () => t(adminCoKetQua ? khoaNhanCoKetQua : khoaNhanThuong),
        () => {
          callApi("reset_data", phamVi, "XOA").then((res) => {
            if (!res.ok) {
              showToast(t("feedback_error_prefix", { errors: trErrs(res.errors).join("; ") }), "error");
              return;
            }
            showToast(
              t(khoaToast, {
                n_students: res.data.n_students,
                n_clubs: res.data.n_clubs,
                n_clubs_left: res.data.n_clubs_con_lai,
                backup_name: res.data.backup_name,
              }),
              "success"
            );
            /* Phai lam moi CA nhung thu KHONG nam tren tab nay. Thanh ben
               luon hien, va sau khi xoa no van noi "Chay gan nhat: 6/6 xep
               duoc" cho mot lan chay ma du lieu da khong con — man hinh noi
               mot dieu khong dung, ngay sau thao tac nguy hiem nhat. */
            loadAdminTab();
            loadHealthReport();
            refreshDashboardStats();
            refreshSidebarStatus();
          });
        }
      );
    }

    noiNutXoa("btnResetStudents", "hoc_sinh",
              "confirm_reset_students", "confirm_reset_students_has_results",
              "toast_reset_students_done");
    noiNutXoa("btnResetAll", "tat_ca",
              "confirm_reset_all", "confirm_reset_all_has_results",
              "toast_reset_all_done");
  }

  /* ------------------------------------------------------------------ *
   * 7. TAB 5 — NHẬP ĐIỂM
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
        /* KHONG dung type="number". Trinh duyet NUOT mat dau phay va con
           bao la hop le: go "8,5" thi .value tra ve "85" va
           validity.valid === true. Diem bi nhan len 10 lan, im lang. Da
           do trong Chromium that, ca locale en-US lan vi-VN.

           Ma "8,5" la cach viet thap phan BINH THUONG cua tieng Viet —
           khong phai go nham, ma go dung thoi quen rồi máy hiểu sai.
           Backend doc bang _doc_diem() nen nhan ca dau phay lan dau cham. */
        input.type = "text";
        input.inputMode = "decimal";   // may cam ung van hien ban phim so
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

    /* Nut dang cho xac nhan ket lai o tieng cu: applyStaticText() co y bo
       qua phan tu .is-confirming de nhan hien thi khong lech khoi trang
       thai ben trong. Ly do dung, nhung cach xu ly la NHA nut ra — giong
       het cach runConfirmBar bi go o tren. */
    nhaMoiNutXacNhan();

    /* Hang cho nap tep khong thuoc tab nao nen vong lap theo tab ben duoi
       khong cham toi. Day chinh la cho nguoi dung cham vao dau tien. */
    veHangDoi();
    veCanhBaoNhap();
    const oTomTat = el("feedbackImportAll");
    if (oTomTat) oTomTat.textContent = "";

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

  /* Ham chac chan co trong PipelineAPI va init() goi ngay — dung lam phep
     thu "backend da goi duoc chua". */
  const HAM_THU = "get_last_run_info";
  const NHIP_MS = 50;
  const HIEN_DANG_CHO_SAU_MS = 400;   // duoi nguong nay khong ai kip thay
  /* Test rut ngan han cho, vi de nguyen 20 giay thi rieng ca "backend khong
     bao gio toi" phai ngoi doi 20 giay (tests/test_khoi_dong_backend.py).
     Ban chay that khong bao gio dat bien nay. */
  const HAN_MS = Number(window.__HAN_BACKEND_MS) || 20000;

  let daKhoiDong = false;
  let daNoiDangCho = false;

  /* CO DAT NGAY TRONG DAY, nen MOI duong vao deu di qua no. Cong cu dat co
     trong nhanh hen gio thoi, nen duong su kien khoi dong ma khong danh dau
     gi, roi hen gio khoi dong lan hai — va vi ca 40 cho gan su kien trong
     file nay deu dung addEventListener (khong cho nao dung .onclick), khoi
     dong hai lan la GAN DOI TOAN BO nut: mot cu bam doi ngon ngu goi setLang
     hai luot (vi->en->vi, nut trong nhu chet), mot chuoi bam hai buoc goi
     reset_data hai lan. Ca hai deu da do duoc. */
  function khoiDongMotLan() {
    if (daKhoiDong) return;
    daKhoiDong = true;
    document.body.dataset.appInit = "1";
    init();
  }

  function baoVaoOSucKhoe(cau) {
    const o = el("healthSummary");
    if (o) {
      o.className = "health-summary is-warn";
      o.textContent = cau;
    }
  }

  /* CHI HOI VONG, KHONG NGHE `pywebviewready`. Dieu kien hoi vong
     (apiSanSang) MANH HON su kien: su kien chi bao "_createApi da chay",
     con cai ta thuc su can la "ham goi duoc". Mot duong vao thi kiem chung
     duoc; hai duong vao cho cung mot viec chinh la cach loi nay sinh ra
     lan dau. Cham nhat la tre NHIP_MS, khong ai thay. */
  const batDau = Date.now();
  (function cho() {
    if (apiSanSang(HAM_THU)) {
      khoiDongMotLan();
      return;
    }
    if (Date.now() - batDau > HAN_MS) {
      baoVaoOSucKhoe(t("backend_qua_han"));
      const oDb = el("dbStatusLine");
      if (oDb) oDb.textContent = t("backend_khong_ket_noi");
      return;
    }
    if (!daNoiDangCho && Date.now() - batDau > HIEN_DANG_CHO_SAU_MS) {
      daNoiDangCho = true;
      baoVaoOSucKhoe(t("backend_dang_ket_noi"));
    }
    setTimeout(cho, NHIP_MS);
  })();
})();
