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
    home: '<div class="kick">Overview</div><h3>Simple Meridian</h3>' +
      '<div class="minihero" data-t="home-hero"><b>Find out which ads really bring in your sales</b>' +
      "<p>Google Meridian, made simple. Take the tour, open the demo, or use your own data.</p>" +
      '<span class="fakebtn gold">Take the 2-minute tour</span> <span class="fakebtn ghost">Open the demo</span></div>',
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
      '<div class="box" data-t="s1-ready"><div class="boxh">Model ready</div><div class="tiles">' +
      '<div class="tile"><div class="k">Fit (R²)</div><div class="v">' + Q.r2.toFixed(2) + '</div><div class="d">weekly variation explained</div></div>' +
      '<div class="tile"><div class="k">Error (MAPE)</div><div class="v">' + (Q.mape * 100).toFixed(1) + '%</div><div class="d">average miss per week</div></div>' +
      '<div class="tile"><div class="k">Convergence</div><div class="v">' + Q.max_rhat.toFixed(2) + '</div><div class="d up">converged</div></div></div>' +
      '<div class="row"><span class="fakebtn">Fit model</span><span class="radio">◉ Quick check ○ Standard ○ Thorough</span></div></div>',
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
    run: '<div class="kick">Your turn</div><h3>Run the full version</h3>' +
      '<div class="box" data-t="run-cta"><div class="boxh">On your Mac or Windows PC</div>' +
      "<p>The full app fits Meridian on your own weekly data, with budget plans and GeoX (Lift test)<span class=\"new\">NEW</span> included. Your data stays on your computer.</p>" +
      '<a class="btn btn-primary" href="https://github.com/alibb007/Simple-Meridian#quick-start" target="_blank" rel="noopener noreferrer">Run the full version on your computer</a></div>',
  };

  // ---------------- Tour steps (text comes from the app's utils/tour.py) ----------------
  var PAGE_NAV = { home: "home", step1: "data", step2: "insights", step3: "plan", geox: "geox" };
  var STEPS = (D.tour || []).map(function (s) {
    var st = { chapter: s.chapter, title: s.title, body: s.body, screen: s.page, nav: PAGE_NAV[s.page], target: s.anchor };
    if (s.chart) {
      st.screen = "mr-" + s.chart; st.target = "mr-" + s.chart;
      st.nav = s.chapter === "Budget plan charts" ? "plan" : "insights";
      if (!SCREENS[st.screen]) {
        SCREENS[st.screen] = '<div class="kick">' + (st.nav === "plan" ? "Budget plan · charts" : "Insights · Meridian's own charts") + "</div>" +
          '<div class="shot" data-t="mr-' + s.chart + '"><img src="assets/charts/' + s.chart + '.png" loading="lazy" width="' + s.w +
          '" height="' + s.h + '" alt="' + esc(s.title) + ' (chart from the Simple Meridian app)"></div>';
      }
    }
    if (s.chapter === "Your turn") {
      // Adapted for the web demo: the app says "Click Change data…".
      st.screen = "run"; st.nav = "data"; st.target = "run-cta"; st.last = true;
      st.body = "Run the full version on your computer, then upload a spreadsheet with one row per week: a date, your sales " +
        "and the spend on each channel. The app finds the columns for you. Stuck on a word? Open <b>Help &amp; glossary</b> in the sidebar.";
    }
    return st;
  });
  var CHAPTERS = [];
  STEPS.forEach(function (s, k) { if (!k || STEPS[k - 1].chapter !== s.chapter) CHAPTERS.push(k); });

  // ---------------- Tour engine ----------------
  var app = document.getElementById("app"), main = document.getElementById("app-main"), spot = document.getElementById("spot");
  var cap = document.getElementById("t-caption"), title = document.getElementById("t-title"), body = document.getElementById("t-body");
  var count = document.getElementById("t-count"), chap = document.getElementById("t-chapter"), bar = document.getElementById("t-progress");
  var playBtn = document.getElementById("t-play"), nextBtn = document.getElementById("t-next"), skipBtn = document.getElementById("t-skip");
  var runLink = document.getElementById("t-run");
  var i = 0, playing = !reduce, elapsed = 0, last = null, inView = false, basePad = null, followUntil = 0;

  Object.keys(SCREENS).forEach(function (k) {
    var div = document.createElement("div");
    div.className = "screen"; div.dataset.screen = k; div.innerHTML = SCREENS[k];
    main.appendChild(div);
  });
  // The caption floats inside the app window, right above the part it explains.
  app.appendChild(cap); cap.classList.add("floating");

  function stepMs(s) {
    var words = (s.title + " " + s.body.replace(/<[^>]+>/g, "")).split(/\s+/).length;
    return Math.max(6000, Math.min(15000, words * 280));
  }
  function place(scrollToo) {
    var s = STEPS[i], scr = main.querySelector('.screen[data-screen="' + s.screen + '"]');
    var t = scr && scr.querySelector('[data-t="' + s.target + '"]');
    if (!t || !t.offsetParent) t = scr;
    if (basePad === null) basePad = parseFloat(getComputedStyle(main).paddingTop) || 16;
    main.style.paddingTop = basePad + "px";
    var a = app.getBoundingClientRect(), r = t.getBoundingClientRect(), pad = 6, gap = 12;
    var w = Math.min(600, a.width - 24);
    cap.style.width = w + "px";
    var ch = cap.offsetHeight, top = r.top - a.top - pad - gap - ch;
    if (top < 8) {  // not enough room above: push the screen down so the caption still sits above the part
      main.style.paddingTop = (basePad + (8 - top)) + "px";
      a = app.getBoundingClientRect(); r = t.getBoundingClientRect(); top = r.top - a.top - pad - gap - ch;
    }
    var left = Math.max(12, Math.min(r.left - a.left, a.width - w - 12));
    cap.style.top = top + "px"; cap.style.left = left + "px";
    spot.style.left = (r.left - a.left - pad) + "px"; spot.style.top = (r.top - a.top - pad) + "px";
    spot.style.width = (r.width + pad * 2) + "px"; spot.style.height = (r.height + pad * 2) + "px";
    if (scrollToo || Date.now() < followUntil) {
      var c = cap.getBoundingClientRect();
      if (c.top < 0 || c.top > window.innerHeight * 0.6) window.scrollBy({ top: c.top - 16, behavior: reduce ? "auto" : "smooth" });
    }
  }
  function chapterEnd(k) { for (var j = k + 1; j < STEPS.length; j++) if (STEPS[j].chapter !== STEPS[k].chapter) return j; return STEPS.length; }
  function go(j, scrollToo) {
    i = Math.max(0, Math.min(STEPS.length - 1, j)); elapsed = 0;
    var s = STEPS[i];
    [].forEach.call(main.children, function (c) { c.classList.toggle("on", c.dataset.screen === s.screen); });
    [].forEach.call(app.querySelectorAll("[data-nav]"), function (n) { n.classList.toggle("on", n.dataset.nav === s.nav); });
    chap.innerHTML = esc(s.chapter) + (/GeoX/.test(s.chapter) ? '<span class="new">NEW</span>' : "");
    count.textContent = "Step " + (i + 1) + " of " + STEPS.length;
    title.textContent = s.title; body.innerHTML = s.body;
    var nextChapter = chapterEnd(i);
    skipBtn.hidden = nextChapter >= STEPS.length || s.last;
    nextBtn.hidden = !!s.last; runLink.hidden = !s.last;
    bar.style.width = (i / STEPS.length * 100) + "%";
    if (scrollToo) followUntil = Date.now() + 1200;  // keep following while images and fades settle
    requestAnimationFrame(function () { place(scrollToo); });
    setTimeout(function () { place(false); }, 450);  // again after images and the fade-in settle
  }
  function setPlaying(p) { playing = p; playBtn.textContent = p ? "Pause" : "Play"; last = null; }
  function tick(now) {
    if (playing && inView) {
      if (last !== null) elapsed += now - last;
      last = now;
      var ms = stepMs(STEPS[i]);
      bar.style.width = ((i + Math.min(1, elapsed / ms)) / STEPS.length * 100) + "%";
      if (elapsed >= ms) { if (i < STEPS.length - 1) go(i + 1, true); else setPlaying(false); }
    } else { last = null; }
    requestAnimationFrame(tick);
  }
  nextBtn.addEventListener("click", function () { go(i + 1, true); });
  document.getElementById("t-back").addEventListener("click", function () { go(i - 1, true); });
  skipBtn.addEventListener("click", function () { go(chapterEnd(i), true); });
  playBtn.addEventListener("click", function () { setPlaying(!playing); });
  main.addEventListener("load", function () { place(false); }, true);  // a lazy chart image finished loading
  [].forEach.call(document.querySelectorAll("[data-play]"), function (a) {
    a.addEventListener("click", function () { go(0); setPlaying(true); });
  });
  document.addEventListener("keydown", function (e) {
    if (!inView || e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (e.key === "ArrowRight") { go(i + 1, true); e.preventDefault(); }
    else if (e.key === "ArrowLeft") { go(i - 1, true); e.preventDefault(); }
    else if (e.key === " " && tag !== "button" && tag !== "a") { setPlaying(!playing); e.preventDefault(); }
  });
  window.addEventListener("resize", function () { place(false); });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { inView = es[0].isIntersecting; }, { threshold: 0.15 }).observe(document.getElementById("tour"));
  } else { inView = true; }
  setPlaying(!reduce);
  go(0);
  requestAnimationFrame(tick);
})();
