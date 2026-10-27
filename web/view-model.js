export function formatValue(value, unit) {
  if (!Number.isFinite(value)) return "Not reported";
  if (unit === "celsius") return `${value.toFixed(1)} °C`;
  if (unit === "bytes") return `${(value / 1024 ** 3).toFixed(2)} GiB`;
  if (unit === "load") return value.toFixed(2);
  if (unit === "uptime")
    return `${Math.floor(value / 3600)}h ${Math.floor(value / 60) % 60}m`;
  return `${value.toFixed(0)}%`;
}
export function memoryUsedPercent(total, available) {
  return Number.isFinite(total) &&
    Number.isFinite(available) &&
    total > 0 &&
    available >= 0 &&
    available <= total
    ? ((total - available) / total) * 100
    : null;
}
export function appendSnapshot(state, snapshot) {
  const sameMode = state.mode === snapshot.mode;
  if (sameMode && state.key === snapshot.key) return state;
  return {
    mode: snapshot.mode,
    key: snapshot.key,
    values: [...(sameMode ? state.values : []), snapshot.temperature].slice(
      -60,
    ),
  };
}
export function seriesPaths(values, min, max, width = 600, height = 200) {
  if (
    ![min, max, width, height].every(Number.isFinite) ||
    max <= min ||
    width <= 0 ||
    height <= 0
  )
    throw new Error("Invalid chart scale.");
  const groups = [];
  let current = [];
  values.forEach((value, index) => {
    if (!Number.isFinite(value)) {
      if (current.length) groups.push(current.join(" "));
      current = [];
      return;
    }
    current.push(
      `${values.length === 1 ? width / 2 : (index / (values.length - 1)) * width},${height - ((value - min) / (max - min)) * height}`,
    );
  });
  if (current.length) groups.push(current.join(" "));
  return groups;
}
