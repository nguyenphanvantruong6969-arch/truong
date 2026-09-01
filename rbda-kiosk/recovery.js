/* ==========================================================================
   recovery.js — logic cho recovery.html, màn hình CHỈ hiện khi PipelineAPI
   không khởi tạo được (app.db hỏng/mất, xem main.py + recovery.py).
   Cùng quy ước với app.js: mọi hàm backend trả Promise<{ok, data, errors}>,
   mọi chuỗi hiển thị qua I18N, không dùng alert()/confirm() native.
   ========================================================================== */

(function () {
  "use strict";

  const t = window.I18N.t;
  const trErr = window.I18N.translateError;

  /* Xem chu thich day du o app.js: pywebview dung `window.pywebview` TRUOC
     voi `api: {}` RONG, mot lenh run_js THU HAI moi do ham vao. Hoi
     `window.pywebview` khong thoi la hoi sai cau hoi. */
  function apiSanSang(name) {
    return !!(window.pywebview && window.pywebview.api
              && typeof window.pywebview.api[name] === "function");
  }

  function callApi(name, ...args) {
    if (!apiSanSang(name)) {
      return Promise.resolve({ ok: false, data: null, errors: [`Backend not ready yet (${name})`] });
    }
    return window.pywebview.api[name](...args).catch((e) => ({ ok: false, data: null, errors: [String(e)] }));
  }

  function el(id) {
    return document.getElementById(id);
  }

  function fmtBytes(n) {
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  }

  function renderBackups(backups) {
    const tbody = el("backupsTableBody");
    const table = el("backupsTable");
    const noMsg = el("noBackupsMsg");
    tbody.innerHTML = "";
    if (!backups || backups.length === 0) {
      table.hidden = true;
      noMsg.hidden = false;
      noMsg.textContent = trErr({ code: "recovery_no_backups" });
      return;
    }
    table.hidden = false;
    noMsg.hidden = true;
    for (const b of backups) {
      const tr = document.createElement("tr");
      const tdName = document.createElement("td");
      tdName.textContent = b.name;
      const tdTime = document.createElement("td");
      tdTime.textContent = b.modified_at;
      const tdSize = document.createElement("td");
      tdSize.textContent = fmtBytes(b.size_bytes);
      tr.appendChild(tdName);
      tr.appendChild(tdTime);
      tr.appendChild(tdSize);
      tbody.appendChild(tr);
    }
  }

  function showStatus(kind, text) {
    const box = el("recoveryStatus");
    box.className = `recovery-status is-${kind}`;
    box.textContent = text;
    box.hidden = false;
  }

  function clearStatus() {
    const box = el("recoveryStatus");
    box.hidden = true;
    box.textContent = "";
  }

  function setButtonsDisabled(disabled) {
    el("btnRestoreBackup").disabled = disabled;
    el("btnStartFresh").disabled = disabled;
  }

  // Xac nhan 2 buoc rut gon (khong phu thuoc app.js — recovery.html la
  // trang doc lap, khong load app.js).
  function armTwoStepConfirm(button, getConfirmLabel, onConfirmed, windowMs) {
    let armed = false;
    let timer = null;
    function originalLabel() {
      const key = button.getAttribute("data-i18n");
      return key ? t(key) : button.textContent;
    }
    button.addEventListener("click", () => {
      if (!armed) {
        armed = true;
        button.textContent = typeof getConfirmLabel === "function" ? getConfirmLabel() : getConfirmLabel;
        button.classList.add("is-confirming");
        timer = setTimeout(() => {
          armed = false;
          button.textContent = originalLabel();
          button.classList.remove("is-confirming");
        }, windowMs || 4000);
      } else {
        clearTimeout(timer);
        armed = false;
        button.textContent = originalLabel();
        button.classList.remove("is-confirming");
        onConfirmed();
      }
    });
  }

  function refreshStatus() {
    return callApi("get_status").then((res) => {
      if (!res.ok) return;
      el("initErrorDetail").textContent = res.data.init_error || "";
      renderBackups(res.data.backups);
    });
  }

  function init() {
    window.I18N.applyStaticText();
    document.title = t("recovery_title");
    window.addEventListener("langchange", () => {
      document.title = t("recovery_title");
    });

    el("btnLangToggle").addEventListener("click", () => {
      window.I18N.setLang(window.I18N.getLang() === "vi" ? "en" : "vi");
    });

    refreshStatus();

    el("btnRestoreBackup").addEventListener("click", () => {
      clearStatus();
      setButtonsDisabled(true);
      showStatus("pending", t("recovery_working"));
      callApi("restore_from_backup").then((res) => {
        setButtonsDisabled(false);
        if (res.ok) {
          showStatus("success", `${trErr(res.data.detail)} ${t("recovery_please_restart")}`);
        } else {
          showStatus("error", trErr(res.errors[0]));
          refreshStatus();
        }
      });
    });

    armTwoStepConfirm(el("btnStartFresh"), () => t("confirm_start_fresh"), () => {
      clearStatus();
      setButtonsDisabled(true);
      showStatus("pending", t("recovery_working"));
      callApi("start_fresh").then((res) => {
        setButtonsDisabled(false);
        if (res.ok) {
          showStatus("success", `${trErr(res.data.detail)} ${t("recovery_please_restart")}`);
        } else {
          showStatus("error", trErr(res.errors[0]));
          refreshStatus();
        }
      });
    });
  }

  /* CUNG BAN VA VOI app.js muc 9 — day la ban sao nguyen van cua cung mot
     cong khoi dong, va man hinh nay la man hinh hien ra KHI CSDL DA HONG:
     hong not o day thi khong con duong nao. Rieng o day, khoi dong hai lan
     con lam nut "Bat dau lai voi CSDL trong" (start_fresh) chay HAI LUOT
     cho mot chuoi bam hai buoc. */
  const HAM_THU = "get_status";
  const NHIP_MS = 50;
  const HIEN_DANG_CHO_SAU_MS = 400;
  const HAN_MS = Number(window.__HAN_BACKEND_MS) || 20000;

  let daKhoiDong = false;
  let daNoiDangCho = false;

  function khoiDongMotLan() {
    if (daKhoiDong) return;
    daKhoiDong = true;
    document.body.dataset.appInit = "1";
    init();
  }

  const batDau = Date.now();
  (function cho() {
    if (apiSanSang(HAM_THU)) {
      khoiDongMotLan();
      return;
    }
    if (Date.now() - batDau > HAN_MS) {
      showStatus("error", t("backend_qua_han"));
      return;
    }
    if (!daNoiDangCho && Date.now() - batDau > HIEN_DANG_CHO_SAU_MS) {
      daNoiDangCho = true;
      showStatus("pending", t("backend_dang_ket_noi"));
    }
    setTimeout(cho, NHIP_MS);
  })();
})();
