// Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "Interactive Map View (Main Screen)"
/**
 * MapView — Full-screen interactive map using Deck.gl + Mapbox GL JS.
 *
 * Layer panel (from plan doc ASCII mockup):
 *   ☑ Urban Sprawl  — Red/gray change detection overlay
 *   ☑ Vegetation    — Green gradient SAVI intensity
 *   ☐ Crops         — Categorical crop type map
 *   ☐ Flood Risk    — Blue gradient probability
 *   ... (9 total toggleable layers)
 *
 * Each layer is served as XYZ PNG tiles from:
 *   GET /api/v1/tiles/{project_id}/{z}/{x}/{y}.png
 *
 * See: docs/plans/LEVEL-3-SYSTEM.md — "Key UI Components → Interactive Map View"
 */

export default function MapView({ activeLayers, selectedDate, onLayerToggle }) {
  // TODO: Implement
  // 1. Initialize Mapbox GL JS base map (react-map-gl)
  // 2. Add Deck.gl TileLayer for each active project layer
  //    source: `/api/v1/tiles/{project_id}/{z}/{x}/{y}.png`
  // 3. Layer panel for toggling visibility
  // 4. Date selector for historical views
  // 5. Status bar: latest metrics for visible layers
  return <div style={{ width: '100%', height: '100vh', background: '#1a1a2e' }} />;
}
