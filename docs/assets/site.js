/* Simple Meridian live demo: the guided tour is the whole page. Simulated app screens, a spotlight and a caption.
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
  // Region ids (data-t) match the app's tour anchors in utils/tour.py.
  var Q = D.quality, G = D.geox_sample;
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
  var sel = function (label, value) { return '<div class="field"><span>' + label + "</span><em>" + value + " ▾</em></div>"; };

  var SCREENS = {
    home: '<div class="version"><span class="tag">Updated 27 Oct 2026</span>' +
      "<span>First release <b>April 2025</b> on Google Meridian 1.0.6</span>" +
      '<span>Now on <b>Meridian 2.1.0</b>, with <b>GeoX (Lift test)</b><span class="new">NEW</span></span></div>' +
      '<div class="intro">' +
      '<div class="kicker">Guided tour · Google Meridian, made simple</div>' +
      "<h1>Find out which ads really bring in your sales</h1>" +
      '<p class="lede">Meridian is Google\'s free tool for working out what each ad channel earns and where the next dollar ' +
      "should go. This tour shows it on a made-up company that advertises on " + channels.length + " channels. You click Next; " +
      "there is nothing to type.</p>" +
      '<iframe class="motion" src="assets/story.html" title="Animated story: a shop works out where its ad budget should go"></iframe>' +
      '<div class="start"><button class="btn btn-gold btn-big" id="t-start" type="button">' +
      '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>Start the guided tour</button>' +
      '<span class="startnote">STEPS_COUNT steps · use Next and Back, or the arrow keys</span></div>' +
      '<div class="sign"><img class="avatar" src="assets/ali.png" alt="" width="36" height="36">' +
      "<span>Built by <b>Ali Barfi Bafghi</b> so anyone can try Meridian without writing code. First release April 2025 on " +
      "Meridian 1.0.6, updated 27 Oct 2026 to Meridian 2.1.0.</span></div></div>",
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
      '<div class="box" data-t="s1-ready"><div class="boxh">How good is the model?</div><div class="tiles">' +
      '<div class="tile"><div class="k">Fit (R²)</div><div class="v">' + Q.r2.toFixed(2) + '</div><div class="d">weekly ups and downs explained</div></div>' +
      '<div class="tile"><div class="k">Error (MAPE)</div><div class="v">' + (Q.mape * 100).toFixed(1) + '%</div><div class="d">average miss per week</div></div>' +
      '<div class="tile"><div class="k">Convergence (R-hat)</div><div class="v">' + Q.max_rhat.toFixed(2) + '</div><div class="d up">converged</div></div></div>' +
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
    geox: '<div class="kick">Meridian GeoX <span class="new">NEW</span></div><h3>GeoX (Lift test)</h3>' +
      '<div class="box" data-t="gx-plan"><div class="boxh">1 · Plan the test</div>' +
      '<div class="callout">Made-up data for 40 regions. The campaign really returns $' + G.true_iroas.toFixed(2) + " per $1. Can GeoX find it?</div>" +
      '<span class="fakebtn">Pick test regions</span> <span class="fakebtn">Run the test and measure</span></div>' +
      '<div class="tiles">' +
      '<div class="tile"><div class="k">Test regions</div><div class="v">' + G.test_regions + '</div><div class="d">ads run here</div></div>' +
      '<div class="tile"><div class="k">Control regions</div><div class="v">' + G.control_regions + '</div><div class="d">no change</div></div>' +
      '<div class="tile"><div class="k">Return per $1 found</div><div class="v">$' + G.estimate.toFixed(2) + '</div><div class="d">90% range $' + G.lo.toFixed(2) + " – $" + G.hi.toFixed(2) + "</div></div>" +
      '<div class="tile"><div class="k">True value</div><div class="v">$' + G.true_iroas.toFixed(2) + '</div><div class="d up">inside the range</div></div></div>',
    run: '<div class="kick">Your turn</div><h3>Run it on your own data</h3>' +
      '<div class="runwrap" data-t="run-cta"><p class="lede">The full app fits Meridian on your own weekly data, runs budget plans and ' +
      'GeoX (Lift test)<span class="new">NEW</span> experiments, and keeps your data on your computer. It runs in ' +
      '<a href="https://www.docker.com/products/docker-desktop/" target="_blank" rel="noopener noreferrer">Docker Desktop</a> ' +
      "on a Mac or a Windows PC. Tested so far on Apple silicon; the Intel/Windows build passed a full model fit under emulation.</p>" +
      '<div class="runs">' +
      '<div class="box"><div class="boxh">1. Get the code</div><pre><code>git clone https://github.com/alibb007/Simple-Meridian.git\ncd Simple-Meridian</code></pre>' +
      '<p>No git? Download the ZIP from <a href="https://github.com/alibb007/Simple-Meridian" target="_blank" rel="noopener noreferrer">GitHub</a> and unzip it.</p></div>' +
      '<div class="box"><div class="boxh">2. Start it</div><pre><code>./start.sh</code></pre>' +
      "<p>That's on a Mac. On Windows, double-click <code>start.bat</code>. The first build takes a few minutes.</p></div>" +
      '<div class="box"><div class="boxh">3. Upload your file</div><p>Go to <b>http://localhost:8501</b> and upload a CSV or Excel file ' +
      "with one row per week, or load the sample data to try it first.</p>" +
      '<p><a href="https://github.com/alibb007/Simple-Meridian#quick-start" target="_blank" rel="noopener noreferrer">Full instructions in the README</a></p></div>' +
      "</div></div>",
  };

  // true = show the PNG screenshots in assets/charts/ instead of the interactive charts.
  var CHART_IMAGES = false;

  // ---------------- Tour steps (text comes from docs/tour_steps.py) ----------------
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
        "and the spend on each channel. The app finds the columns for you, and <b>Help &amp; glossary</b> explains the terms.";
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

  Object.keys(SCREENS).forEach(function (k) {
    var div = document.createElement("div");
    div.className = "screen"; div.dataset.screen = k; div.innerHTML = SCREENS[k];
    main.appendChild(div);
  });
  // Sidebar: the welcome page, then one link per chapter.
  [-1].concat(CHAPTERS).forEach(function (k, n) {
    var b = document.createElement("button"), name = k < 0 ? "Welcome" : STEPS[k].chapter;
    b.type = "button"; b.className = "chap"; b.dataset.k = k;
    b.innerHTML = '<span class="n">' + (n + 1) + "</span><span>" + esc(name) + "</span>" +
      (/GeoX/.test(name) ? '<span class="new">NEW</span>' : "");
    b.addEventListener("click", function () { go(k, true); });
    nav.appendChild(b);
  });

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
                     "vendor/vega-interpreter@2.2.1.js", "charts.js"].reduce(function (p, f) {
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
  function chapterEnd(k) { for (var j = k + 1; j < STEPS.length; j++) if (STEPS[j].chapter !== STEPS[k].chapter) return j; return STEPS.length; }
  function go(j, scrollToo) {
    i = Math.max(-1, Math.min(STEPS.length - 1, j));
    var intro = i < 0, s = intro ? { screen: "home" } : STEPS[i];
    [].forEach.call(main.children, function (c) { c.classList.toggle("on", c.dataset.screen === s.screen); });
    drawCharts(main.querySelector('.screen[data-screen="' + s.screen + '"]'));
    cap.hidden = spot.hidden = intro;
    app.classList.toggle("touring", !intro);
    var start = -1; CHAPTERS.forEach(function (k) { if (k <= i) start = k; });
    [].forEach.call(nav.children, function (b) {
      var k = +b.dataset.k, on = k === start;
      b.classList.toggle("on", on); b.classList.toggle("done", k < start);
      if (on) { b.setAttribute("aria-current", "step"); nav.scrollTo({ left: b.offsetLeft - 16 }); }
      else b.removeAttribute("aria-current");
    });
    if (history.replaceState) history.replaceState(null, "", intro ? location.pathname + location.search : "#step-" + (i + 1));
    if (intro) {
      main.style.paddingTop = main.style.paddingBottom = "";
      if (scrollToo) window.scrollTo(0, 0);
      return;
    }
    chap.innerHTML = esc(s.chapter) + (/GeoX/.test(s.chapter) ? '<span class="new">NEW</span>' : "");
    count.textContent = "Step " + (i + 1) + " of " + STEPS.length;
    title.textContent = s.title; body.innerHTML = s.body;
    skipBtn.hidden = chapterEnd(i) >= STEPS.length || !!s.last;
    nextBtn.hidden = !!s.last; againBtn.hidden = !s.last;
    bar.style.width = ((i + 1) / STEPS.length * 100) + "%";
    place(scrollToo);
    // Layout can still shift for a moment (scrollbar appearing, chart sizing), so place again once it settles.
    var at = i;
    requestAnimationFrame(function () { if (i === at) place(false); });
    [120, 400].forEach(function (ms) { setTimeout(function () { if (i === at) place(false); }, ms); });
    if (scrollToo) cap.focus({ preventScroll: true });
  }
  // The motion graphic is same-origin: size its frame to its content so there is no empty band below it.
  var motion = main.querySelector("iframe.motion");
  function fitMotion() {
    try { var d = motion.contentDocument; if (d && d.body) motion.style.height = d.body.scrollHeight + "px"; } catch (e) {}
  }
  motion.addEventListener("load", function () {
    fitMotion();
    try { if ("ResizeObserver" in window) new ResizeObserver(fitMotion).observe(motion.contentDocument.body); } catch (e) {}
  });
  document.getElementById("t-start").addEventListener("click", function () { go(0, true); if (!CHART_IMAGES) loadCharts(); });
  nextBtn.addEventListener("click", function () { go(i + 1, true); });
  document.getElementById("t-back").addEventListener("click", function () { go(i - 1, true); });
  skipBtn.addEventListener("click", function () { go(chapterEnd(i), true); });
  againBtn.addEventListener("click", function () { go(-1, true); });
  document.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (e.key === "ArrowRight") { go(i + 1, true); e.preventDefault(); }
    else if (e.key === "ArrowLeft" && i >= 0) { go(i - 1, true); e.preventDefault(); }
  });
  // Re-place whenever anything moves: images loading, fonts, window size, the caption's own height.
  var ro = "ResizeObserver" in window ? new ResizeObserver(function () { place(false); }) : null, watched = null;
  if (ro) { ro.observe(main); ro.observe(cap); ro.observe(document.documentElement); }
  window.addEventListener("resize", function () { place(false); });
  main.addEventListener("load", function () { place(false); }, true);
  window.addEventListener("hashchange", function () {
    var h = /^#step-(\d+)$/.exec(location.hash);
    if (h && +h[1] - 1 !== i) go(+h[1] - 1, true);
  });
  var m0 = /^#step-(\d+)$/.exec(location.hash);
  go(m0 ? +m0[1] - 1 : -1, !!m0);
})();
