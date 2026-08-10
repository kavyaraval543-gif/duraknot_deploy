"use strict";
/* Reproduces the "Output realism" evidence cited in the submitted PDF:
 * five independent 20-minute runs of the simulator, reporting the OEE,
 * availability, quality and length ranges they produce.
 *
 * This is informational, not a pass/fail gate -- the simulator is
 * intentionally stochastic (see DATA_SOURCES.md for why its parameters are
 * calibrated the way they are), so the exact numbers will vary run to run.
 * That's the point: this script lets anyone re-run the claim rather than
 * trust a number frozen in a slide deck.
 *
 * Usage: node validate_output_realism.js [runs] [ticksPerRun]
 *   runs         default 5   (matches "five independent runs" in the PDF)
 *   ticksPerRun  default 1200 (20 simulated minutes, 1 tick = 1 virtual second)
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const RUNS = parseInt(process.argv[2] || "5", 10);
const TICKS_PER_RUN = parseInt(process.argv[3] || "1200", 10);

const INDEX_PATH = path.join(__dirname, "..", "index.html");
const html = fs.readFileSync(INDEX_PATH, "utf8");

const scriptMatch = html.match(/<script>\s*"use strict";[\s\S]*?<\/script>/);
if (!scriptMatch) {
  console.error("FAIL: could not locate the dashboard's inline <script> block in index.html");
  process.exit(1);
}
const scriptSrc = scriptMatch[0].replace(/^<script>/, "").replace(/<\/script>$/, "");
const htmlWithoutScript = html.slice(0, scriptMatch.index) + html.slice(scriptMatch.index + scriptMatch[0].length);

const dom = new JSDOM(htmlWithoutScript, {
  url: "file:///dashboard/index.html",
  runScripts: "dangerously",
  pretendToBeVisual: true,
});
const { window } = dom;

// Same headless-canvas + layout stand-ins as render_check.js -- this script
// only needs the simulation/OEE math (no DOM dependency of its own), but the
// dashboard's own boot sequence renders once regardless, so it still needs
// somewhere harmless to draw.
Object.defineProperty(window.HTMLElement.prototype, "clientWidth", { get: () => 480, configurable: true });
Object.defineProperty(window.HTMLElement.prototype, "clientHeight", { get: () => 240, configurable: true });
window.HTMLCanvasElement.prototype.getContext = function () {
  return new Proxy({}, {
    get(target, prop) {
      if (prop === "measureText") return () => ({ width: 10 });
      if (prop === "createLinearGradient") return () => ({ addColorStop() {} });
      if (typeof prop === "symbol") return undefined;
      return (...args) => {};
    },
    set(target, prop, value) { target[prop] = value; return true; },
  });
};

let threw = null;
window.addEventListener("error", (e) => { threw = threw || e.error || new Error(e.message); });
const scriptEl = window.document.createElement("script");
scriptEl.textContent = scriptSrc;
window.document.body.appendChild(scriptEl);
if (window.timer) window.clearInterval(window.timer);

if (threw) {
  console.error("FAIL: dashboard script threw during boot: " + threw.stack);
  process.exit(1);
}

function runTrial() {
  window.resetCounters("validation trial");
  window.seed(TICKS_PER_RUN - 20); // resetCounters() already seeds 20 ticks
  const o = window.computeOEE();
  return {
    oee: o.oee * 100,
    availability: o.availability * 100,
    performance: o.performance * 100,
    quality: o.quality * 100,
    length: window.state.totalLength,
    defects: window.state.defectEvents,
    stoppages: window.state.stoppages,
  };
}

const results = [];
for (let i = 0; i < RUNS; i++) results.push(runTrial());

console.log(`${RUNS} independent ${(TICKS_PER_RUN / 60).toFixed(0)}-minute simulated runs:\n`);
console.log("run  OEE%   Avail%  Perf%   Qual%   Length(m)  Defects  Stoppages");
results.forEach((r, i) => {
  console.log(
    `${String(i + 1).padStart(3)}  ${r.oee.toFixed(1).padStart(5)}  ${r.availability.toFixed(1).padStart(6)}  ` +
    `${r.performance.toFixed(1).padStart(5)}  ${r.quality.toFixed(1).padStart(5)}  ${r.length.toFixed(1).padStart(9)}  ` +
    `${String(r.defects).padStart(7)}  ${String(r.stoppages).padStart(9)}`
  );
});

function range(key) {
  const vals = results.map((r) => r[key]);
  return `${Math.min(...vals).toFixed(1)}-${Math.max(...vals).toFixed(1)}`;
}
console.log("\nRanges across runs:");
console.log(`  OEE          ${range("oee")}%`);
console.log(`  Availability ${range("availability")}%`);
console.log(`  Performance  ${range("performance")}%`);
console.log(`  Quality      ${range("quality")}%`);
console.log(`  Length       ${range("length")} m`);

process.exit(0);
