// Image Processing Worker
// Handles CPU-intensive tasks off the main thread

self.onmessage = (e: MessageEvent) => {
  const { type, data, options } = e.data;

  if (type === "COMPUTE_HISTOGRAM") {
    const histogram = computeHistogram(data, options?.bins || 256);
    self.postMessage({ type: "HISTOGRAM_RESULT", payload: histogram });
  } else if (type === "APPLY_FILTER") {
    // e.g. Sharpening via convolution
    self.postMessage({ type: "FILTER_COMPLETE", payload: null });
  }
};

function computeHistogram(
  pixelData: Float32Array | Int16Array | Uint16Array,
  bins: number
) {
  // 1. Find Min/Max
  let min = Infinity;
  let max = -Infinity;

  for (let i = 0; i < pixelData.length; i++) {
    const val = pixelData[i];
    if (val < min) min = val;
    if (val > max) max = val;
  }

  // 2. Compute Histogram
  const histogram = new Uint32Array(bins);
  const range = max - min;
  if (range === 0) return { min, max, histogram };

  for (let i = 0; i < pixelData.length; i++) {
    const val = pixelData[i];
    const binIndex = Math.floor(((val - min) / range) * (bins - 1));
    histogram[binIndex]++;
  }

  return { min, max, histogram };
}
