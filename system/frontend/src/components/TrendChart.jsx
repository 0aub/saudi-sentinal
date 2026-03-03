// Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "Project Dashboard → Charts"
/**
 * TrendChart — Recharts time-series visualization of project metrics.
 *
 * Used for: urban expansion trend, NDVI trend, farm count trend, risk score trend, etc.
 * Data source: GET /api/v1/projects/{id}/stats
 *
 * See: docs/plans/LEVEL-3-SYSTEM.md — "Project Dashboard → Monthly Change Trend"
 */

export default function TrendChart({ projectId, aoi, metric }) {
  // TODO: Implement
  // 1. Fetch time-series data from /api/v1/projects/{projectId}/stats?aoi={aoi}
  // 2. Render Recharts LineChart or AreaChart
  // 3. X-axis: date, Y-axis: metric value, tooltip: formatted value
  return null;
}
