// Record the live Flowlight page: hold, scrub, play, click the largest inflow.
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as delay } from "node:timers/promises";

const outDir = "/tmp/flowlight-browser";
mkdirSync(outDir, { recursive: true });
const chrome = spawn("/usr/local/bin/google-chrome", [
  "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
  "--hide-scrollbars", "--window-size=1920,1080",
  "--user-data-dir=/tmp/flowlight-demo-chrome",
  "--remote-debugging-port=9444",
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
  for (let i = 0; i < 40; i++) {
    try {
      const pages = await fetch("http://127.0.0.1:9444/json").then((r) => r.json());
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
      await delay(250);
    }
  }
  throw new Error("chrome did not open");
}

async function shot() {
  const result = await send("Page.captureScreenshot", {
    format: "jpeg", quality: 72,
    clip: { x: 0, y: 0, width: 1920, height: 1080, scale: 1 },
  });
  return Buffer.from(result.data, "base64");
}

async function evalValue(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true });
  return result.result && result.result.value;
}

async function click(x, y) {
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
}

try {
  await connect();
  await send("Page.navigate", { url: "http://127.0.0.1:8787/?live=1&poll=180000" });
  const started = Date.now();
  let readyAt = 0;
  let frame = 0;
  let didScrub = false;
  let didPlay = false;
  let didClick = false;
  let savedWide = false;
  let savedDetail = false;
  const holdMs = 46000;
  while (Date.now() - started < holdMs) {
    const headline = await evalValue("globalThis.__flowlight && globalThis.__flowlight.headline()") || "";
    const t = Date.now() - (readyAt || started);
    if (!readyAt && headline.indexOf("Largest inflow") === 0) readyAt = Date.now();
    if (readyAt && !didScrub && t > 12000) {
      await evalValue("globalThis.__flowlight.scrub(0.08)");
      didScrub = true;
    }
    if (readyAt && didScrub && !didPlay && t > 18000) {
      await evalValue("globalThis.__flowlight.play()");
      didPlay = true;
    }
    if (readyAt && didPlay && !didClick && t > 26000) {
      const point = await evalValue("globalThis.__flowlight.inflowPoint()");
      if (point && point.x) {
        await click(point.x, point.y);
        didClick = true;
      }
    }
    const jpg = await shot();
    writeFileSync(`${outDir}/${String(frame).padStart(5, "0")}.jpg`, jpg);
    if (readyAt && t > 3500 && !savedWide) {
      writeFileSync("/tmp/flowlight-wide.jpg", jpg);
      savedWide = true;
    }
    if (didClick && t > 29000 && !savedDetail) {
      writeFileSync("/tmp/flowlight-detail.jpg", jpg);
      savedDetail = true;
    }
    frame += 1;
  }
  const headline = await evalValue("globalThis.__flowlight && globalThis.__flowlight.headline()") || "";
  writeFileSync("/tmp/flowlight-headline.txt", headline + "\n");
  console.log("frames", frame);
  console.log("headline", headline);
  console.log("flags", { didScrub, didPlay, didClick });
} finally {
  try { ws && ws.close(); } catch {}
  chrome.kill("SIGKILL");
}
