/* Simple Meridian live demo: hero numbers, simulated app screens, auto-playing guided tour.
   All data comes from assets/demo.js (built by docs/build_demo_json.py from data/demo/). */
(function () {
  "use strict";
  var D = window.SM_DEMO;
  if (!D) return;
  var PALETTE = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#6250D6", "#E34948"];
  var channels = D.summary.filter(function (r) { return !r.is_total; });
  var COLOR = {};
  channels.forEach(function (r, i) { COLOR[r.channel] = PALETTE[i % PALETTE.length]; });
  var total = D.summary.filter(function (r) { return r.is_total; })[0];
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function money(x) {
    var a = Math.abs(x), s = x < 0 ? "-" : "";
    if (a >= 1e9) return s + "$" + (a / 1e9).toFixed(1) + "B";
    if (a >= 1e6) return s + "$" + (a / 1e6).toFixed(1) + "M";
    if (a >= 1e3) return s + "$" + (a / 1e3).toFixed(1) + "K";
    return s + "$" + a.toFixed(0);
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  var byRoi = channels.slice().sort(function (a, b) { return b.roi - a.roi; });
  var best = byRoi[0], worst = byRoi[byRoi.length - 1];
  var T = D.plan_totals, gain = T.outcome_after - T.outcome_before, gainPct = gain / T.outcome_before * 100;
  var baseline = D.fit.reduce(function (a, r) { return a + r.baseline; }, 0);

  // ---------------- Hero ----------------
  var top = best.roi;
  document.getElementById("hero-roi").innerHTML = byRoi.map(function (r) {
    return '<div class="roirow"><span>' + esc(r.channel) + '</span><span class="track"><span class="fill" style="width:' +
      (r.roi / top * 100).toFixed(0) + '%;background:' + COLOR[r.channel] + '"></span></span><b>$' + r.roi.toFixed(2) + "</b></div>";
  }).join("");
  document.getElementById("hero-gain").innerHTML = "Same budget, better split: <b>+" + money(gain) + " (+" + gainPct.toFixed(1) +
    "%)</b> revenue over the last year";

  // ---------------- Charts (hand-written SVG, no libraries) ----------------
  function roiChart() {
    var rows = channels.slice().sort(function (a, b) { return b.roi - a.roi; });
    var W = 640, rowH = 34, H = rows.length * rowH + 40, left = 70, right = 20;
    var max = Math.max.apply(null, rows.map(function (r) { return r.roi_hi; })) * 1.05;
    var x = function (v) { return left + v / max * (W - left - right); };
    var s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="ROI by channel with 90% ranges">';
    s += '<line x1="' + x(1) + '" x2="' + x(1) + '" y1="8" y2="' + (H - 24) + '" stroke="#D92D20" stroke-dasharray="5 4"/>';
    s += '<text x="' + (x(1) + 4) + '" y="14" font-size="11" fill="#D92D20">break-even</text>';
    rows.forEach(function (r, i) {
      var y = 22 + i * rowH;
      s += '<text x="' + (left - 8) + '" y="' + (y + 15) + '" font-size="12" text-anchor="end" fill="#101828">' + esc(r.channel) + "</text>";
      s += '<rect x="' + left + '" y="' + y + '" width="' + (x(r.roi) - left) + '" height="20" rx="5" fill="' + COLOR[r.channel] + '"/>';
      s += '<line x1="' + x(r.roi_lo) + '" x2="' + x(r.roi_hi) + '" y1="' + (y + 10) + '" y2="' + (y + 10) + '" stroke="#344054" stroke-width="1.4"/>';
      s += '<text x="' + (x(r.roi_hi) + 6) + '" y="' + (y + 14) + '" font-size="11" fill="#5B6475">$' + r.roi.toFixed(2) + "</text>";
    });
    for (var v = 0; v <= max; v += 5) s += '<text x="' + x(v) + '" y="' + (H - 6) + '" font-size="10" text-anchor="middle" fill="#5B6475">' + v + "</text>";
    return s + "</svg>";
  }

  function donut() {
    var parts = [{ n: "Baseline", v: baseline, c: "#B8C2D6" }].concat(channels.slice().sort(function (a, b) { return b.incremental - a.incremental; })
      .map(function (r) { return { n: r.channel, v: r.incremental, c: COLOR[r.channel] }; }));
    var sum = parts.reduce(function (a, p) { return a + p.v; }, 0), R = 70, C = 2 * Math.PI * R, off = 0;
    var s = '<svg viewBox="0 0 420 200" style="max-width:520px" role="img" aria-label="Where sales came from: baseline and each channel">';
    parts.forEach(function (p) {
      var len = p.v / sum * C;
      s += '<circle cx="100" cy="100" r="' + R + '" fill="none" stroke="' + p.c + '" stroke-width="34" stroke-dasharray="' + (len - 2) + " " + (C - len + 2) +
        '" stroke-dashoffset="' + (-off) + '" transform="rotate(-90 100 100)"/>';
      off += len;
    });
    s += '<text x="100" y="98" text-anchor="middle" font-size="16" font-weight="800" fill="#101828">' + money(sum) + "</text>";
    s += '<text x="100" y="116" text-anchor="middle" font-size="10" fill="#5B6475">modeled revenue</text>';
    parts.forEach(function (p, i) {
      var y = 26 + i * 22;
      s += '<rect x="210" y="' + (y - 10) + '" width="12" height="12" rx="3" fill="' + p.c + '"/>';
      s += '<text x="228" y="' + y + '" font-size="12" fill="#101828">' + esc(p.n) + " · " + (p.v / sum * 100).toFixed(0) + "%</text>";
    });
    return s + "</svg>";
  }

  function curvesChart() {
    var names = channels.map(function (r) { return r.channel; }), cols = 3, pw = 200, ph = 120, gap = 14;
    var H = Math.ceil(names.length / cols) * (ph + 34);
    var s = '<svg viewBox="0 0 ' + (cols * pw + (cols - 1) * gap) + " " + H + '" role="img" aria-label="Response curves for each channel">';
    names.forEach(function (n, i) {
      var pts = D.curves.filter(function (r) { return r.channel === n; }).sort(function (a, b) { return a.spend - b.spend; });
      var ox = (i % cols) * (pw + gap), oy = Math.floor(i / cols) * (ph + 34) + 18;
      var mx = Math.max.apply(null, pts.map(function (p) { return p.spend; })), my = Math.max.apply(null, pts.map(function (p) { return p.mean; }));
      var X = function (v) { return ox + 6 + v / mx * (pw - 12); }, Y = function (v) { return oy + ph - v / my * (ph - 10); };
      s += '<text x="' + ox + '" y="' + (oy - 4) + '" font-size="12" font-weight="700" fill="#101828">' + esc(n) + "</text>";
      s += '<line x1="' + ox + '" x2="' + (ox + pw) + '" y1="' + (oy + ph) + '" y2="' + (oy + ph) + '" stroke="#D0D5DD"/>';
      s += '<path d="' + pts.map(function (p, j) { return (j ? "L" : "M") + X(p.spend).toFixed(1) + " " + Y(p.mean).toFixed(1); }).join("") +
        '" fill="none" stroke="' + COLOR[n] + '" stroke-width="2.5"/>';
      var now = pts.reduce(function (a, p) { return Math.abs(p.multiplier - 1) < Math.abs(a.multiplier - 1) ? p : a; }, pts[0]);
      s += '<circle cx="' + X(now.spend) + '" cy="' + Y(now.mean) + '" r="5" fill="#fff" stroke="' + COLOR[n] + '" stroke-width="2.5"/>';
    });
    return s + "</svg>";
  }

  function planChart() {
    var rows = D.plan.slice().sort(function (a, b) { return a.spend_change_pct - b.spend_change_pct; });
    var W = 640, rowH = 30, H = rows.length * rowH + 16, mid = 360, scale = 7;
    var s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Change in spend by channel">';
    s += '<line x1="' + mid + '" x2="' + mid + '" y1="4" y2="' + (H - 4) + '" stroke="#667085"/>';
    rows.forEach(function (r, i) {
      var y = 8 + i * rowH, v = r.spend_change_pct, w = Math.abs(v) * scale, up = v >= 0;
      s += '<text x="10" y="' + (y + 14) + '" font-size="12" fill="#101828">' + esc(r.channel) + "</text>";
      s += '<rect x="' + (up ? mid : mid - w) + '" y="' + y + '" width="' + w + '" height="18" rx="5" fill="' + (up ? "#2A78D6" : "#E34948") + '"/>';
      s += '<text x="' + (up ? mid + w + 6 : mid - w - 6) + '" y="' + (y + 13) + '" font-size="11" text-anchor="' + (up ? "start" : "end") +
        '" fill="#101828">' + (up ? "+" : "") + v.toFixed(0) + "%</text>";
    });
    return s + "</svg>";
  }

  // ---------------- Simulated app screens ----------------
  var Q = D.quality, G = D.geox_sample;
  var tabs = function (on) {
    return '<div class="tabs" data-t="tabs">' + ["ROI", "Contribution", "Response curves", "Model fit", "Report"].map(function (t, i) {
      return '<span data-t="tab' + i + '" class="' + (i === on ? "on" : "") + '">' + t + "</span>";
    }).join("") + "</div>";
  };
  var insightsTiles = '<div class="tiles">' +
    '<div class="tile"><div class="k">Media spend</div><div class="v">' + money(total.spend) + '</div><div class="d">' + channels.length + " channels</div></div>" +
    '<div class="tile"><div class="k">Revenue from media</div><div class="v">' + money(total.incremental) + "</div></div>" +
    '<div class="tile"><div class="k">Blended ROI</div><div class="v">' + total.roi.toFixed(2) + "×</div></div>" +
    '<div class="tile"><div class="k">Top channel</div><div class="v">' + esc(best.channel) + "</div></div></div>";
  var rowsHtml = D.sample_rows.map(function (r) {
    return "<tr><td>" + esc(r.week) + "</td><td>" + r.TV.toLocaleString() + "</td><td>" + r.Radio.toLocaleString() + "</td><td>" +
      r.Search.toLocaleString() + "</td><td>" + r.Email.toLocaleString() + "</td><td>" + r.Sales.toLocaleString() + "</td></tr>";
  }).join("");

  var SCREENS = {
    data: '<div class="kick">Step 1 of 3</div><h3>Data &amp; model</h3>' +
      '<div class="pills"><span>simple_dataset.csv</span><span>156 weeks</span><span>02 Jan 2022 → 22 Dec 2024</span></div>' +
      '<div class="tablewrap" data-t="table"><table><thead><tr><th>week</th><th>TV spend</th><th>Radio spend</th><th>Search spend</th><th>Email spend</th><th>Sales</th></tr></thead><tbody>' +
      rowsHtml + "</tbody></table></div>" +
      '<div class="tiles" data-t="fit">' +
      '<div class="tile"><div class="k">Fit (R²)</div><div class="v">' + Q.r2.toFixed(2) + '</div><div class="d">weekly variation explained</div></div>' +
      '<div class="tile"><div class="k">Error (MAPE)</div><div class="v">' + (Q.mape * 100).toFixed(1) + '%</div><div class="d">average miss per week</div></div>' +
      '<div class="tile"><div class="k">Convergence</div><div class="v">' + Q.max_rhat.toFixed(2) + '</div><div class="d up">converged</div></div></div>',
    roi: '<div class="kick">Step 2 of 3</div><h3>Insights</h3>' + insightsTiles + tabs(0) + '<div class="chart" data-t="chart">' + roiChart() + "</div>",
    contrib: '<div class="kick">Step 2 of 3</div><h3>Insights</h3>' + insightsTiles + tabs(1) + '<div class="chart" data-t="chart">' + donut() + "</div>",
    curves: '<div class="kick">Step 2 of 3</div><h3>Insights</h3>' + insightsTiles + tabs(2) + '<div class="chart" data-t="chart">' + curvesChart() + "</div>",
    plan: '<div class="kick">Step 3 of 3</div><h3>Budget plan</h3>' +
      '<div class="pills"><span>Latest year: ' + esc(T.start) + " → " + esc(T.end) + "</span><span>Max change ±30%</span><span>Same total budget</span></div>" +
      '<span class="fakebtn" data-t="optimize">Optimize budget</span>' +
      '<div class="tiles" data-t="result">' +
      '<div class="tile"><div class="k">Budget</div><div class="v">' + money(T.budget_after) + '</div><div class="d">same total</div></div>' +
      '<div class="tile"><div class="k">Incremental revenue</div><div class="v">' + money(T.outcome_after) + '</div><div class="d up">+' + gainPct.toFixed(1) + "% · +" + money(gain) + "</div></div>" +
      '<div class="tile"><div class="k">ROI</div><div class="v">' + T.roi_after.toFixed(2) + '×</div><div class="d">was ' + T.roi_before.toFixed(2) + "×</div></div></div>" +
      '<div class="chart">' + planChart() + "</div>",
    geox: '<div class="kick">Meridian GeoX <span class="new">NEW</span></div><h3>GeoX (Lift test)</h3>' +
      '<div class="callout">Made-up data for 40 regions. The campaign really returns $' + G.true_iroas.toFixed(2) + " per $1. Can GeoX find it?</div>" +
      '<span class="fakebtn" data-t="pick">Pick test regions</span> <span class="fakebtn" data-t="run">Run the test and measure</span>' +
      '<div class="tiles" data-t="gres">' +
      '<div class="tile"><div class="k">Test regions</div><div class="v">' + G.test_regions + '</div><div class="d">ads run here</div></div>' +
      '<div class="tile"><div class="k">Control regions</div><div class="v">' + G.control_regions + '</div><div class="d">no change</div></div>' +
      '<div class="tile"><div class="k">Return per $1 found</div><div class="v">$' + G.estimate.toFixed(2) + '</div><div class="d">90% range $' + G.lo.toFixed(2) + " – $" + G.hi.toFixed(2) + "</div></div>" +
      '<div class="tile"><div class="k">True value</div><div class="v">$' + G.true_iroas.toFixed(2) + '</div><div class="d up">inside the range</div></div></div>',
  };

  // Captions match utils/tour.py in the app.
  var STEPS = [
    { screen: "data", nav: "data", target: "table", title: "Step 1: the data",
      body: "Everything starts with one simple table: one row per week, with what the company spent on each channel (TV, Radio, Search…) and what it sold." },
    { screen: "data", nav: "data", target: "fit", title: "How well the model fits",
      body: "The boxes say how well the model fits. <b>" + Q.r2.toFixed(2) + "</b> means it explains " + Math.round(Q.r2 * 100) + "% of the ups and downs in weekly sales, which is very good." },
    { screen: "roi", nav: "insights", target: "chart", title: "Step 2: what each $1 brought back",
      body: "Each bar is a channel's <b>ROI</b>: the sales it brought back for every $1 spent. <b>" + esc(best.channel) + "</b> returned about <b>$" + best.roi.toFixed(2) +
        "</b>; <b>" + esc(worst.channel) + "</b> about <b>$" + worst.roi.toFixed(2) + "</b>. Bars to the right of the red dashed line paid for themselves. The thin line shows how sure the model is." },
    { screen: "contrib", nav: "insights", target: "tab1", title: "Where the sales came from",
      body: "The <b>Contribution</b> tab splits all sales into <b>Baseline</b> (sales that would happen with no ads at all: loyal customers, brand, season) and the extra each channel added on top." },
    { screen: "curves", nav: "insights", target: "chart", title: "When more money stops helping",
      body: "Each <b>response curve</b> shows what happens to sales if you spend more or less on one channel. The ringed dot is what was actually spent. <b>Steep</b> means extra budget still pays; <b>flat</b> means the channel is saturated." },
    { screen: "plan", nav: "plan", target: "optimize", title: "Step 3: a better budget",
      body: "Press <b>Optimize budget</b>. Meridian keeps the same total and moves money from saturated channels to ones that still pay back, never changing any channel by more than ±30%. Here that adds <b>+" +
        money(gain) + " (+" + gainPct.toFixed(1) + "%)</b>." },
    { screen: "geox", nav: "geox", target: "gres", title: "New: GeoX (Lift test), a real experiment",
      body: "A model learns from history, so it can be fooled. A <b>lift test</b> runs ads in some regions, keeps them off in similar ones, and measures the gap. GeoX found <b>$" +
        G.estimate.toFixed(2) + "</b> per $1 for a hidden true value of <b>$" + G.true_iroas.toFixed(2) + "</b>." },
  ];

  // ---------------- Tour engine ----------------
  var app = document.getElementById("app"), main = document.getElementById("app-main"), spot = document.getElementById("spot");
  var title = document.getElementById("t-title"), body = document.getElementById("t-body"), count = document.getElementById("t-count");
  var dotsBox = document.getElementById("t-dots"), bar = document.getElementById("t-progress"), playBtn = document.getElementById("t-play");
  var STEP_MS = 7000, i = 0, playing = !reduce, elapsed = 0, last = null, inView = false;

  Object.keys(SCREENS).forEach(function (k) {
    var div = document.createElement("div");
    div.className = "screen"; div.dataset.screen = k; div.innerHTML = SCREENS[k];
    main.appendChild(div);
  });
  STEPS.forEach(function (s, j) {
    var b = document.createElement("button");
    b.type = "button"; b.setAttribute("aria-label", "Go to step " + (j + 1) + ": " + s.title);
    b.addEventListener("click", function () { go(j); });
    dotsBox.appendChild(b);
  });

  function place() {
    var step = STEPS[i], scr = main.querySelector('.screen[data-screen="' + step.screen + '"]');
    var t = scr && scr.querySelector('[data-t="' + step.target + '"]');
    if (!t || !t.offsetParent) t = scr;
    var a = app.getBoundingClientRect(), r = t.getBoundingClientRect(), pad = 6;
    spot.style.left = (r.left - a.left - pad) + "px"; spot.style.top = (r.top - a.top - pad) + "px";
    spot.style.width = (r.width + pad * 2) + "px"; spot.style.height = (r.height + pad * 2) + "px";
  }
  function go(j) {
    i = (j + STEPS.length) % STEPS.length; elapsed = 0;
    var s = STEPS[i];
    [].forEach.call(main.children, function (c) { c.classList.toggle("on", c.dataset.screen === s.screen); });
    [].forEach.call(app.querySelectorAll("[data-nav]"), function (n) { n.classList.toggle("on", n.dataset.nav === s.nav); });
    [].forEach.call(dotsBox.children, function (d, k) { d.classList.toggle("on", k <= i); });
    count.textContent = "Guided tour · step " + (i + 1) + " of " + STEPS.length;
    title.textContent = s.title; body.innerHTML = s.body;
    bar.style.width = "0%";
    requestAnimationFrame(place);
    setTimeout(place, 400);  // again after the screen's fade-in settles
  }
  function setPlaying(p) { playing = p; playBtn.textContent = p ? "Pause" : "Play"; last = null; }
  function tick(now) {
    if (playing && inView) {
      if (last !== null) elapsed += now - last;
      last = now;
      bar.style.width = Math.min(100, elapsed / STEP_MS * 100) + "%";
      if (elapsed >= STEP_MS) go(i + 1);
    } else { last = null; }
    requestAnimationFrame(tick);
  }
  document.getElementById("t-next").addEventListener("click", function () { go(i + 1); });
  document.getElementById("t-back").addEventListener("click", function () { go(i - 1); });
  playBtn.addEventListener("click", function () { setPlaying(!playing); });
  [].forEach.call(document.querySelectorAll("[data-play]"), function (a) {
    a.addEventListener("click", function () { go(0); setPlaying(true); });
  });
  document.addEventListener("keydown", function (e) {
    if (!inView || e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (e.key === "ArrowRight") { go(i + 1); e.preventDefault(); }
    else if (e.key === "ArrowLeft") { go(i - 1); e.preventDefault(); }
    else if (e.key === " " && (tag !== "button" && tag !== "a")) { setPlaying(!playing); e.preventDefault(); }
  });
  window.addEventListener("resize", place);
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { inView = es[0].isIntersecting; }, { threshold: 0.25 }).observe(document.getElementById("tour"));
  } else { inView = true; }
  setPlaying(!reduce);
  go(0);
  requestAnimationFrame(tick);
})();
