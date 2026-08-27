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

  function callApi(name, ...args) {
    if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api[name] !== "function") {
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

  if (window.pywebview) {
    init();
  } else {
    window.addEventListener("pywebviewready", init);
    setTimeout(() => {
      if (window.pywebview && !document.body.dataset.appInit) {
        document.body.dataset.appInit = "1";
        init();
      }
    }, 300);
  }
})();
