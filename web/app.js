import {
  formatValue,
  memoryUsedPercent,
  seriesPaths,
  appendSnapshot,
} from "./view-model.js";
const $ = (id) => document.getElementById(id);
const set = (id, value) => {
  if ($(id).textContent !== value) $(id).textContent = value;
};
let paused = false,
  busy = false,
  history = { mode: null, key: null, values: [] },
  budgetVersion = 0;
const svgNode = (name, attrs) => {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attrs))
    node.setAttribute(key, String(value));
  return node;
};
async function get(path) {
  const controller = new AbortController(),
    timeout = setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(path, {
      signal: controller.signal,
      cache: "no-store",
    });
    const data = await response.json();
    if (!response.ok)
      throw new Error(data.error || "Local data is unavailable.");
    return data;
  } finally {
    clearTimeout(timeout);
  }
}
function chart() {
  const values = history.values,
    finite = values.filter(Number.isFinite);
  const min = finite.length
      ? Math.floor((Math.min(...finite) - 5) / 10) * 10
      : 30,
    max = finite.length ? Math.ceil((Math.max(...finite) + 5) / 10) * 10 : 60;
  set("chart-high", `${max} °C`);
  set("chart-low", `${min} °C`);
  set(
    "sample-count",
    `${values.length} received sample${values.length === 1 ? "" : "s"}`,
  );
  const node = $("chart");
  node.replaceChildren();
  const paths = seriesPaths(values, min, max);
  for (const points of paths)
    node.append(svgNode("polyline", { points, class: "chart-line" }));
  if (paths.length) {
    const [x, y] = paths.at(-1).split(" ").at(-1).split(",").map(Number);
    node.append(svgNode("circle", { cx: x, cy: y, r: 3, class: "chart-dot" }));
  }
}
function labelMode(mode) {
  set(
    "mode",
    `${mode === "live" ? "LIVE / LOCAL OS" : "REPLAY / SYNTHETIC"}${paused ? " / PAUSED" : ""}`,
  );
  $("mode").classList.toggle("live", mode === "live");
  $("mode").classList.toggle("paused", paused);
}
async function refresh() {
  if (busy) return;
  busy = true;
  $("refresh").disabled = true;
  try {
    const data = await get("/api/v1/status");
    if (
      data.schema_version !== 1 ||
      !["live", "replay"].includes(data.mode) ||
      !data.metrics ||
      !data.sources
    )
      throw new Error("The local response is unsupported.");
    const m = data.metrics,
      key =
        data.mode === "replay" ? data.trace_elapsed_seconds : data.collected_at;
    history = appendSnapshot(history, {
      mode: data.mode,
      key,
      temperature: m.temperature_c,
    });
    labelMode(data.mode);
    $("mode").dataset.mode = data.mode;
    set("temperature", formatValue(m.temperature_c, "celsius"));
    set("load", formatValue(m.load_1m, "load"));
    set(
      "memory",
      formatValue(
        memoryUsedPercent(m.memory_total_bytes, m.memory_available_bytes),
        "percent",
      ),
    );
    set(
      "memory-detail",
      Number.isFinite(m.memory_total_bytes) &&
        Number.isFinite(m.memory_available_bytes)
        ? `${formatValue(m.memory_available_bytes, "bytes")} available / ${formatValue(m.memory_total_bytes, "bytes")} total`
        : "No supported memory reading",
    );
    set("uptime", formatValue(m.uptime_seconds, "uptime"));
    set("battery", formatValue(m.battery_percent, "percent"));
    set(
      "disk",
      Number.isFinite(m.disk_free_bytes)
        ? `${formatValue(m.disk_free_bytes, "bytes")} free`
        : "Not reported",
    );
    set(
      "sample-time",
      data.mode === "replay"
        ? `Trace ${String(Math.floor(data.trace_elapsed_seconds / 60)).padStart(2, "0")}:${String(data.trace_elapsed_seconds % 60).padStart(2, "0")} · repeats every 60 s`
        : `Read at ${new Date(data.collected_at).toLocaleTimeString()}`,
    );
    set("provenance-note", data.note);
    $("sources").replaceChildren();
    for (const [key, source] of Object.entries(data.sources)) {
      const dt = document.createElement("dt"),
        dd = document.createElement("dd");
      dt.textContent = key.replaceAll("_", " ");
      dd.textContent = source || "Not reported";
      $("sources").append(dt, dd);
    }
    $("status").classList.remove("error");
    document.querySelector(".telemetry").classList.remove("stale");
    set(
      "status",
      data.mode === "replay"
        ? `Synthetic fixture replay. No hardware is measured.${paused ? " Updates paused; this snapshot was fetched manually." : ""}`
        : `Read-only local OS readings.${data.missing.length ? " Unsupported sensors remain unknown." : ""}${paused ? " Updates paused; this snapshot was fetched manually." : ""}`,
    );
    chart();
  } catch (error) {
    set(
      "status",
      "Data unavailable. The last snapshot, if shown, may be stale. Check the local server.",
    );
    $("status").classList.add("error");
    document.querySelector(".telemetry").classList.add("stale");
  } finally {
    busy = false;
    $("refresh").disabled = false;
  }
}
$("pause").addEventListener("click", () => {
  paused = !paused;
  $("pause").setAttribute("aria-pressed", String(paused));
  set("pause", paused ? "Resume updates" : "Pause updates");
  labelMode($("mode").dataset.mode || "replay");
  if (!paused) refresh();
  else
    set(
      "status",
      "Updates paused. The last snapshot is retained. Refresh once to request one sample.",
    );
});
$("refresh").addEventListener("click", refresh);
const powerFields = [
  "capacity_wh",
  "load_w",
  "efficiency",
  "reserve_fraction",
  "supply_w",
];
function clearBudget() {
  budgetVersion++;
  ["runtime", "full-runtime"].forEach((id) => set(id, "—"));
  set("energy", "After efficiency and reserve");
  set("supply-result", "Inputs changed. Calculate to update the model.");
  $("supply-result").classList.remove("over");
  set("power-status", "");
}
powerFields.forEach((id) => $(id).addEventListener("input", clearBudget));
async function calculate(event) {
  event?.preventDefault();
  const version = budgetVersion;
  try {
    const query = new URLSearchParams();
    for (const key of powerFields) {
      const raw = $(key).value;
      if (!raw.trim()) throw new Error("Enter every declared power value.");
      const value = Number(raw);
      if (!Number.isFinite(value))
        throw new Error("Use finite numeric power values.");
      query.set(
        key,
        String(
          ["efficiency", "reserve_fraction"].includes(key)
            ? value / 100
            : value,
        ),
      );
    }
    const result = await get(`/api/v1/budget?${query}`);
    if (version !== budgetVersion) return;
    set("runtime", `${result.usable_runtime_hours.toFixed(2)} h`);
    set("full-runtime", `${result.full_runtime_hours.toFixed(2)} h`);
    set(
      "energy",
      `${result.usable_output_wh.toFixed(2)} usable Wh / ${result.full_output_wh.toFixed(2)} output Wh`,
    );
    set(
      "supply-result",
      `${result.within_nominal_supply ? "Within" : "Above"} the declared nominal rating: ${result.supply_headroom_w.toFixed(2)} W headroom. This is not an electrical test.`,
    );
    $("supply-result").classList.toggle("over", !result.within_nominal_supply);
    set("power-status", "Model updated from the declared inputs.");
  } catch (error) {
    if (version !== budgetVersion) return;
    ["runtime", "full-runtime"].forEach((id) => set(id, "—"));
    set("power-status", error.message);
  }
}
$("power-form").addEventListener("submit", calculate);
chart();
await refresh();
await calculate();
setInterval(() => {
  if (!paused) refresh();
}, 5000);
