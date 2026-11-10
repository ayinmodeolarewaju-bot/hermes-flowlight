/* Flowlight picture. Shared by the loopback page, the dashboard tab, and Desktop. */
var FLOWLIGHT_CSS = [
  ".flowlight-root{position:relative;width:100%;height:100%;min-height:320px;overflow:hidden;",
  "background:#07060e;color:#e7eefc;font-family:var(--fl-ui,Outfit,ui-sans-serif,Segoe UI,sans-serif);}",
  ".flowlight-root *{box-sizing:border-box}",
  ".fl-stage{position:absolute;inset:0}",
  ".fl-canvas{width:100%;height:100%;display:block;cursor:grab;touch-action:none}",
  ".fl-canvas.dragging{cursor:grabbing}",
  ".fl-top{position:absolute;left:14px;right:14px;top:12px;display:flex;gap:12px;align-items:flex-start;",
  "justify-content:space-between;pointer-events:none;z-index:2}",
  ".fl-brand{pointer-events:auto;display:flex;flex-direction:column;gap:4px}",
  ".fl-word{font-family:var(--fl-display,Syne,Outfit,sans-serif);font-weight:750;letter-spacing:.22em;",
  "font-size:13px;margin:0}",
  ".fl-sub{margin:0;font-size:12px;color:rgba(231,238,252,.62);max-width:460px;line-height:1.35}",
  ".fl-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}",
  ".fl-badge{pointer-events:auto;border:1px solid rgba(255,255,255,.16);border-radius:999px;",
  "padding:4px 9px;font-size:10px;letter-spacing:.16em;text-transform:uppercase}",
  ".fl-badge.live{color:#9dffe2;border-color:rgba(120,255,214,.45);box-shadow:0 0 18px rgba(80,255,200,.18)}",
  ".fl-badge.demo{color:#ffd27a;border-color:rgba(255,196,90,.55);background:rgba(255,180,60,.08)}",
  ".fl-stats{pointer-events:none;text-align:right;font-variant-numeric:tabular-nums;font-size:12px;",
  "color:rgba(231,238,252,.78);line-height:1.45;white-space:pre-line}",
  ".fl-bottom{position:absolute;left:14px;right:14px;bottom:12px;display:flex;gap:10px;align-items:center;",
  "z-index:2;padding:8px 10px;border-radius:14px;background:rgba(8,8,16,.55);",
  "border:1px solid rgba(255,255,255,.08);backdrop-filter:blur(10px)}",
  ".fl-btn{border:1px solid rgba(255,255,255,.16);background:transparent;color:inherit;border-radius:999px;",
  "padding:6px 10px;font:inherit;font-size:12px;cursor:pointer}",
  ".fl-btn[aria-pressed=true],.fl-btn.primary{background:rgba(120,190,255,.18);border-color:rgba(140,200,255,.5)}",
  ".fl-btn:disabled{opacity:.4;cursor:default}",
  ".fl-range{flex:1;accent-color:#8fd4ff;min-width:80px}",
  ".fl-time{font-size:11px;color:rgba(231,238,252,.66);white-space:nowrap;font-variant-numeric:tabular-nums}",
  ".fl-panel{position:absolute;top:74px;right:14px;width:min(300px,calc(100% - 28px));max-height:calc(100% - 150px);",
  "overflow:auto;z-index:3;padding:14px;border-radius:16px;background:rgba(10,10,18,.82);",
  "border:1px solid rgba(180,210,255,.18);box-shadow:0 18px 50px rgba(0,0,0,.35);backdrop-filter:blur(16px)}",
  ".fl-panel h3{margin:0 0 6px;font-size:14px;font-weight:640}",
  ".fl-panel p{margin:0 0 8px;font-size:12px;line-height:1.4;color:rgba(231,238,252,.78);overflow-wrap:anywhere}",
  ".fl-k{display:block;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:rgba(231,238,252,.46)}",
  ".fl-panel a{color:#9fd4ff}",
  ".fl-x{position:absolute;top:8px;right:8px}",
  ".fl-empty{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:2;pointer-events:none}",
  ".fl-card{pointer-events:auto;max-width:420px;padding:22px;border-radius:18px;background:rgba(8,8,16,.62);",
  "border:1px solid rgba(255,255,255,.1);text-align:left}",
  ".fl-card h2{margin:8px 0;font-family:var(--fl-display,Syne,sans-serif);font-size:28px;letter-spacing:.08em}",
  ".fl-legend{position:absolute;left:14px;top:74px;display:flex;flex-direction:column;gap:4px;z-index:2;pointer-events:none}",
  ".fl-key{display:flex;gap:6px;align-items:center;font-size:11px;color:rgba(231,238,252,.72)}",
  ".fl-dot{width:8px;height:8px;border-radius:99px;box-shadow:0 0 8px currentColor}",
  ".fl-warn{position:absolute;left:14px;right:14px;bottom:62px;z-index:2;font-size:11px;",
  "color:rgba(255,214,150,.8);pointer-events:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
  ".fl-tip{position:absolute;z-index:4;pointer-events:none;padding:6px 8px;border-radius:8px;font-size:11px;",
  "background:rgba(6,6,12,.9);border:1px solid rgba(255,255,255,.12);transform:translate(12px,12px);max-width:240px}"
].join("");

var TOKEN_COLOR = {
  USDC: "#5ad0ff",
  USDT: "#3ee0a2",
  DAI: "#f0c14a",
  ETH: "#9db4ff",
  WETH: "#9db4ff",
  NEAR: "#c6ff73",
  WNEAR: "#c6ff73",
  SOL: "#d2b4ff",
  AERO: "#7dffe8",
  USDBC: "#7ecbff"
};

var CHAIN_COLOR = {
  base: "#6ecbff",
  ethereum: "#b9a6ff",
  arbitrum: "#7ee0ff",
  optimism: "#ff8b7a",
  near: "#c6ff73",
  solana: "#d2b4ff"
};

function flHash(text) {
  var h = 2166136261;
  var s = String(text || "");
  for (var i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295;
}

function flTokenColor(symbol) {
  var key = String(symbol || "").toUpperCase();
  if (TOKEN_COLOR[key]) return TOKEN_COLOR[key];
  return "hsl(" + Math.round(flHash(key) * 360) + " 78% 68%)";
}

function flEl(tag, className) {
  var node = document.createElement(tag);
  if (className) node.className = className;
  return node;
}

function flEnsureStyle() {
  var style = document.getElementById("flowlight-style");
  if (!style) {
    style = document.createElement("style");
    style.id = "flowlight-style";
    (document.head || document.documentElement).appendChild(style);
  }
  style.textContent = FLOWLIGHT_CSS;
}

function flUsd(usd) {
  var n = Number(usd);
  if (!isFinite(n)) return "";
  var sign = n < 0 ? "-" : "";
  n = Math.abs(n);
  if (n >= 1000000) return sign + "$" + (n / 1000000).toFixed(2) + "M";
  if (n >= 10000) return sign + "$" + (n / 1000).toFixed(1) + "k";
  if (n > 0 && n < 0.01) return sign + "<$0.01";
  return sign + "$" + n.toFixed(2);
}

function flMoney(amount, token, usd) {
  var text = String(amount) + " " + token;
  var body = flUsd(usd);
  return body ? text + " · " + body : text;
}

function flShort(address) {
  var text = String(address || "");
  if (!text || text.length <= 18 || text.indexOf(".near") !== -1 || text.indexOf(".tg") !== -1) return text;
  if (text.slice(0, 2) === "0x") return text.slice(0, 6) + "…" + text.slice(-4);
  return text.slice(0, 4) + "…" + text.slice(-4);
}

function flClock(ts) {
  if (!ts) return "";
  try {
    return new Date(ts * 1000).toISOString().slice(0, 16).replace("T", " ") + " UTC";
  } catch (err) {
    return "";
  }
}

function mountFlowlight(root, options) {
  flEnsureStyle();
  options = options || {};
  root.classList.add("flowlight-root");
  root.textContent = "";

  var stage = flEl("div", "fl-stage");
  var canvas = flEl("canvas", "fl-canvas");
  canvas.setAttribute("aria-label", "Animated money flow graph");
  stage.appendChild(canvas);
  var top = flEl("div", "fl-top");
  var brand = flEl("div", "fl-brand");
  var word = flEl("p", "fl-word");
  word.textContent = "FLOWLIGHT";
  var sub = flEl("p", "fl-sub");
  sub.textContent = "Reading public chain data…";
  var row = flEl("div", "fl-row");
  var badge = flEl("span", "fl-badge");
  badge.textContent = "LIVE";
  var demoBtn = flEl("button", "fl-btn");
  demoBtn.type = "button";
  demoBtn.textContent = "Demo fixture";
  var liveBtn = flEl("button", "fl-btn");
  liveBtn.type = "button";
  liveBtn.textContent = "Live";
  row.appendChild(badge);
  row.appendChild(demoBtn);
  row.appendChild(liveBtn);
  brand.appendChild(word);
  brand.appendChild(row);
  brand.appendChild(sub);
  var stats = flEl("div", "fl-stats");
  top.appendChild(brand);
  top.appendChild(stats);
  var legend = flEl("div", "fl-legend");
  var warn = flEl("div", "fl-warn");
  var empty = flEl("div", "fl-empty");
  var bottom = flEl("div", "fl-bottom");
  var play = flEl("button", "fl-btn");
  play.type = "button";
  play.textContent = "Play";
  var range = flEl("input", "fl-range");
  range.type = "range";
  range.min = "0";
  range.max = "1000";
  range.value = "1000";
  range.setAttribute("aria-label", "Time scrubber");
  var timeLabel = flEl("span", "fl-time");
  var windows = [900, 3600, 21600, 86400];
  var windowButtons = windows.map(function (seconds) {
    var button = flEl("button", "fl-btn");
    button.type = "button";
    button.textContent = seconds < 3600 ? "15m" : (seconds / 3600) + "h";
    button.dataset.seconds = String(seconds);
    bottom.appendChild(button);
    return button;
  });
  bottom.insertBefore(play, bottom.firstChild);
  bottom.insertBefore(range, windowButtons[0]);
  bottom.appendChild(timeLabel);
  var panel = flEl("aside", "fl-panel");
  panel.hidden = true;
  var tip = flEl("div", "fl-tip");
  tip.hidden = true;
  root.appendChild(stage);
  root.appendChild(top);
  root.appendChild(legend);
  root.appendChild(warn);
  root.appendChild(empty);
  root.appendChild(bottom);
  root.appendChild(panel);
  root.appendChild(tip);

  var state = {
    data: null,
    error: "",
    force: options.initialDemo ? "demo" : (options.initialLive ? "live" : null),
    live: true,
    playing: false,
    cursor: 1,
    windowSec: 21600,
    hover: null,
    selected: null,
    cam: { x: 0, y: 0, k: 1 },
    drag: null,
    nodes: {},
    dust: [],
    dead: false,
    picked: false
  };
  for (var d = 0; d < 70; d++) {
    state.dust.push({
      x: flHash("x" + d),
      y: flHash("y" + d),
      r: 0.4 + flHash("r" + d) * 1.4,
      s: 0.015 + flHash("s" + d) * 0.04,
      a: 0.15 + flHash("a" + d) * 0.45
    });
  }

  function setWindow(seconds) {
    state.windowSec = seconds;
    windowButtons.forEach(function (button) {
      button.setAttribute("aria-pressed", button.dataset.seconds === String(seconds) ? "true" : "false");
    });
  }
  setWindow(21600);

  function query() {
    if (state.force === "demo") return { demo: true };
    if (state.force === "live") return { live: true };
    return {};
  }

  function load() {
    if (!options.poll) return;
    Promise.resolve(options.poll(query())).then(function (payload) {
      if (state.dead || !payload) return;
      state.data = payload;
      state.error = "";
      paintChrome();
    }).catch(function (err) {
      if (state.dead) return;
      state.error = err && err.message ? err.message : "The flow service did not answer.";
      paintChrome();
    });
  }

  demoBtn.addEventListener("click", function () {
    state.force = "demo";
    state.selected = null;
    state.picked = false;
    load();
  });
  liveBtn.addEventListener("click", function () {
    state.force = "live";
    state.live = true;
    state.cursor = 1;
    state.selected = null;
    state.picked = false;
    load();
  });
  play.addEventListener("click", function () {
    state.playing = !state.playing;
    state.live = false;
    if (state.cursor >= 0.995) state.cursor = 0;
    play.textContent = state.playing ? "Pause" : "Play";
    play.setAttribute("aria-pressed", state.playing ? "true" : "false");
  });
  range.addEventListener("input", function () {
    state.live = false;
    state.playing = false;
    play.textContent = "Play";
    state.cursor = Number(range.value) / 1000;
  });
  windowButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      setWindow(Number(button.dataset.seconds));
    });
  });

  function span() {
    var flows = (state.data && state.data.flows) || [];
    var min = Infinity;
    var max = -Infinity;
    flows.forEach(function (flow) {
      if (!flow.ts) return;
      min = Math.min(min, flow.ts);
      max = Math.max(max, flow.ts);
    });
    if (!isFinite(min)) {
      var now = Date.now() / 1000;
      return { min: now - 3600, max: now };
    }
    if (max <= min) max = min + 60;
    return { min: min, max: max };
  }

  function cursorTs() {
    var ends = span();
    if (state.live) return ends.max;
    return ends.min + state.cursor * (ends.max - ends.min);
  }

  function visibleFlows() {
    var end = cursorTs();
    var start = end - state.windowSec;
    return ((state.data && state.data.flows) || []).filter(function (flow) {
      return flow.ts <= end + 1 && flow.ts >= start;
    });
  }

  function aggregate(flows) {
    var map = {};
    flows.forEach(function (flow) {
      var from = flow.chain + ":" + flow.src;
      var to = flow.chain + ":" + flow.dst;
      var key = flow.chain + "|" + from + "|" + to + "|" + flow.token;
      var row = map[key];
      if (!row) {
        row = map[key] = {
          id: key, from: from, to: to, chain: flow.chain, token: flow.token,
          usd: 0, amount: 0, count: 0, latest: flow, samples: []
        };
      }
      row.count += 1;
      row.usd += Number(flow.usd || 0);
      row.amount += Number(flow.amount_value || flow.amount || 0);
      if (!row.latest || flow.ts >= row.latest.ts) row.latest = flow;
      if (row.samples.length < 4) row.samples.push(flow);
    });
    return Object.keys(map).map(function (key) { return map[key]; });
  }

  function syncNodes(flows) {
    var next = {};
    var watches = (state.data && state.data.nodes) || [];
    watches.forEach(function (node) {
      if (!node || !node.id) return;
      var prev = state.nodes[node.id] || {};
      next[node.id] = Object.assign({}, prev, node, { touch: {} });
    });
    flows.forEach(function (flow) {
      [ ["src", flow.src, flow.src_label], ["dst", flow.dst, flow.dst_label] ].forEach(function (part) {
        var id = flow.chain + ":" + part[1];
        if (!next[id]) {
          var prev = state.nodes[id] || {};
          next[id] = Object.assign({
            id: id, chain: flow.chain, address: part[1], label: part[2] || part[1],
            watched: false, kind: "account", x: undefined, y: undefined, touch: {}
          }, prev);
        }
      });
    });
    state.nodes = next;
  }

  function layout(width, height, panelOpen) {
    var list = Object.keys(state.nodes).map(function (id) { return state.nodes[id]; });
    var watched = list.filter(function (node) { return node.watched; });
    var others = list.filter(function (node) { return !node.watched; });
    var cx = width * 0.46;
    var cy = height * 0.48;
    var right = panelOpen ? 280 : 24;
    watched.forEach(function (node, index) {
      var angle = (index / Math.max(watched.length, 1)) * Math.PI * 2 - Math.PI / 2;
      var radius = watched.length <= 1 ? 0 : Math.min(width, height) * 0.16;
      node.tx = cx + Math.cos(angle) * radius;
      node.ty = cy + Math.sin(angle) * radius * 0.78;
    });
    others.forEach(function (node) {
      var anchor = watched[0];
      var best = -1;
      watched.forEach(function (item) {
        var weight = (node.touch && node.touch[item.id]) || 0;
        if (weight > best) { best = weight; anchor = item; }
      });
      var angle = flHash(node.id) * Math.PI * 2;
      var radius = Math.min(width, height) * (0.28 + flHash(node.id + ":r") * 0.14);
      var ax = anchor ? anchor.tx : cx;
      var ay = anchor ? anchor.ty : cy;
      node.tx = ax + Math.cos(angle) * radius;
      node.ty = ay + Math.sin(angle) * radius * 0.74;
    });
    for (var pass = 0; pass < 8; pass++) {
      for (var i = 0; i < list.length; i++) {
        for (var j = i + 1; j < list.length; j++) {
          var a = list[i];
          var b = list[j];
          var dx = b.tx - a.tx;
          var dy = b.ty - a.ty;
          var dist = Math.hypot(dx, dy) || 0.01;
          var min = (a.watched ? 78 : 48) + (b.watched ? 64 : 36);
          if (dist < min) {
            var push = (min - dist) * 0.35;
            var ux = dx / dist;
            var uy = dy / dist;
            a.tx -= ux * push;
            a.ty -= uy * push;
            b.tx += ux * push;
            b.ty += uy * push;
          }
        }
      }
    }
    list.forEach(function (node) {
      node.tx = Math.max(54, Math.min(width - right - 20, node.tx));
      node.ty = Math.max(86, Math.min(height - 78, node.ty));
      if (node.x === undefined) {
        node.x = node.tx;
        node.y = node.ty;
      }
    });
  }

  function paintChrome() {
    var data = state.data;
    var demo = !!(data && (data.demo || data.mode === "demo"));
    badge.textContent = demo ? "Demo fixture" : "Live";
    badge.className = "fl-badge " + (demo ? "demo" : "live");
    var summary = (data && data.summary) || {};
    var flows = visibleFlows();
    var inn = 0;
    var out = 0;
    flows.forEach(function (flow) {
      var usd = Number(flow.usd || 0);
      if (flow.direction === "in") inn += usd;
      if (flow.direction === "out") out += usd;
    });
    stats.textContent = flows.length
      ? flows.length + " flows in view\n" + (inn ? "$" + Math.round(inn).toLocaleString() + " in" : "in —") + "\n" + (out ? "$" + Math.round(out).toLocaleString() + " out" : "out —")
      : "";
    if (!data) {
      sub.textContent = state.error || "Reading public chain data…";
    } else if (demo) {
      sub.textContent = "DEMO FIXTURE — these transfers were not read from a chain.";
    } else if (!(data.watches || []).length) {
      sub.textContent = "No watches yet. Ask Hermes to watch an address, or load the demo fixture.";
    } else {
      var big = summary.largest_inflow;
      sub.textContent = big
        ? "Largest inflow " + flMoney(big.amount, big.token, big.usd) + " · " + (summary.count || flows.length) + " transfers in the scanned window."
        : "Watching public transfers. No inflow in this window.";
    }
    warn.textContent = state.error || ((data && data.warnings && data.warnings[0]) || "");
    var tokens = {};
    flows.forEach(function (flow) { tokens[flow.token] = flTokenColor(flow.token); });
    legend.textContent = "";
    Object.keys(tokens).slice(0, 6).forEach(function (token) {
      var line = flEl("div", "fl-key");
      var dot = flEl("span", "fl-dot");
      dot.style.background = tokens[token];
      dot.style.color = tokens[token];
      line.appendChild(dot);
      line.appendChild(document.createTextNode(token));
      legend.appendChild(line);
    });
    var showEmpty = data && !(data.flows || []).length && !(data.demo);
    empty.textContent = "";
    if (!data || showEmpty) {
      var card = flEl("div", "fl-card");
      var kicker = flEl("div", "fl-k");
      kicker.textContent = data ? "Quiet window" : "Flowlight";
      var title = flEl("h2");
      title.textContent = data ? "No flows yet" : "Lighting the routes";
      var copy = flEl("p");
      copy.textContent = data
        ? "The watched accounts have no transfers in the scanned window. That is a real result, not a blank failure."
        : "Public transfers will draw themselves as soon as the read returns.";
      card.appendChild(kicker);
      card.appendChild(title);
      card.appendChild(copy);
      empty.appendChild(card);
    }
    var ends = span();
    var at = cursorTs();
    timeLabel.textContent = flClock(at).slice(11, 16);
    if (state.live) range.value = "1000";
    if (options.autoselect === "largest" && !state.picked) {
      var arcs = aggregate(visibleFlows());
      arcs.sort(function (a, b) { return (b.usd || b.amount) - (a.usd || a.amount); });
      if (arcs[0]) {
        state.selected = { type: "arc", id: arcs[0].id };
        state.picked = true;
      }
    }
    renderPanel();
  }

  function renderPanel() {
    var arcs = aggregate(visibleFlows());
    var arc = null;
    var node = null;
    if (state.selected && state.selected.type === "arc") {
      arc = arcs.filter(function (item) { return item.id === state.selected.id; })[0] || null;
    }
    if (state.selected && state.selected.type === "node") node = state.nodes[state.selected.id] || null;
    if (!arc && !node) {
      panel.hidden = true;
      return;
    }
    panel.hidden = false;
    panel.textContent = "";
    var close = flEl("button", "fl-btn fl-x");
    close.type = "button";
    close.textContent = "Close";
    close.addEventListener("click", function () { state.selected = null; panel.hidden = true; });
    panel.appendChild(close);
    if (node) {
      var title = flEl("h3");
      title.textContent = node.label || node.address;
      var meta = flEl("p");
      meta.textContent = (node.watched ? "Watched · " : "") + node.chain;
      var addr = flEl("p");
      addr.textContent = node.address;
      panel.appendChild(title);
      panel.appendChild(meta);
      panel.appendChild(addr);
      if (node.explorer) {
        var link = flEl("a");
        link.href = node.explorer;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Open address in explorer";
        panel.appendChild(link);
      }
      return;
    }
    var latest = arc.latest || {};
    var heading = flEl("h3");
    heading.textContent = flMoney(latest.amount || arc.amount.toFixed(2), arc.token, latest.usd);
    var dir = flEl("p");
    dir.textContent = arc.count + " transfer" + (arc.count === 1 ? "" : "s") + " on this route · " + (flUsd(arc.usd) || arc.chain);
    var route = flEl("p");
    var fromLabel = latest.src_label && latest.src_label !== latest.src ? latest.src_label : flShort(latest.src);
    var toLabel = latest.dst_label && latest.dst_label !== latest.dst ? latest.dst_label : flShort(latest.dst);
    route.textContent = fromLabel + " → " + toLabel;
    var when = flEl("p");
    when.textContent = flClock(latest.ts);
    panel.appendChild(heading);
    panel.appendChild(dir);
    panel.appendChild(route);
    panel.appendChild(when);
    if (latest.explorer && String(latest.explorer).indexOf("demo-tx") === -1) {
      var tx = flEl("a");
      tx.href = latest.explorer;
      tx.target = "_blank";
      tx.rel = "noopener noreferrer";
      tx.textContent = "Open transfer in explorer";
      panel.appendChild(tx);
    } else if (state.data && state.data.demo) {
      var note = flEl("p");
      note.textContent = "Demo fixture: this arc is not a real transaction.";
      panel.appendChild(note);
    }
  }

  function resize() {
    var rect = stage.getBoundingClientRect();
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = Math.max(1, rect.width);
    var h = Math.max(1, rect.height);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas._css = { w: w, h: h, dpr: dpr };
  }

  function worldFromEvent(event) {
    var rect = canvas.getBoundingClientRect();
    var css = canvas._css || { w: rect.width, h: rect.height };
    var x = ((event.clientX - rect.left) / rect.width) * css.w;
    var y = ((event.clientY - rect.top) / rect.height) * css.h;
    return { x: (x - state.cam.x) / state.cam.k, y: (y - state.cam.y) / state.cam.k, sx: x, sy: y };
  }

  function hit(point) {
    var nodes = state.nodes;
    var ids = Object.keys(nodes);
    for (var i = ids.length - 1; i >= 0; i--) {
      var node = nodes[ids[i]];
      var r = node.watched ? 26 : 14;
      if (Math.hypot(point.x - node.x, point.y - node.y) <= r + 6) return { type: "node", id: node.id, node: node };
    }
    var arcs = aggregate(visibleFlows());
    var best = null;
    var bestDist = 14;
    arcs.forEach(function (arc) {
      var a = nodes[arc.from];
      var b = nodes[arc.to];
      if (!a || !b) return;
      var bend = (flHash(arc.id) - 0.5) * 90;
      var ctrl = control(a, b, bend);
      for (var t = 0; t <= 1; t += 0.08) {
        var p = quad(a, ctrl, b, t);
        var dist = Math.hypot(point.x - p.x, point.y - p.y);
        if (dist < bestDist) { bestDist = dist; best = { type: "arc", id: arc.id, arc: arc }; }
      }
    });
    return best;
  }

  canvas.addEventListener("mousemove", function (event) {
    var point = worldFromEvent(event);
    if (state.drag) {
      state.cam.x += event.clientX - state.drag.x;
      state.cam.y += event.clientY - state.drag.y;
      state.drag.x = event.clientX;
      state.drag.y = event.clientY;
      return;
    }
    var found = hit(point);
    state.hover = found;
    if (!found) { tip.hidden = true; return; }
    tip.hidden = false;
    tip.style.left = point.sx + "px";
    tip.style.top = point.sy + "px";
    if (found.type === "node") tip.textContent = (found.node.label || found.node.address) + " · " + found.node.chain;
    else tip.textContent = found.arc.token + " · " + found.arc.count + " · " + (found.arc.usd ? "$" + Math.round(found.arc.usd).toLocaleString() : "");
  });
  canvas.addEventListener("mousedown", function (event) {
    state.drag = { x: event.clientX, y: event.clientY, ox: event.clientX, oy: event.clientY };
    canvas.classList.add("dragging");
  });
  function onMouseUp(event) {
    if (!state.drag) return;
    var moved = Math.hypot(event.clientX - state.drag.ox, event.clientY - state.drag.oy) > 4;
    canvas.classList.remove("dragging");
    if (!moved) {
      var found = hit(worldFromEvent(event));
      state.selected = found ? { type: found.type, id: found.id } : null;
      renderPanel();
    }
    state.drag = null;
  }
  window.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("dblclick", function () {
    state.cam = { x: 0, y: 0, k: 1 };
  });
  canvas.addEventListener("wheel", function (event) {
    event.preventDefault();
    var next = state.cam.k * (event.deltaY > 0 ? 0.92 : 1.08);
    state.cam.k = Math.max(0.55, Math.min(2.4, next));
  }, { passive: false });

  var ctx2d = canvas.getContext("2d");

  function draw(now) {
    if (state.dead) return;
    var css = canvas._css || { w: 1, h: 1, dpr: 1 };
    if (!canvas._css || stage.clientWidth !== css.w) resize();
    css = canvas._css;
    var flows = visibleFlows();
    syncNodes(flows);
    var arcs = aggregate(flows);
    arcs.forEach(function (arc) {
      var from = state.nodes[arc.from];
      var to = state.nodes[arc.to];
      if (from) from.touch[arc.to] = (from.touch[arc.to] || 0) + arc.count;
      if (to) to.touch[arc.from] = (to.touch[arc.from] || 0) + arc.count;
    });
    layout(css.w, css.h, !panel.hidden);
    Object.keys(state.nodes).forEach(function (id) {
      var node = state.nodes[id];
      node.x += (node.tx - node.x) * 0.08;
      node.y += (node.ty - node.y) * 0.08;
    });
    if (state.playing) {
      state.cursor = Math.min(1, state.cursor + 0.004);
      range.value = String(Math.round(state.cursor * 1000));
      if (state.cursor >= 1) {
        state.playing = false;
        play.textContent = "Play";
      }
      timeLabel.textContent = flClock(cursorTs()).slice(11, 16);
    }
    var g = ctx2d;
    g.setTransform(css.dpr, 0, 0, css.dpr, 0, 0);
    var bg = g.createLinearGradient(0, 0, 0, css.h);
    bg.addColorStop(0, "#12101c");
    bg.addColorStop(0.55, "#090812");
    bg.addColorStop(1, "#05040a");
    g.fillStyle = bg;
    g.fillRect(0, 0, css.w, css.h);
    var glow = g.createRadialGradient(css.w * 0.5, css.h * 0.42, 20, css.w * 0.5, css.h * 0.42, css.w * 0.55);
    glow.addColorStop(0, "rgba(80,110,180,0.20)");
    glow.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = glow;
    g.fillRect(0, 0, css.w, css.h);
    state.dust.forEach(function (speck) {
      speck.y -= speck.s;
      if (speck.y < 0) speck.y += 1;
      g.fillStyle = "rgba(210,220,255," + speck.a + ")";
      g.beginPath();
      g.arc(speck.x * css.w, speck.y * css.h, speck.r, 0, Math.PI * 2);
      g.fill();
    });
    g.translate(state.cam.x, state.cam.y);
    g.scale(state.cam.k, state.cam.k);
    g.lineCap = "round";
    arcs.forEach(function (arc) {
      var a = state.nodes[arc.from];
      var b = state.nodes[arc.to];
      if (!a || !b) return;
      var bend = (flHash(arc.id) - 0.5) * 110;
      var ctrl = control(a, b, bend);
      var color = flTokenColor(arc.token);
      var width = Math.max(1.2, Math.min(8.5, 1.1 + Math.log10(Math.max(arc.usd || arc.amount || 1, 1)) * 1.7));
      var selected = state.selected && state.selected.type === "arc" && state.selected.id === arc.id;
      g.strokeStyle = color;
      g.globalAlpha = selected ? 0.28 : 0.16;
      g.lineWidth = width + 7;
      strokeCurve(g, a, ctrl, b);
      g.globalAlpha = selected ? 0.95 : 0.82;
      g.lineWidth = width;
      strokeCurve(g, a, ctrl, b);
      var bits = 1 + Math.min(4, arc.count);
      for (var i = 0; i < bits; i++) {
        var speed = 0.00012 + Math.min(width, 6) * 0.00003;
        var t = ((now * speed) + flHash(arc.id + ":" + i)) % 1;
        var p = quad(a, ctrl, b, t);
        g.globalAlpha = 0.95;
        g.fillStyle = "#f7fbff";
        g.beginPath();
        g.arc(p.x, p.y, Math.max(1.6, width * 0.45), 0, Math.PI * 2);
        g.fill();
        g.fillStyle = color;
        g.globalAlpha = 0.35;
        g.beginPath();
        g.arc(p.x, p.y, width * 1.6, 0, Math.PI * 2);
        g.fill();
      }
      g.globalAlpha = 1;
    });
    Object.keys(state.nodes).forEach(function (id) {
      var node = state.nodes[id];
      var selected = state.selected && state.selected.type === "node" && state.selected.id === id;
      var color = CHAIN_COLOR[node.chain] || "#d5def2";
      var radius = node.watched ? 16 : 7 + Math.min(8, (node.touch ? Object.keys(node.touch).length : 0));
      g.fillStyle = color;
      g.globalAlpha = node.watched ? 0.18 : 0.12;
      g.beginPath();
      g.arc(node.x, node.y, radius * 2.4, 0, Math.PI * 2);
      g.fill();
      g.globalAlpha = 1;
      g.strokeStyle = color;
      g.lineWidth = selected ? 2.4 : 1.2;
      g.beginPath();
      g.arc(node.x, node.y, radius + 5, now / 900, now / 900 + (node.watched ? 1.4 : 0.8));
      g.stroke();
      var core = g.createRadialGradient(node.x - 2, node.y - 3, 1, node.x, node.y, radius);
      core.addColorStop(0, "#f4f7ff");
      core.addColorStop(1, color);
      g.fillStyle = core;
      g.beginPath();
      g.arc(node.x, node.y, radius, 0, Math.PI * 2);
      g.fill();
      var label = node.label || node.address || "";
      g.font = (node.watched ? "600 12px " : "11px ") + "Outfit, ui-sans-serif, sans-serif";
      g.textAlign = "center";
      var tw = g.measureText(label).width;
      g.fillStyle = "rgba(6,6,12,0.72)";
      roundRect(g, node.x - tw / 2 - 6, node.y + radius + 8, tw + 12, 16, 8);
      g.fill();
      g.fillStyle = "rgba(236,242,255,0.92)";
      g.fillText(label, node.x, node.y + radius + 20);
    });
    g.setTransform(1, 0, 0, 1, 0, 0);
  }

  var timer = null;
  var frame = 0;
  function loop(now) {
    if (state.dead) return;
    draw(now || 0);
    frame = requestAnimationFrame(loop);
  }
  resize();
  load();
  var every = options.setInterval || function (fn, ms) { return setInterval(fn, ms); };
  var clearEvery = options.clearInterval || function (id) { clearInterval(id); };
  timer = every(load, options.pollMs || 8000);
  frame = requestAnimationFrame(loop);
  var observer = null;
  if (typeof ResizeObserver === "function") {
    observer = new ResizeObserver(resize);
    observer.observe(stage);
  }

  function destroy() {
    if (state.dead) return;
    state.dead = true;
    cancelAnimationFrame(frame);
    if (timer) clearEvery(timer);
    if (observer) observer.disconnect();
    window.removeEventListener("mouseup", onMouseUp);
  }
  return { destroy: destroy, reload: load };
}

function control(a, b, bend) {
  var mx = (a.x + b.x) / 2;
  var my = (a.y + b.y) / 2;
  var dx = b.x - a.x;
  var dy = b.y - a.y;
  var len = Math.hypot(dx, dy) || 1;
  return { x: mx + (-dy / len) * bend, y: my + (dx / len) * bend };
}

function quad(a, c, b, t) {
  var u = 1 - t;
  return {
    x: u * u * a.x + 2 * u * t * c.x + t * t * b.x,
    y: u * u * a.y + 2 * u * t * c.y + t * t * b.y
  };
}

function strokeCurve(g, a, c, b) {
  g.beginPath();
  g.moveTo(a.x, a.y);
  g.quadraticCurveTo(c.x, c.y, b.x, b.y);
  g.stroke();
}

function roundRect(g, x, y, w, h, r) {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}

var FlowlightEngine = { mount: mountFlowlight };
if (typeof globalThis !== "undefined") globalThis.FlowlightEngine = FlowlightEngine;
