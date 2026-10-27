import test from "node:test";
import assert from "node:assert/strict";
import {
  formatValue,
  memoryUsedPercent,
  seriesPaths,
  appendSnapshot,
} from "../web/view-model.js";
test("missing values stay unknown and binary memory units are explicit", () => {
  assert.equal(formatValue(null, "celsius"), "Not reported");
  assert.equal(formatValue(NaN, "load"), "Not reported");
  assert.equal(formatValue(43.56, "celsius"), "43.6 °C");
  assert.equal(formatValue(1024 ** 3, "bytes"), "1.00 GiB");
  assert.equal(formatValue(0.51, "load"), "0.51");
  assert.equal(memoryUsedPercent(100, 25), 75);
  for (const pair of [
    [0, 0],
    [100, 101],
    [null, 10],
    [100, NaN],
  ])
    assert.equal(memoryUsedPercent(...pair), null);
});
test("received history de-duplicates a sample, caps its size and never mixes replay with live", () => {
  let state = { mode: null, key: null, values: [] };
  state = appendSnapshot(state, { mode: "replay", key: 0, temperature: 42 });
  assert.equal(
    appendSnapshot(state, { mode: "replay", key: 0, temperature: 42 }),
    state,
  );
  for (let index = 1; index < 80; index++)
    state = appendSnapshot(state, {
      mode: "replay",
      key: index,
      temperature: index % 3 ? 43 : null,
    });
  assert.equal(state.values.length, 60);
  assert.ok(state.values.includes(null));
  state = appendSnapshot(state, {
    mode: "live",
    key: "2026-10-27T00:00:00Z",
    temperature: null,
  });
  assert.deepEqual(state.values, [null]);
});
test("history draws only received finite samples and keeps missing-value gaps", () => {
  assert.deepEqual(seriesPaths([], 0, 100), []);
  const paths = seriesPaths([10, 20, null, 30], 0, 100, 300, 100);
  assert.equal(paths.length, 2);
  assert.equal(paths[0], "0,90 100,80");
  assert.equal(paths[1], "300,70");
  assert.throws(() => seriesPaths([1], 10, 10));
  assert.throws(() => seriesPaths([1], 0, 100, 0, 100));
});
