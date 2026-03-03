// Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "React Frontend → Page Structure"
/**
 * App root — defines route structure for Saudi Sentinel AI dashboard.
 *
 * Page routes (from docs/plans/LEVEL-3-SYSTEM.md — "Page Structure"):
 *   /                         → Overview Dashboard (landing)
 *   /map                      → Full-screen interactive map (all 9 project layers)
 *   /projects                 → Project grid with status cards
 *   /projects/:id             → Individual project dashboard
 *   /projects/:id/map         → Project-specific map view
 *   /projects/:id/trends      → Time-series analysis (Recharts)
 *   /projects/:id/reports     → Downloadable PDF/CSV reports
 *   /alerts                   → Alert center (active + history)
 *   /compare                  → Before/after comparison tool
 *   /admin                    → System administration
 *   /admin/pipelines          → Airflow pipeline status
 *   /admin/models             → MLflow model registry view
 *   /admin/aois               → AOI management
 *   /api-docs                 → Interactive API documentation
 *
 * Tech stack: React 18 + TypeScript + Vite + Deck.gl + Mapbox GL JS +
 *             Recharts + TanStack Query + Zustand + Tailwind CSS
 *
 * See: docs/plans/LEVEL-3-SYSTEM.md — "React Frontend"
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Pages (stubs — see src/pages/)
import OverviewPage from './pages/OverviewPage';
import MapPage from './pages/MapPage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import ProjectMapPage from './pages/ProjectMapPage';
import ProjectTrendsPage from './pages/ProjectTrendsPage';
import ProjectReportsPage from './pages/ProjectReportsPage';
import AlertsPage from './pages/AlertsPage';
import ComparePage from './pages/ComparePage';
import AdminPage from './pages/AdminPage';
import AdminPipelinesPage from './pages/AdminPipelinesPage';
import AdminModelsPage from './pages/AdminModelsPage';
import AdminAOIsPage from './pages/AdminAOIsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,       // 1 minute — satellite data doesn't change that fast
      refetchInterval: 300_000, // 5 minutes — auto-refresh dashboard
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/"                        element={<OverviewPage />} />
          <Route path="/map"                     element={<MapPage />} />
          <Route path="/projects"                element={<ProjectsPage />} />
          <Route path="/projects/:id"            element={<ProjectDetailPage />} />
          <Route path="/projects/:id/map"        element={<ProjectMapPage />} />
          <Route path="/projects/:id/trends"     element={<ProjectTrendsPage />} />
          <Route path="/projects/:id/reports"    element={<ProjectReportsPage />} />
          <Route path="/alerts"                  element={<AlertsPage />} />
          <Route path="/compare"                 element={<ComparePage />} />
          <Route path="/admin"                   element={<AdminPage />} />
          <Route path="/admin/pipelines"         element={<AdminPipelinesPage />} />
          <Route path="/admin/models"            element={<AdminModelsPage />} />
          <Route path="/admin/aois"              element={<AdminAOIsPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
