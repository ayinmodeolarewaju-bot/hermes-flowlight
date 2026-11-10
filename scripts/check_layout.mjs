// Confirm the header, summary, and legend do not overlap at the demo sizes.
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const chrome = spawn("/usr/local/bin/google-chrome", [
  "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
  "--user-data-dir=/tmp/flowlight-layout-chrome",
  "--remote-debugging-port=9333",
  "--window-size=1920,1080",
  "about:blank",
], { stdio: "ignore" });

let ws;
let seq = 0;
const pending = new Map();
function send(method, params = {}) {
  const id = ++seq;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout " + method)), 20000);
    pending.set(id, (result) => { clearTimeout(timer); resolve(result || {}); });
  });
}

async function connect() {
  for (let i = 0; i < 30; i++) {
    try {
      const pages = await fetch("http://127.0.0.1:9333/json").then((r) => r.json());
      const page = pages.find((item) => item.type === "page");
      ws = new WebSocket(page.webSocketDebuggerUrl);
      await new Promise((resolve, reject) => {
        ws.addEventListener("open", resolve);
        ws.addEventListener("error", reject);
      });
      ws.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);
        if (message.id && pending.has(message.id)) {
          const done = pending.get(message.id);
          pending.delete(message.id);
          done(message.result);
        }
      });
      await send("Page.enable");
      await send("Runtime.enable");
      await send("Emulation.setDeviceMetricsOverride", {
        width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false,
      });
      return;
    } catch {
      await delay(300);
    }
  }
  throw new Error("chrome did not open");
}

const probe = `(() => {
  function box(node) {
    const r = node.getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, w: r.width, h: r.height };
  }
  function hit(a, b) {
    if (!a || !b || a.h < 1 || b.h < 1) return false;
    return a.left < b.right - 1 && a.right > b.left + 1 && a.top < b.bottom - 1 && a.bottom > b.top + 1;
  }
  const sub = document.querySelector(".fl-sub");
  const legend = document.querySelector(".fl-legend");
  const stats = document.querySelector(".fl-stats");
  const word = document.querySelector(".fl-word");
  const row = document.querySelector(".fl-row");
  const b = {
    sub: box(sub), legend: box(legend), stats: box(stats), word: box(word), row: box(row)
  };
  return {
    text: sub.textContent,
    boxes: b,
    overlaps: {
      subLegend: hit(b.sub, b.legend),
      subStats: hit(b.sub, b.stats),
      legendStats: hit(b.legend, b.stats),
      wordSub: hit(b.word, b.sub),
      rowSub: hit(b.row, b.sub),
      rowLegend: hit(b.row, b.legend)
    }
  };
})()`;

try {
  await connect();
  await send("Page.navigate", { url: "http://127.0.0.1:8787/?live=1" });
  await delay(4000);
  const sizes = [[1280, 720], [1440, 900], [1920, 1080]];
  let failed = false;
  for (const [width, height] of sizes) {
    await send("Emulation.setDeviceMetricsOverride", {
      width, height, deviceScaleFactor: 1, mobile: false,
    });
    await delay(500);
    const result = await send("Runtime.evaluate", { expression: probe, returnByValue: true });
    const value = result.result.value;
    const bad = Object.entries(value.overlaps).filter(([, on]) => on).map(([name]) => name);
    console.log(width + "x" + height, bad.length ? "OVERLAP " + bad.join(",") : "clear", JSON.stringify(value.boxes.sub), "legend", JSON.stringify(value.boxes.legend));
    console.log("  ", (value.text || "").slice(0, 140));
    if (bad.length) failed = true;
  }
  if (failed) process.exitCode = 1;
} finally {
  try { ws && ws.close(); } catch {}
  chrome.kill("SIGKILL");
}
