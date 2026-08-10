"use strict";
/* Headless render-verification harness for the Duraknot dashboard.
 *
 * Loads the unmodified ../index.html into jsdom, replaces every canvas's
 * 2D context with an "instrumented" stand-in that records every draw call,
 * then runs the dashboard's own draw functions (drawTrend, drawDefectStrip,
 * drawOeeTrend, drawLoss, drawPareto, drawDrate) plus a full renderAll().
 *
 * Pass criteria (matches the submission's claim): all six charts draw at
 * least one primitive without throwing, and every DOM reference the
 * dashboard touches resolves (a null ref would throw and fail the run).
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const INDEX_PATH = path.join(__dirname, "..", "index.html");
const SIX_CANVASES = ["cv-trend", "cv-defect", "cv-oee", "cv-loss", "cv-pareto", "cv-drate"];
const DRAW_FUNCTIONS = ["drawTrend", "drawDefectStrip", "drawOeeTrend", "drawLoss", "drawPareto", "drawDrate"];

function fail(msg) {
  console.error("FAIL: " + msg);
  process.exitCode = 1;
}

const html = fs.readFileSync(INDEX_PATH, "utf8");

// Pull the dashboard's inline <script>...</script> out so we can patch the
// environment (canvas + layout) BEFORE it runs, instead of after.
const scriptMatch = html.match(/<script>\s*"use strict";[\s\S]*?<\/script>/);
if (!scriptMatch) {
  fail("could not locate the dashboard's inline <script> block in index.html");
  process.exit(1);
}
const scriptSrc = scriptMatch[0].replace(/^<script>/, "").replace(/<\/script>$/, "");
const htmlWithoutScript = html.slice(0, scriptMatch.index) + html.slice(scriptMatch.index + scriptMatch[0].length);

const dom = new JSDOM(htmlWithoutScript, {
  url: "file:///dashboard/index.html", // location.protocol === 'file:' -> skips the live-backend fetch probe
  runScripts: "dangerously", // needed so the <script> element we inject below actually executes
  pretendToBeVisual: true,
});
const { window } = dom;

// jsdom has no layout engine, so every element reports 0x0. The dashboard's
// setupCanvas() treats 0-width/height as "hidden view, skip" -- give every
// canvas a plausible on-screen size so drawing actually proceeds.
Object.defineProperty(window.HTMLElement.prototype, "clientWidth", { get: () => 480, configurable: true });
Object.defineProperty(window.HTMLElement.prototype, "clientHeight", { get: () => 240, configurable: true });

const calls = {}; // canvas id -> number of draw-primitive calls recorded
const NOOP_RETURN_SELF_PROPS = new Set(["strokeStyle", "fillStyle", "font", "textAlign", "textBaseline", "lineWidth", "lineJoin", "lineCap"]);

function makeInstrumentedContext(canvasId) {
  const store = {};
  return new Proxy(store, {
    get(target, prop) {
      if (prop === "measureText") return () => ({ width: 10 });
      if (prop === "createLinearGradient") return () => ({ addColorStop() {} });
      if (typeof prop === "symbol") return undefined;
      if (NOOP_RETURN_SELF_PROPS.has(prop)) return target[prop];
      return (...args) => {
        calls[canvasId] = (calls[canvasId] || 0) + 1;
      };
    },
    set(target, prop, value) {
      target[prop] = value;
      return true;
    },
  });
}

window.HTMLCanvasElement.prototype.getContext = function () {
  return makeInstrumentedContext(this.id);
};

let threw = null;
window.addEventListener("error", (e) => {
  threw = threw || e.error || new Error(e.message);
});
try {
  // Inject as a real <script> element (rather than window.eval) so the
  // dashboard's top-level `var`/`function` declarations reliably attach to
  // `window`, exactly as they would from the classic <script> tag in the
  // real index.html -- this lets us call its internals below.
  const scriptEl = window.document.createElement("script");
  scriptEl.textContent = scriptSrc;
  window.document.body.appendChild(scriptEl);
} catch (err) {
  threw = err;
}

if (threw) {
  fail("the dashboard script threw during initial load/boot: " + threw.stack);
} else {
  console.log("PASS: dashboard script loaded and booted without exception");
}

if (!threw) {
  for (const fn of DRAW_FUNCTIONS) {
    try {
      if (typeof window[fn] !== "function") {
        fail(`window.${fn} is not defined -- expected draw function missing`);
        continue;
      }
      window[fn]();
    } catch (err) {
      fail(`${fn}() threw: ${err.stack}`);
    }
  }

  try {
    window.renderAll();
  } catch (err) {
    fail("renderAll() threw: " + err.stack);
  }
}

console.log("");
for (const id of SIX_CANVASES) {
  const n = calls[id] || 0;
  if (n > 0) {
    console.log(`PASS: #${id} drew ${n} canvas primitive call(s)`);
  } else {
    fail(`#${id} recorded zero draw calls -- chart did not render`);
  }
}

if (!threw) {
  const requiredIds = [
    "k-length", "k-speed", "k-defect", "k-status",
    "ring-oee-txt", "ring-a-txt", "ring-p-txt", "ring-q-txt",
    "oee-tbody", "pareto-tbody", "alert-tbody", "a-total",
  ];
  for (const id of requiredIds) {
    const el = window.document.getElementById(id);
    if (!el) {
      fail(`#${id} not found in DOM after renderAll()`);
    } else if (!el.textContent && !el.innerHTML) {
      fail(`#${id} resolved but was never populated`);
    }
  }
  console.log("PASS: all inspected DOM references resolved and were populated");
}

console.log("");
if (process.exitCode) {
  console.log("RENDER CHECK: FAILED");
} else {
  console.log(`RENDER CHECK: PASSED -- ${SIX_CANVASES.length} charts, ${DRAW_FUNCTIONS.length} draw functions, full renderAll() clean`);
}

// The dashboard's own boot sequence starts a setInterval tick loop (and a
// clock timer) that would otherwise keep the Node event loop alive forever.
if (window.timer) window.clearInterval(window.timer);
process.exit(process.exitCode || 0);
