// Capture stills and a short animation from the loopback Flowlight page.
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as delay } from "node:timers/promises";

const chromePath = process.env.CHROME || "/usr/local/bin/google-chrome";
const base = process.env.FLOWLIGHT_URL || "http://127.0.0.1:8787";
const outDir = process.env.FLOWLIGHT_OUT || "/workspace/docs";
const framesDir = "/tmp/flowlight-frames";
mkdirSync(framesDir, { recursive: true });
mkdirSync(`${outDir}/screenshots`, { recursive: true });
mkdirSync(`${outDir}/demo`, { recursive: true });

const chrome = spawn(chromePath, [
  "--headless=new",
  "--no-sandbox",
  "--disable-dev-shm-usage",
  "--disable-gpu",
  "--hide-scrollbars",
  "--window-size=1440,900",
  "--user-data-dir=/tmp/flowlight-chrome",
  "--remote-debugging-port=9222",
  "about:blank",
], { stdio: "ignore" });

let ws;
let seq = 0;
const pending = new Map();

function send(method, params = {}) {
  const id = ++seq;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`timeout ${method}`)), 20000);
    pending.set(id, (result) => {
      clearTimeout(timer);
      resolve(result);
    });
  });
}

async function connect() {
  for (let attempt = 0; attempt < 30; attempt++) {
    try {
      const pages = await fetch("http://127.0.0.1:9222/json").then((r) => r.json());
      const page = pages.find((item) => item.type === "page");
      if (!page) throw new Error("no page");
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
          done(message.result || {});
        }
      });
      await send("Page.enable");
      await send("Runtime.enable");
      return;
    } catch {
      await delay(300);
    }
  }
  throw new Error("chrome debugging port did not open");
}

async function shot(name) {
  const result = await send("Page.captureScreenshot", { format: "png" });
  const file = `${outDir}/screenshots/${name}.png`;
  writeFileSync(file, Buffer.from(result.data, "base64"));
  console.log("wrote", file);
}

async function open(url) {
  await send("Page.navigate", { url });
  await delay(2800);
}

try {
  await connect();
  await open(`${base}/?select=largest`);
  await shot("live-flows");
  await shot("arc-detail");
  await open(`${base}/?demo=1&select=largest`);
  await shot("demo-fixture");
  await open(`${base}/?select=largest`);
  await delay(600);
  const count = 8 * 12;
  for (let i = 0; i < count; i++) {
    const result = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(`${framesDir}/${String(i).padStart(3, "0")}.png`, Buffer.from(result.data, "base64"));
    await delay(70);
  }
  console.log("frames", count);
} finally {
  try { ws && ws.close(); } catch {}
  chrome.kill("SIGKILL");
}
