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

  function fullCount(value) {
    return new Intl.NumberFormat("en-US").format(value);
  }

  function niceCeiling(value) {
    if (!(value > 0)) return 1;
    const pow = Math.pow(10, Math.floor(Math.log10(value)));
    const steps = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12];
    for (let i = 0; i < steps.length; i += 1) {
      const ceiling = steps[i] * pow;
      if (ceiling >= value * 1.12) return ceiling;
    }
    return 12 * pow;
  }

  function drawChart(series) {
    const svg = document.getElementById("chart");
    const tip = document.getElementById("chart-tip");
    const wrap = svg ? svg.parentNode : null;
    if (!svg || !wrap) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    if (!series || series.length === 0) {
      svg.hidden = true;
      return;
    }

    const width = 720;
    const height = 260;
    const pad = { l: 52, r: 14, t: 18, b: 32 };
    const innerW = width - pad.l - pad.r;
    const innerH = height - pad.t - pad.b;
    const max = Math.max.apply(null, series.map(function (item) { return item.downloads; }));
    const ceiling = niceCeiling(max);
    const step = series.length === 1 ? 0 : innerW / (series.length - 1);

    const points = series.map(function (item, index) {
      const x = pad.l + step * index;
      const y = pad.t + innerH - (item.downloads / ceiling) * innerH;
      return { x: x, y: y, date: item.date, downloads: item.downloads };
    });

    function line(y) {
      svg.appendChild(el("line", {
        x1: pad.l, x2: width - pad.r, y1: y, y2: y,
        stroke: "rgba(239,232,214,0.12)", "stroke-width": "1",
      }));
    }

    [0, 0.5, 1].forEach(function (fraction) {
      const y = pad.t + innerH - innerH * fraction;
      line(y);
      svg.appendChild(el("text", {
        x: pad.l - 8,
        y: y + 4,
        fill: "#a39c8a",
        "font-size": "11",
        "font-family": "IBM Plex Mono, ui-monospace, monospace",
        "text-anchor": "end",
      })).textContent = compact(ceiling * fraction);
    });

    const area = points.map(function (point) { return point.x + "," + point.y; }).join(" ");
    const baseline = (width - pad.r) + "," + (pad.t + innerH) + " " + pad.l + "," + (pad.t + innerH);
    svg.appendChild(el("polygon", {
      points: area + " " + baseline,
      fill: "rgba(142,184,204,0.38)",
    }));
    svg.appendChild(el("polyline", {
      points: area,
      fill: "none",
      stroke: "#d5e8f2",
      "stroke-width": "2.5",
      "stroke-linejoin": "round",
      "stroke-linecap": "round",
    }));

    const labels = [points[0], points[Math.floor((points.length - 1) / 2)], points[points.length - 1]];
    const seen = {};
    labels.forEach(function (point) {
      if (!point || seen[point.date]) return;
      seen[point.date] = true;
      const anchor = point === points[0] ? "start" : point === points[points.length - 1] ? "end" : "middle";
      svg.appendChild(el("text", {
        x: point.x,
        y: height - 8,
        fill: "#a39c8a",
        "font-size": "11",
        "font-family": "IBM Plex Mono, ui-monospace, monospace",
        "text-anchor": anchor,
      })).textContent = prettyDate(point.date);
    });

    const last = points[points.length - 1];
    svg.appendChild(el("circle", {
      cx: last.x, cy: last.y, r: "3.5", fill: "#e4c36a",
    }));
    const dot = el("circle", { r: "4.5", fill: "#e4c36a", stroke: "#101410", "stroke-width": "2", visibility: "hidden" });
    svg.appendChild(dot);
    svg.hidden = false;

    function nearest(localX) {
      let best = points[0];
      let bestDist = Infinity;
      points.forEach(function (point) {
        const dist = Math.abs(point.x - localX);
        if (dist < bestDist) {
          best = point;
          bestDist = dist;
        }
      });
      return best;
    }

    function show(event) {
      const matrix = svg.getScreenCTM();
      if (!matrix || !tip) return;
      const probe = svg.createSVGPoint();
      probe.x = event.clientX;
      probe.y = event.clientY;
      const local = probe.matrixTransform(matrix.inverse());
      const point = nearest(local.x);
      dot.setAttribute("cx", point.x);
      dot.setAttribute("cy", point.y);
      dot.setAttribute("visibility", "visible");
      tip.hidden = false;
      tip.textContent = prettyDate(point.date) + " · " + fullCount(point.downloads);
      const bounds = wrap.getBoundingClientRect();
      tip.style.left = (event.clientX - bounds.left) + "px";
      tip.style.top = (event.clientY - bounds.top) + "px";
    }

    function hide() {
      dot.setAttribute("visibility", "hidden");
      if (tip) tip.hidden = true;
    }

    wrap.addEventListener("pointermove", show);
    wrap.addEventListener("pointerleave", hide);
  }

  const statsNode = document.getElementById("stats-data");
  if (statsNode) {
    try {
      const stats = JSON.parse(statsNode.textContent || "{}");
      drawChart(stats.series || []);
    } catch (error) {
      drawChart([]);
    }
  }
})();
