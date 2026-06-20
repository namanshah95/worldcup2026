import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import PickEmPage from './pages/PickEmPage';
import CaptainPage from './pages/CaptainPage';
import BingoPage from './pages/BingoPage';
import TriviaPage from './pages/TriviaPage';
import LeaderboardPage from './pages/LeaderboardPage';
import ScoringPage from './pages/ScoringPage';
import AttendancePage from './pages/AttendancePage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="text-gold text-2xl animate-pulse">⚽</div>
      </div>
    );
  }
  if (!user) return <Navigate to="/register" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/game/:gameId/pick-em" element={<ProtectedRoute><PickEmPage /></ProtectedRoute>} />
      <Route path="/game/:gameId/captain" element={<ProtectedRoute><CaptainPage /></ProtectedRoute>} />
      <Route path="/game/:gameId/bingo" element={<ProtectedRoute><BingoPage /></ProtectedRoute>} />
      <Route path="/game/:gameId/trivia" element={<ProtectedRoute><TriviaPage /></ProtectedRoute>} />
      <Route path="/captain" element={<ProtectedRoute><CaptainPage /></ProtectedRoute>} />
      <Route path="/leaderboard" element={<ProtectedRoute><LeaderboardPage /></ProtectedRoute>} />
      <Route path="/scoring" element={<ProtectedRoute><ScoringPage /></ProtectedRoute>} />
      <Route path="/attendance" element={<ProtectedRoute><AttendancePage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
