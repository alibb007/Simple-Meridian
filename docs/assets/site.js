/* Simple Meridian live demo: the guided tour is the whole page. Simulated app screens, a spotlight and a caption.
   All data comes from assets/demo.js (built by scripts/site/build_site_data.py from data/demo/). */
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

  // ---------------- GeoX sample (real results from scripts/demo/build_geox_demo.py) ----------------
  var GX = D.geox, gxTest = {}; GX.treatment.forEach(function (g) { gxTest[g] = 1; });
  function regionGrid() {
    var names = Object.keys(GX.geo_size).sort(), s = '<svg viewBox="0 0 400 210" role="img" aria-label="40 regions: ' + GX.treatment.length + ' test, ' + GX.control.length + ' control">';
    names.forEach(function (n, k) {
      var x = 10 + (k % 8) * 48, y = 10 + Math.floor(k / 8) * 40, t = gxTest[n];
      s += '<rect x="' + x + '" y="' + y + '" width="42" height="34" rx="7" fill="' + (t ? "#6D4AE8" : "#DCE7FF") + '"/>';
      s += '<text x="' + (x + 21) + '" y="' + (y + 21) + '" font-size="10" text-anchor="middle" fill="' + (t ? "#fff" : "#1D3A8A") + '">' + n.replace("Region ", "") + "</text>";
    });
    return s + "</svg>";
  }
  function lineChart(series, opts) {
    // series: [{v: [...], color, dash}], all the same length; opts.shadeFrom: index where the test starts
    var W = 640, H = 210, L = 46, R = 10, T = 12, B = 26, n = series[0].v.length;
    var all = [].concat.apply([], series.map(function (s) { return s.v.filter(function (x) { return x != null; }); }));
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all), pad = (hi - lo) * 0.08; lo -= pad; hi += pad;
    var X = function (k) { return L + k / (n - 1) * (W - L - R); }, Y = function (v) { return T + (hi - v) / (hi - lo) * (H - T - B); };
    var s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(opts.label) + '">';
    if (opts.shadeFrom != null) {
      s += '<rect x="' + X(opts.shadeFrom) + '" y="' + T + '" width="' + (X(n - 1) - X(opts.shadeFrom)) + '" height="' + (H - T - B) + '" fill="#F4F0FF"/>';
      s += '<text x="' + (X(opts.shadeFrom) + 6) + '" y="' + (T + 14) + '" font-size="11" fill="#6941C6">ads running</text>';
    }
    [0, .5, 1].forEach(function (f) { var v = lo + (hi - lo) * f; s += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(v) + '" y2="' + Y(v) + '" stroke="#EDF0F6"/>' +
      '<text x="' + (L - 6) + '" y="' + (Y(v) + 4) + '" font-size="10" text-anchor="end" fill="#5B6475">' + opts.fmt(v) + "</text>"; });
    series.forEach(function (sr) {
      var d = "", started = false;
      sr.v.forEach(function (v, k) { if (v == null) { started = false; return; } d += (started ? "L" : "M") + X(k).toFixed(1) + " " + Y(v).toFixed(1); started = true; });
      s += '<path d="' + d + '" fill="none" stroke="' + sr.color + '" stroke-width="2"' + (sr.dash ? ' stroke-dasharray="6 4"' : "") + "/>";
    });
    s += '<text x="' + L + '" y="' + (H - 6) + '" font-size="10" fill="#5B6475">' + esc(opts.from) + '</text><text x="' + (W - R) + '" y="' + (H - 6) + '" font-size="10" text-anchor="end" fill="#5B6475">' + esc(opts.to) + "</text>";
    return s + "</svg>";
  }
  var legend = function (items) { return '<div class="lgd">' + items.map(function (it) { return '<span><i style="background:' + it[1] + (it[2] ? ";background:repeating-linear-gradient(90deg," + it[1] + " 0 6px,transparent 6px 9px)" : "") + '"></i>' + it[0] + "</span>"; }).join("") + "</div>"; };
  var gxPre = (function () {
    var t = GX.pre_groups.test, c = GX.pre_groups.control, mt = t.reduce(function (a, b) { return a + b; }, 0) / t.length, mc = c.reduce(function (a, b) { return a + b; }, 0) / c.length;
    return lineChart([{ v: c.map(function (v) { return v / mc * 100; }), color: "#7DA2F0" }, { v: t.map(function (v) { return v / mt * 100; }), color: "#6D4AE8" }],
      { label: "Daily sales before the test, test vs control regions, indexed to 100", fmt: function (v) { return v.toFixed(0); }, from: GX.pre_groups.date[0], to: GX.pre_groups.date[GX.pre_groups.date.length - 1] });
  })();
  var gxCf = (function () {
    var rows = GX.counterfactual.data, start = rows.findIndex(function (r) { return r[0].slice(0, 10) >= GX.start; });
    return lineChart([{ v: rows.map(function (r) { return r[2]; }), color: "#98A2B3", dash: true }, { v: rows.map(function (r) { return r[1]; }), color: "#6D4AE8" }],
      { label: "Test regions: actual sales vs what GeoX expects without the ads", shadeFrom: start, fmt: function (v) { return money(v); }, from: rows[0][0].slice(0, 10), to: rows[rows.length - 1][0].slice(0, 10) });
  })();
  var gxCum = GX.cumulative.data[GX.cumulative.data.length - 1];
  function rangeBar(lo, hi, max, color) {
    return '<div class="rbar"><span style="left:' + (lo / max * 100) + "%;width:" + ((hi - lo) / max * 100) + "%;background:" + color + '"></span></div>';
  }

  // ---------------- Simulated app screens ----------------
  // Region ids (data-t) match the app's tour anchors in utils/tour.py.
  var Q = D.quality;
  var tabs = function (on) {
    return '<div class="tabs">' + ["ROI", "Contribution", "Response curves", "Model fit", "Report"].map(function (t, k) {
      return '<span class="' + (k === on ? "on" : "") + '">' + t + "</span>";
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

  function sparkline() {
    var pts = D.fit.map(function (r) { return r.actual; }), mx = Math.max.apply(null, pts), mn = Math.min.apply(null, pts);
    var d = pts.map(function (v, k) { return (k ? "L" : "M") + (k / (pts.length - 1) * 600).toFixed(1) + " " + (70 - (v - mn) / (mx - mn) * 60).toFixed(1); }).join("");
    return '<svg viewBox="0 0 600 76" role="img" aria-label="Weekly sales over three years"><path d="' + d + '" fill="none" stroke="#2459E8" stroke-width="2"/></svg>';
  }
  function channelCards() {
    return channels.map(function (r) {
      var n = r.channel;
      return '<div class="chcard" style="border-top-color:' + COLOR[n] + '"><div class="chhead"><b>' + esc(n) + "</b>" +
        '<span class="chicons" aria-hidden="true">✎ ✕</span></div>' +
        '<div class="field"><span>Spend column</span><em>' + esc(n) + "_spend ▾</em></div>" +
        '<div class="field"><span>Impressions or clicks</span><em>' + esc(n) + "_impression ▾</em></div></div>";
    }).join("") + '<div class="chcard add">+ Add a channel</div>';
  }
  function code(text) {
    return '<div class="code"><pre><code>' + esc(text) + '</code></pre><button class="copy" type="button" data-copy="' + esc(text) + '">Copy</button></div>';
  }
  var sel = function (label, value) { return '<div class="field"><span>' + label + "</span><em>" + value + " ▾</em></div>"; };

  var SCREENS = {
    home: '<div class="intro">' +
      '<svg class="mark" viewBox="0 0 512 512" role="img" aria-label="Simple Meridian logo">' +
      '<line class="mk-mid" x1="315" y1="170" x2="268" y2="330" stroke="#AECBFA" stroke-width="58" stroke-linecap="round"/>' +
      '<line class="mk-a" x1="166" y1="168" x2="262" y2="334" stroke="#4285F4" stroke-width="96" stroke-linecap="round"/>' +
      '<line class="mk-b" x1="328" y1="168" x2="424" y2="334" stroke="#1967D2" stroke-width="96" stroke-linecap="round"/>' +
      '<circle class="mk-dot" cx="87" cy="331" r="54" fill="#174EA6"/></svg>' +
      "<h1>Google Meridian,<br>in plain words.</h1>" +
      '<p class="lede">See which ads bring in your sales and where the next dollar should go.<br>' +
      "A guided tour on a made-up shop, then run it on your own data.</p>" +
      '<div class="starts"><button class="btn pill pill-gold" id="t-start" type="button">Start the Simple Meridian guided tour</button>' +
      '<button class="btn pill pill-story" id="t-story" type="button">' +
      '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>Start the story</button></div>' +
      '<a class="by" href="https://www.linkedin.com/in/alibarfibafghi/" target="_blank" rel="noopener noreferrer">' +
      '<img src="assets/ali.png" alt="" width="52" height="52"><span><small>Built by</small><b>Ali Barfi Bafghi</b></span></a>' +
      '<p class="vnote">Updated 27 Oct 2026. I built the <a href="https://github.com/alibb007/Simple-Meridian/tree/5438c16" target="_blank" ' +
      'rel="noopener noreferrer">first release of Simple Meridian</a> in April 2025 on Meridian 1.0.6: upload, fit, charts and a budget ' +
      "optimizer. Today it runs Meridian 2.1.0 and adds GeoX lift tests, this guided tour and a new design.</p></div>",
    story: '<div class="storypage"><div class="kick">The story</div>' +
      '<iframe class="motion" data-src="assets/story.html?v=d44730050f" title="Animated story: a shop works out where its ad budget should go"></iframe>' +
      '<div class="starts"><button class="btn pill pill-gold" id="t-start2" type="button">Start the Simple Meridian guided tour</button>' +
      '<button class="btn pill pill-light" id="t-home" type="button">Back to the start</button></div></div>',
    upload: '<div class="kick">Step 1 of 3</div><h3>Data &amp; model</h3>' +
      '<div class="startcards" data-t="s1-upload">' +
      '<div class="box startcard hot"><span class="hotchip">Start here</span><div class="boxh">Upload your file</div>' +
      "<p>CSV or Excel. Date, outcome and channel columns are detected for you.</p>" +
      '<div class="drop">⇪ Drop a file here, or <u>browse</u><small>50MB per file · CSV, XLSX, XLS</small></div></div>' +
      '<div class="box startcard"><div class="boxh">Or use the sample</div><p>Three years of made-up weekly data for six channels.</p>' +
      '<span class="fakebtn ghostbtn">Load sample data</span></div>' +
      '<div class="box startcard"><div class="boxh">Just look around</div><p>Skip the run: open a model already fitted on the sample.</p>' +
      '<span class="fakebtn ghostbtn">Open demo results</span></div></div>',
    step1: '<div class="kick">Step 1 of 3</div><h3>Data &amp; model</h3>' +
      '<div class="box" data-t="s1-data"><div class="boxh">Your data</div>' +
      '<div class="pills"><span>simple_dataset.csv</span><span>156 weeks</span><span>02 Jan 2022 → 22 Dec 2024</span></div>' +
      '<div class="exp">▾ Preview the table</div><div class="tablewrap"><table><thead><tr><th>week</th><th>TV spend</th><th>Radio spend</th>' +
      "<th>Search spend</th><th>Email spend</th><th>Sales</th></tr></thead><tbody>" + rowsHtml + "</tbody></table></div></div>" +
      '<div class="box" data-t="s1-time"><div class="boxh">1 · Time and outcome</div><div class="fields">' +
      sel("Date column", "time") + sel("Outcome column", "Sales") + sel("Outcome is", "Revenue") + "</div>" +
      '<div class="chart">' + sparkline() + "</div></div>" +
      '<div class="box" data-t="s1-channels"><div class="boxh">2 · Your ad channels</div><div class="chgrid">' + channelCards() + "</div></div>" +
      '<div class="box" data-t="s1-controls"><div class="boxh">3 · Other things that move sales</div>' +
      '<div class="chips"><span>Industry_Trend ✕</span><span>Discount ✕</span></div></div>' +
      '<div class="box" data-t="s1-run"><div class="boxh">4 · Run the model</div>' +
      '<div class="checks"><span>✓ Date and outcome set</span><span>✓ ' + channels.length + ' channels</span><span>✓ 2 control columns</span></div>' +
      '<div class="radio">How long should Meridian learn? ◉ Quick check (about 30 s) ○ Standard (about 1 min) ○ Thorough</div>' +
      '<span class="fakebtn bigbtn">▶ Run model</span></div>',
    ready: '<div class="kick">Step 1 of 3 · after the run</div><h3>Model ready</h3>' +
      '<div class="box readybox" data-t="s1-ready"><div class="build" aria-live="polite"><div class="ring"></div>' +
      '<div class="btxt">Meridian is learning…</div><div class="bbar"><span></span></div>' +
      '<div class="bdone"><span>✓</span>Done. The model is ready.</div></div>' +
      '<div class="boxh">How good is the model?</div><div class="tiles">' +
      '<div class="tile"><div class="k">Fit (R²)</div><div class="v">' + Q.r2.toFixed(2) + '</div><div class="d">weekly ups and downs explained</div></div>' +
      '<div class="tile"><div class="k">Error (MAPE)</div><div class="v">' + (Q.mape * 100).toFixed(1) + '%</div><div class="d">average miss per week</div></div>' +
      '<div class="tile"><div class="k">Convergence (R-hat)</div><div class="v">' + Q.max_rhat.toFixed(2) + '</div><div class="d up">converged</div></div></div>' +
      '<table class="fit"><thead><tr><th>Score</th><th>Value</th><th>What it means</th><th>Good when</th></tr></thead><tbody>' +
      '<tr><td>R-squared</td><td>' + Q.r2.toFixed(3) + '</td><td>Share of the week-to-week ups and downs the model explains</td><td>close to 1</td></tr>' +
      '<tr><td>MAPE</td><td>' + (Q.mape * 100).toFixed(1) + '%</td><td>How far off it is in an average week</td><td>under 10%</td></tr>' +
      '<tr><td>wMAPE</td><td>' + (Q.wmape * 100).toFixed(1) + '%</td><td>The same, with big weeks counting more</td><td>under 10%</td></tr>' +
      '<tr><td>R-hat</td><td>' + Q.max_rhat.toFixed(2) + '</td><td>Whether the model finished learning</td><td>under 1.2</td></tr></tbody></table>' +
      '<div class="row"><span class="fakebtn">Next: see the insights →</span><span class="fakebtn ghostbtn">Download the model</span></div></div>',
    step2: '<div class="kick">Step 2 of 3</div><h3>Insights</h3>' + insightsTiles + tabs(0) + '<div class="chart" data-t="s2-roi">' + roiChart() + "</div>",
    step3: '<div class="kick">Step 3 of 3</div><h3>Budget plan</h3>' +
      '<div class="box" data-t="s3-settings"><div class="boxh">Plan settings</div>' +
      '<div class="pills"><span>Latest year: ' + esc(T.start) + " → " + esc(T.end) + "</span><span>Max change ±30%</span><span>Same total budget</span></div>" +
      '<span class="fakebtn">Optimize budget</span></div>' +
      '<div class="tiles">' +
      '<div class="tile"><div class="k">Budget</div><div class="v">' + money(T.budget_after) + '</div><div class="d">same total</div></div>' +
      '<div class="tile"><div class="k">Incremental revenue</div><div class="v">' + money(T.outcome_after) + '</div><div class="d up">+' + gainPct.toFixed(1) + "% · +" + money(gain) + "</div></div>" +
      '<div class="tile"><div class="k">ROI</div><div class="v">' + T.roi_after.toFixed(2) + '×</div><div class="d">was ' + T.roi_before.toFixed(2) + "×</div></div></div>" +
      '<div class="chart">' + planChart() + "</div>",
    geox: '<div class="kick">Meridian GeoX</div><h3>GeoX (Lift test)</h3>' +
      '<div class="box" data-t="gx-why"><div class="boxh">Why a test?</div><div class="why">' +
      '<div><b>A model looks back</b><p>It sees that sales rose in weeks with more TV, but it cannot be sure TV caused it.</p></div>' +
      '<div class="arrow" aria-hidden="true">→</div>' +
      '<div><b>A test checks it live</b><p>Ads run in some regions and stay off in similar ones. The difference is what the ads did.</p></div></div></div>' +
      '<div class="box" data-t="gx-plan"><div class="boxh">1 · Pick the test regions</div><div class="gx2">' +
      '<div>' + regionGrid() + legend([["Test regions (" + GX.treatment.length + ")", "#6D4AE8"], ["Control regions (" + GX.control.length + ")", "#DCE7FF"]]) + "</div>" +
      '<div><div class="chart">' + gxPre + "</div>" + legend([["Test regions", "#6D4AE8"], ["Control regions", "#7DA2F0"]]) +
      '<p class="note">Daily sales before the test, each group indexed to its own average (100).</p></div></div></div>' +
      '<div class="box" data-t="gx-run"><div class="boxh">2 · Run the ads for ' + GX.test_days + ' days</div>' +
      '<div class="chart">' + gxCf + "</div>" + legend([["Test regions: actual sales", "#6D4AE8"], ["Without the ads (GeoX's estimate)", "#98A2B3", 1]]) + "</div>" +
      '<div class="box" data-t="gx-result"><div class="boxh">3 · The result</div><div class="tiles">' +
      '<div class="tile"><div class="k">Back for every $1</div><div class="v">$' + GX.iroas.mean.toFixed(2) + '</div><div class="d">90% range $' + GX.iroas.lo.toFixed(2) + " – $" + GX.iroas.hi.toFixed(2) + "</div></div>" +
      '<div class="tile"><div class="k">True value we hid</div><div class="v">$' + GX.true_iroas.toFixed(2) + '</div><div class="d up">inside the range</div></div>' +
      '<div class="tile"><div class="k">Extra sales in ' + GX.test_days + ' days</div><div class="v">' + money(gxCum[1]) + '</div><div class="d">+' + (GX.pct.mean * 100).toFixed(1) + "% in the test regions</div></div>" +
      '<div class="tile"><div class="k">Is it real?</div><div class="v">Yes</div><div class="d">p = ' + GX.lift.p.toFixed(3) + "</div></div></div></div>" +
      '<div class="box" data-t="gx-prior"><div class="boxh">4 · Teach the model: TV\'s likely ROI</div>' +
      '<div class="prior"><span>Before the test</span>' + rangeBar(1.42, 3.86, 4.5, "#B8C2D6") + "<b>$1.42 – $3.86</b></div>" +
      '<div class="prior"><span>After the test</span>' + rangeBar(2.23, 2.95, 4.5, "#6D4AE8") + "<b>$2.23 – $2.95</b></div>" +
      '<p class="note">90% ranges from the demo model, Quick check preset, with the test result as TV\'s prior.</p></div>',
    run: '<div class="kick">Your turn</div><h3>Run it on your own data</h3>' +
      '<div class="runwrap" data-t="run-cta">' +
      '<div class="safe"><b>Your data stays on your computer.</b> The app runs in Docker on your own machine at ' +
      '<code>localhost</code>. Your file is never uploaded anywhere, Meridian runs on your computer, usage statistics are off, ' +
      "and the app's fonts and icons come with it, so the page makes no requests to other sites.</div>" +
      '<div class="runs">' +
      '<div class="box"><div class="boxh">1. Install Docker Desktop and open it</div><p>Get it free from ' +
      '<a href="https://www.docker.com/products/docker-desktop/" target="_blank" rel="noopener noreferrer">docker.com</a>, then start it ' +
      "and wait until it says it is running. Tested so far on Apple silicon Macs; the Intel/Windows build passed a full model fit under emulation.</p></div>" +
      '<div class="box"><div class="boxh">2. Paste these lines, then press Enter</div>' +
      '<div class="ostabs" role="tablist"><button type="button" role="tab" class="on" data-os="mac" aria-selected="true">Mac</button>' +
      '<button type="button" role="tab" data-os="win" aria-selected="false">Windows</button></div>' +
      '<div class="os" data-os="mac"><p>Open <b>Terminal</b> (press ⌘ Space, type Terminal, press Enter) and paste:</p>' +
      code("git clone https://github.com/alibb007/Simple-Meridian.git\ncd Simple-Meridian\n./start.sh") + "</div>" +
      '<div class="os" data-os="win" hidden><p>Open <b>PowerShell</b> (Start menu, type PowerShell, press Enter) and paste:</p>' +
      code("git clone https://github.com/alibb007/Simple-Meridian.git\ncd Simple-Meridian\n.\\start.bat") + "</div>" +
      '<p>The first build takes a few minutes, then the app opens in your browser. No git? Download the ZIP from ' +
      '<a href="https://github.com/alibb007/Simple-Meridian" target="_blank" rel="noopener noreferrer">GitHub</a>, unzip it, and double-click ' +
      "<code>start.bat</code> (Windows) or run <code>./start.sh</code> in that folder (Mac).</p></div>" +
      '<div class="box"><div class="boxh">3. Upload your file</div><p>Open <b>http://localhost:8501</b> and upload a CSV or Excel file ' +
      'with one row per week, or load the sample data to try it first. <a href="https://github.com/alibb007/Simple-Meridian#quick-start" ' +
      'target="_blank" rel="noopener noreferrer">Full instructions in the README</a></p></div>' +
      "</div>" +
      '<div class="more"><b>This is the simple path through Meridian.</b> Google Meridian has many more tools than this tour shows, ' +
      "such as models per region, reach and frequency, custom priors and more settings and charts. Simple Meridian keeps the common " +
      'steps easy. For everything else, see the <a href="https://developers.google.com/meridian" target="_blank" rel="noopener noreferrer">Meridian documentation</a>.</div>' +
      "</div>",
  };

  // true = show the PNG screenshots in assets/charts/ instead of the interactive charts.
  var CHART_IMAGES = false;

  // ---------------- Tour steps (text comes from scripts/site/tour_steps.py) ----------------
  // The welcome page is not a step: it has its own start button.
  var STEPS = (D.tour || []).filter(function (s) { return s.chapter !== "Welcome"; }).map(function (s) {
    var st = { chapter: s.chapter, title: s.title, body: s.body, screen: s.page, target: s.anchor };
    if (s.chart) {
      st.screen = "mr-" + s.chart; st.target = "mr-" + s.chart;
      if (!SCREENS[st.screen]) {
        SCREENS[st.screen] = '<div class="kick">' + (s.chapter === "Budget plan charts" ? "Budget plan · charts" : "Insights · Meridian's own charts") + "</div>" +
          (CHART_IMAGES
            ? '<div class="shot" data-t="mr-' + s.chart + '"><img src="assets/charts/' + s.chart + '.png" width="' + s.w +
              '" height="' + s.h + '" alt="' + esc(s.title) + ' (chart from the Simple Meridian app)"></div>'
            : '<div class="shot vchart" data-t="mr-' + s.chart + '" data-chart="' + s.chart + '" role="img" aria-label="' + esc(s.title) +
              ' (interactive chart drawn by Meridian)"><div class="vload">Drawing the chart…</div></div>');
      }
    }
    if (s.chapter === "Your turn") {
      // Adapted for the web demo: the app says "Click Change data…".
      st.screen = "run"; st.target = "run-cta"; st.last = true;
      st.body = "The full app is free and runs on your computer. Upload a spreadsheet with one row per week: a date, your sales " +
        "and the spend on each channel. Your file never leaves your computer, and nothing is sent to us or anyone else.";
    }
    return st;
  });
  SCREENS.home = SCREENS.home.replace("STEPS_COUNT", STEPS.length);
  var CHAPTERS = [];
  STEPS.forEach(function (s, k) { if (!k || STEPS[k - 1].chapter !== s.chapter) CHAPTERS.push(k); });

  // ---------------- Tour engine (no timer: visitors move with Next and Back) ----------------
  var app = document.getElementById("app"), main = document.getElementById("app-main"), spot = document.getElementById("spot");
  var cap = document.getElementById("t-caption"), title = document.getElementById("t-title"), body = document.getElementById("t-body");
  var count = document.getElementById("t-count"), chap = document.getElementById("t-chapter"), bar = document.getElementById("t-progress");
  var nextBtn = document.getElementById("t-next"), skipBtn = document.getElementById("t-skip");
  var againBtn = document.getElementById("t-again"), nav = document.getElementById("chapters");
  var small = window.matchMedia("(max-width: 860px)"), wide = window.matchMedia("(min-width: 1200px)"), SIDE = 380;
  var i = -1, basePad = null;  // i = -1 is the welcome page
  var fold = document.getElementById("fold");
  function setFolded(f) {
    app.classList.toggle("folded", f);
    fold.setAttribute("aria-expanded", String(!f));
    fold.setAttribute("aria-label", f ? "Show the chapter list" : "Hide the chapter list");
    try { localStorage.setItem("sm-folded", f ? "1" : "0"); } catch (e) {}
  }
  fold.addEventListener("click", function () { setFolded(!app.classList.contains("folded")); });
  try { if (localStorage.getItem("sm-folded") === "1") setFolded(true); } catch (e) {}

  if (/Win/.test(navigator.platform || navigator.userAgent)) SCREENS.run = SCREENS.run
    .replace('class="on" data-os="mac" aria-selected="true"', 'data-os="mac" aria-selected="false"')
    .replace('data-os="win" aria-selected="false"', 'class="on" data-os="win" aria-selected="true"')
    .replace('<div class="os" data-os="mac">', '<div class="os" data-os="mac" hidden>').replace('<div class="os" data-os="win" hidden>', '<div class="os" data-os="win">');
  Object.keys(SCREENS).forEach(function (k) {
    var div = document.createElement("div");
    div.className = "screen"; div.dataset.screen = k; div.innerHTML = SCREENS[k];
    main.appendChild(div);
  });
  // Sidebar: Welcome, four numbered sections whose steps fold open, and Your turn.
  var SECTIONS = [
    { name: "Welcome", icon: "home", chapters: [] },
    { name: "Data & model", num: "1", chapters: ["Step 1 · Data & model"] },
    { name: "Insights", num: "2", chapters: ["Step 2 · Insights", "Meridian's own charts"] },
    { name: "Budget plan", num: "3", chapters: ["Step 3 · Budget plan", "Budget plan charts"] },
    { name: "GeoX (Lift test)", num: "4", badge: true, chapters: ["GeoX (Lift test)"] },
    { name: "Your turn", icon: "flag", chapters: ["Your turn"] }
  ];
  var ICONS = { home: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 4 3 11h2.5v8h5v-5h3v5h5v-8H21z"/></svg>',
                flag: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6 3h2v18H6zM9 4h10l-2.5 4L19 12H9z"/></svg>' };
  SECTIONS.forEach(function (sec, n) {
    sec.steps = [];
    STEPS.forEach(function (st, k) { if (sec.chapters.indexOf(st.chapter) >= 0) sec.steps.push(k); });
    sec.first = n === 0 ? -1 : sec.steps[0];
    var wrap = document.createElement("div"), b = document.createElement("button"), many = sec.steps.length > 1;
    wrap.className = "sec"; b.type = "button"; b.className = "chap"; b.dataset.sec = n;
    b.innerHTML = '<span class="n">' + (sec.num || ICONS[sec.icon]) + "</span><span>" + esc(sec.name) + "</span>" +
      (sec.badge ? '<span class="new">NEW</span>' : "") + (many ? '<span class="chev" aria-hidden="true"></span>' : "");
    if (many) b.setAttribute("aria-expanded", "false");
    wrap.appendChild(b);
    var subs = null;
    if (many) {
      subs = document.createElement("div"); subs.className = "subs"; subs.hidden = true;  // closed by default
      sec.steps.forEach(function (k) {
        var x = document.createElement("button");
        x.type = "button"; x.className = "sub"; x.dataset.k = k; x.textContent = STEPS[k].title;
        x.addEventListener("click", function () { go(k, true); });
        subs.appendChild(x);
      });
      wrap.appendChild(subs);
    }
    // The section name opens its steps and goes to the first one; the other sections fold away.
    b.addEventListener("click", function () {
      if (subs) {
        var open = subs.hidden;
        [].forEach.call(nav.querySelectorAll(".subs"), function (o) { o.hidden = true; o.previousSibling.setAttribute("aria-expanded", "false"); });
        subs.hidden = !open; b.setAttribute("aria-expanded", String(open));
        if (!open) return;
      }
      go(sec.first, true);
    });
    sec.el = b;
    nav.appendChild(wrap);
  });
  function sectionOf(k) {
    if (k < 0) return 0;
    for (var n = 1; n < SECTIONS.length; n++) if (SECTIONS[n].steps.indexOf(k) >= 0) return n;
    return 0;
  }

  // Vega libraries and Meridian's chart specs load on first use (same origin, no eval: the AST interpreter runs expressions).
  var chartsReady = null;
  function loadScript(src) {
    return new Promise(function (ok, fail) {
      var t = document.createElement("script"); t.src = src; t.onload = ok; t.onerror = function () { fail(new Error(src)); };
      document.head.appendChild(t);
    });
  }
  function loadCharts() {
    if (!chartsReady) {
      chartsReady = ["vendor/vega@6.2.0.min.js", "vendor/vega-lite@6.4.1.min.js", "vendor/vega-embed@7.0.2.min.js",
                     "vendor/vega-interpreter@2.2.1.js", "charts.js?v=61000e872f"].reduce(function (p, f) {
        return p.then(function () { return loadScript("assets/" + f); });
      }, Promise.resolve());
    }
    return chartsReady;
  }
  function drawCharts(scr) {
    var boxes = scr ? scr.querySelectorAll(".vchart:not(.drawn)") : [];
    if (!boxes.length) return;
    loadCharts().then(function () {
      [].forEach.call(boxes, function (box) {
        if (box.classList.contains("drawn")) return;
        box.classList.add("drawn");
        var spec = window.SM_CHARTS[box.dataset.chart];
        if (spec && spec.table) {  // the fit-score table
          var t = spec.table;
          box.innerHTML = "<table><thead><tr>" + t.columns.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr></thead><tbody>" +
            t.data.map(function (r) { return "<tr>" + r.map(function (v) { return "<td>" + esc(typeof v === "number" ? (+v.toFixed(3)) : v) + "</td>"; }).join("") + "</tr>"; }).join("") +
            "</tbody></table>";
          place(false); return;
        }
        vegaEmbed(box, spec, { actions: false, renderer: "svg", ast: true, expr: vegaInterpreter.expressionInterpreter })
          .then(function () { place(false); })
          .catch(function () { box.innerHTML = '<div class="vload">This chart could not be drawn.</div>'; });
      });
    }).catch(function () { [].forEach.call(boxes, function (b) { b.innerHTML = '<div class="vload">This chart could not be loaded.</div>'; }); });
  }

  function setSpot(r, a, pad) {
    spot.style.left = (r.left - a.left - pad) + "px"; spot.style.top = (r.top - a.top - pad) + "px";
    spot.style.width = (r.width + pad * 2) + "px"; spot.style.height = (r.height + pad * 2) + "px";
  }
  function target() {
    var s = STEPS[i], scr = main.querySelector('.screen[data-screen="' + s.screen + '"]');
    var t = scr && scr.querySelector('[data-t="' + s.target + '"]');
    return { scr: scr, t: t && t.offsetParent ? t : scr };
  }
  // Positions the caption above the part it explains and rings that part. Runs again whenever the layout moves.
  function place(scrollToo) {
    if (i < 0) return;
    var x = target(), scr = x.scr, t = x.t;
    if (ro && watched !== t) { if (watched) ro.unobserve(watched); ro.observe(t); watched = t; }
    if (basePad === null) basePad = parseFloat(getComputedStyle(main).paddingTop) || 16;
    [].forEach.call(main.querySelectorAll(".screen > h3"), function (h) { h.style.marginBottom = ""; });
    main.style.paddingTop = basePad + "px";
    var pad = 6, gap = 12, a, r;
    if (small.matches) {  // phones: the caption is a sheet fixed to the bottom
      cap.style.top = cap.style.left = cap.style.width = "";
      main.style.paddingBottom = (cap.offsetHeight + 24) + "px";
      a = app.getBoundingClientRect(); r = t.getBoundingClientRect();
      setSpot(r, a, pad);
      if (scrollToo) {
        var barBottom = document.querySelector(".app-side").getBoundingClientRect().bottom;
        window.scrollBy({ top: r.top - barBottom - 14, behavior: "auto" });
      }
      return;
    }
    main.style.paddingBottom = "";
    if (wide.matches) {  // wide screens: the caption is a column to the right of the part it explains
      a = app.getBoundingClientRect(); var mm = main.getBoundingClientRect();
      if (scrollToo) { window.scrollBy({ top: t.getBoundingClientRect().top - 64, behavior: "auto" }); a = app.getBoundingClientRect(); }
      r = t.getBoundingClientRect();
      cap.style.width = SIDE + "px";
      // Beside the part it explains, never past the window edge.
      var maxLeft = Math.min(mm.right, document.documentElement.clientWidth) - a.left - SIDE - 28;
      cap.style.left = Math.min(maxLeft, r.right - a.left + 28) + "px";
      cap.style.top = Math.max(r.top - a.top - pad, mm.top - a.top + 16) + "px";
      setSpot(r, a, pad);
      return;
    }
    var m = main.getBoundingClientRect(), w = Math.min(620, m.width - 24);
    cap.style.width = w + "px";
    a = app.getBoundingClientRect(); r = t.getBoundingClientRect();
    var ch = cap.offsetHeight, top = r.top - a.top - pad - gap - ch;
    // The caption sits between the screen's heading and the part it explains; open up room there if needed.
    var hdr = t !== scr && scr.querySelector(":scope > h3");
    var floor = hdr ? hdr.getBoundingClientRect().bottom - a.top + 10 : m.top - a.top + 8;
    if (top < floor) {
      if (hdr) hdr.style.marginBottom = (parseFloat(getComputedStyle(hdr).marginBottom) + floor - top) + "px";
      else main.style.paddingTop = (basePad + floor - top) + "px";
      a = app.getBoundingClientRect(); r = t.getBoundingClientRect(); top = r.top - a.top - pad - gap - ch;
    }
    cap.style.top = top + "px";
    cap.style.left = Math.max(m.left - a.left + 12, Math.min(r.left - a.left, m.right - a.left - w - 12)) + "px";
    setSpot(r, a, pad);
    if (scrollToo) {
      var c = top + a.top;  // caption top in the viewport
      if (c < 0 || c > window.innerHeight * 0.4) window.scrollBy({ top: c - 16, behavior: "auto" });
    }
  }
  // After "Run the model": a short build animation, then the scores.
  var buildTimer = null, readyBox = main.querySelector(".readybox");
  function finishBuild() {
    clearTimeout(buildTimer); buildTimer = null;
    readyBox.classList.remove("building", "isdone");
    cap.style.visibility = "";
  }
  function build() {
    finishBuild();
    var txt = readyBox.querySelector(".btxt"), stages = ["Reading 156 weeks of sales and spend…", "Learning how long each ad keeps working…",
      "Trying hundreds of possible answers…", "Checking the answers agree…"], k = 0, at = i;
    readyBox.classList.add("building"); cap.style.visibility = "hidden";
    txt.textContent = stages[0];
    (function next() {
      buildTimer = setTimeout(function () {
        if (i !== at) return;
        k++;
        if (k < stages.length) { txt.textContent = stages[k]; next(); return; }
        readyBox.classList.add("isdone");
        buildTimer = setTimeout(function () { if (i === at) { finishBuild(); place(false); } }, 900);
      }, 650);
    })();
  }
  main.addEventListener("click", function (e) {
    var tab = e.target.closest && e.target.closest(".ostabs button");
    if (tab) {
      var box = tab.closest(".box");
      [].forEach.call(box.querySelectorAll(".ostabs button"), function (t) { t.classList.toggle("on", t === tab); t.setAttribute("aria-selected", String(t === tab)); });
      [].forEach.call(box.querySelectorAll(".os"), function (o) { o.hidden = o.dataset.os !== tab.dataset.os; });
      place(false); return;
    }
    var b = e.target.closest && e.target.closest(".copy");
    if (!b) return;
    var done = function () { b.textContent = "Copied"; setTimeout(function () { b.textContent = "Copy"; }, 1500); };
    var fallback = function () {  // older browsers, or when the clipboard API is not allowed
      var t = document.createElement("textarea");
      t.value = b.dataset.copy; t.setAttribute("readonly", ""); t.style.position = "fixed"; t.style.opacity = "0";
      document.body.appendChild(t); t.select();
      var ok = false; try { ok = document.execCommand("copy"); } catch (err) {}
      document.body.removeChild(t);
      if (ok) done(); else b.textContent = "Select and copy";
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(b.dataset.copy).then(done, fallback);
    else fallback();
  });

  function chapterEnd(k) { for (var j = k + 1; j < STEPS.length; j++) if (STEPS[j].chapter !== STEPS[k].chapter) return j; return STEPS.length; }
  function go(j, scrollToo) {
    var from = i;
    i = Math.max(-2, Math.min(STEPS.length - 1, j));
    var intro = i < 0, s = intro ? { screen: i === -2 ? "story" : "home" } : STEPS[i];
    if (i === -2) { var fr = main.querySelector(".storypage iframe"); if (!fr.src) fr.src = fr.dataset.src; }
    [].forEach.call(main.children, function (c) { c.classList.toggle("on", c.dataset.screen === s.screen); });
    drawCharts(main.querySelector('.screen[data-screen="' + s.screen + '"]'));
    cap.hidden = spot.hidden = intro;
    app.classList.toggle("touring", !intro);
    var cs = sectionOf(i);  // the story counts as Welcome
    SECTIONS.forEach(function (sec, n) {
      sec.el.classList.toggle("on", n === cs); sec.el.classList.toggle("done", n < cs);
      if (n === cs) { sec.el.setAttribute("aria-current", "step"); nav.scrollTo({ left: sec.el.offsetLeft - 16 }); }
      else sec.el.removeAttribute("aria-current");
    });
    [].forEach.call(nav.querySelectorAll(".sub"), function (x) { x.classList.toggle("on", +x.dataset.k === i); });
    if (history.replaceState) history.replaceState(null, "", i === -2 ? "#story" : intro ? location.pathname + location.search : "#step-" + (i + 1));
    if (intro) {
      main.style.paddingTop = main.style.paddingBottom = "";
      if (scrollToo) window.scrollTo(0, 0);
      return;
    }
    chap.textContent = s.chapter;
    count.textContent = "";  // no step numbers: the chapter name and the bar show where you are
    title.textContent = s.title; body.innerHTML = s.body;
    skipBtn.hidden = chapterEnd(i) >= STEPS.length || !!s.last;
    nextBtn.hidden = !!s.last; againBtn.hidden = !s.last;
    bar.style.width = ((i + 1) / STEPS.length * 100) + "%";
    if (s.target === "s1-ready" && from === i - 1 && !reduce) build(); else finishBuild();
    place(scrollToo);
    // Layout can still shift for a moment (scrollbar appearing, chart sizing), so place again once it settles.
    var at = i;
    requestAnimationFrame(function () { if (i === at) place(false); });
    [120, 400].forEach(function (ms) { setTimeout(function () { if (i === at) place(false); }, ms); });
    if (scrollToo) cap.focus({ preventScroll: true });
  }
  // The motion graphic is same-origin: size its frame to its content so there is no empty band below it.
  var motion = main.querySelector(".storypage iframe.motion");
  function fitMotion() {
    try { var d = motion.contentDocument; if (d && d.body) motion.style.height = d.body.scrollHeight + "px"; } catch (e) {}
  }
  motion.addEventListener("load", function () {
    fitMotion();
    try { if ("ResizeObserver" in window) new ResizeObserver(fitMotion).observe(motion.contentDocument.body); } catch (e) {}
  });
  var startTour = function () { go(0, true); if (!CHART_IMAGES) loadCharts(); };
  document.getElementById("t-start").addEventListener("click", startTour);
  document.getElementById("t-start2").addEventListener("click", startTour);
  document.getElementById("t-story").addEventListener("click", function () { go(-2, true); });
  document.getElementById("t-home").addEventListener("click", function () { go(-1, true); });
  nextBtn.addEventListener("click", function () { go(i + 1, true); });
  document.getElementById("t-back").addEventListener("click", function () { go(i - 1, true); });
  skipBtn.addEventListener("click", function () { go(chapterEnd(i), true); });
  againBtn.addEventListener("click", function () { go(-1, true); });
  document.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (i === -2) {  // on the story page the arrow keys move the story, not the tour
      var sw = null; try { sw = main.querySelector(".storypage iframe").contentWindow; } catch (err) {}
      if (sw && sw.storyStep && (e.key === "ArrowRight" || e.key === "ArrowLeft")) { sw.storyStep(e.key === "ArrowRight" ? 1 : -1); e.preventDefault(); }
      else if (sw && sw.storyPause && e.key === " " && tag !== "button" && tag !== "a") { sw.storyPause(); e.preventDefault(); }
      return;
    }
    if (e.key === "ArrowRight") { go(i + 1, true); e.preventDefault(); }
    else if (e.key === "ArrowLeft" && i >= 0) { go(i === 0 ? -1 : i - 1, true); e.preventDefault(); }
  });
  // Re-place whenever anything moves: images loading, fonts, window size, the caption's own height.
  var ro = "ResizeObserver" in window ? new ResizeObserver(function () { place(false); }) : null, watched = null;
  if (ro) { ro.observe(main); ro.observe(cap); ro.observe(document.documentElement); }
  window.addEventListener("resize", function () { place(false); });
  main.addEventListener("load", function () { place(false); }, true);
  window.addEventListener("hashchange", function () {
    var h = /^#step-(\d+)$/.exec(location.hash);
    if (location.hash === "#story" && i !== -2) go(-2, true);
    else if (h && +h[1] - 1 !== i) go(+h[1] - 1, true);
  });
  var m0 = /^#step-(\d+)$/.exec(location.hash);
  go(location.hash === "#story" ? -2 : m0 ? +m0[1] - 1 : -1, !!m0);
})();
