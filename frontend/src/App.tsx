import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import AppShell from './components/AppShell';
import AuthModal from './components/AuthModal';

const Landing = lazy(() => import('./pages/Landing'));
const FindFish = lazy(() => import('./pages/FindFish'));
const ContributeSighting = lazy(() => import('./pages/ContributeSighting'));
const SpeciesPage = lazy(() => import('./pages/SpeciesPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));

const router = createBrowserRouter([
  // The shelf stands alone: the field manuals bring their own topbar and footer, and the
  // app's chrome around them would compete with the effect.
  { path: '/', element: <Suspense fallback={<PageLoading />}><Landing /></Suspense> },
  {
    // Everything the books open lives inside the app shell.
    element: <AppShell />,
    children: [
      { path: 'find', element: <Suspense fallback={<PageLoading />}><FindFish /></Suspense> },
      { path: 'contribute', element: <Suspense fallback={<PageLoading />}><ContributeSighting /></Suspense> },
      { path: 'species', element: <Suspense fallback={<PageLoading />}><SpeciesPage /></Suspense> },
      { path: 'species/:id', element: <Suspense fallback={<PageLoading />}><SpeciesPage /></Suspense> },
      { path: 'profile', element: <Suspense fallback={<PageLoading />}><ProfilePage /></Suspense> },
      { path: 'admin', element: <Suspense fallback={<PageLoading />}><AdminPage /></Suspense> },
    ],
  },
]);

function PageLoading() {
  return (
    <div className="flex h-full items-center justify-center text-xs tracking-[0.3em] text-cyan-500 aq-pulse">
      LOADING…
    </div>
  );
}

export default function App() {
  return (
    <>
      <RouterProvider router={router} />
      <AuthModal />
    </>
  );
}
