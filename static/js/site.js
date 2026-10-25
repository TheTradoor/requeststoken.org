(function () {
  const POLL_MS = 30000;

  function text(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value == null || value === "" ? "—" : String(value);
  }

  function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(value);
    }
    return new Promise(function (resolve, reject) {
      const area = document.createElement("textarea");
      area.value = value;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.left = "-9999px";
      document.body.appendChild(area);
      area.select();
      try {
        if (document.execCommand("copy")) resolve();
        else reject(new Error("copy failed"));
      } catch (error) {
        reject(error);
      } finally {
        area.remove();
      }
    });
  }

  const copyButton = document.getElementById("copy-contract");
  const copyStatus = document.getElementById("copy-status");
  if (copyButton) {
    copyButton.addEventListener("click", function () {
      const value = copyButton.getAttribute("data-contract") || "";
      copyText(value).then(function () {
        copyButton.textContent = "Copied";
        copyButton.classList.add("is-copied");
        if (copyStatus) copyStatus.textContent = "Contract address copied.";
      }).catch(function () {
        copyButton.textContent = "Select it";
        if (copyStatus) {
          copyStatus.textContent = "Could not copy automatically. Select the contract address and copy it.";
        }
      });
      window.setTimeout(function () {
        copyButton.textContent = "Copy";
        copyButton.classList.remove("is-copied");
      }, 1600);
    });
  }


  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      copyText(button.getAttribute("data-copy") || "").then(function () {
        button.textContent = "Copied";
        button.classList.add("is-copied");
        if (copyStatus) copyStatus.textContent = "Address copied.";
      }).catch(function () {
        button.textContent = "Failed";
      });
      window.setTimeout(function () {
        button.textContent = "Copy";
        button.classList.remove("is-copied");
      }, 1600);
    });
  });

  const lock = document.getElementById("lock-progress");
  if (lock) {
    const start = Date.parse(lock.getAttribute("data-start"));
    const end = Date.parse(lock.getAttribute("data-end"));
    const now = Date.now();
    const pct = Math.max(0, Math.min(1, (now - start) / (end - start)));
    const fill = document.getElementById("lock-fill");
    if (fill) fill.style.width = (pct * 100).toFixed(1) + "%";
    const days = Math.max(0, Math.ceil((end - now) / 86400000));
    text("lock-left", days > 0 ? days + " days to unlock" : "Unlock date reached");
  }

  function applyToken(data) {
    const ready = Boolean(data && data.available);
    const grid = document.getElementById("market-grid");
    const missing = document.getElementById("market-unavailable");
    if (grid) grid.hidden = !ready;
    if (missing) {
      missing.hidden = ready;
      if (!ready) {
        missing.textContent = (data && data.detail) || "Market data is temporarily unavailable.";
      }
    }
    if (!data) return;
    text("stat-mcap", data.market_cap_display);
    text("stat-price", data.price_display);
    text("stat-native", data.price_native_display);
    text("stat-liquidity", data.liquidity_display);
    text("stat-volume", data.volume_display);
    text("stat-activity", data.activity_display);
    const change = document.getElementById("stat-change");
    if (change) {
      change.textContent = data.change_display || "—";
      change.classList.remove("up", "down", "flat");
      change.classList.add(data.change_direction || "flat");
    }
    const link = document.getElementById("pair-link");
    if (link && typeof data.pair_url === "string" && data.pair_url.indexOf("https://") === 0) {
      link.href = data.pair_url;
    }
    const listed = document.getElementById("listed-on");
    if (listed) {
      listed.textContent = data.listed_on ? "Pair listed " + data.listed_on + "." : "";
    }
    text("market-status", data.status_display || data.detail || "");
  }

  function refreshToken() {
    fetch("/api/token", {
      headers: { Accept: "application/json" },
      cache: "no-store",
    }).then(function (response) {
      if (!response.ok) throw new Error(String(response.status));
      return response.json();
    }).then(applyToken).catch(function () {
      const status = document.getElementById("market-status");
      if (status) {
        status.textContent = "Could not refresh market data. Showing the last figures on this page.";
      }
    });
  }

  window.setInterval(function () {
    if (document.visibilityState === "visible") refreshToken();
  }, POLL_MS);

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") refreshToken();
  });

  const NS = "http://www.w3.org/2000/svg";

  function el(name, attrs) {
    const node = document.createElementNS(NS, name);
    Object.keys(attrs).forEach(function (key) {
      node.setAttribute(key, attrs[key]);
    });
    return node;
  }

  function prettyDate(iso) {
    const parts = String(iso).split("-");
    if (parts.length !== 3) return iso;
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const month = months[Number(parts[1]) - 1] || parts[1];
    return Number(parts[2]) + " " + month + " " + parts[0];
  }

  function compact(value) {
    const absolute = Math.abs(value);
    if (absolute >= 1e9) return (value / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
    if (absolute >= 1e6) {
      const digits = absolute >= 1e7 ? 0 : 1;
      return (value / 1e6).toFixed(digits).replace(/\.0$/, "") + "M";
    }
    if (absolute >= 1e3) return Math.round(value / 1e3) + "k";
    return String(Math.round(value));
  }

})();
