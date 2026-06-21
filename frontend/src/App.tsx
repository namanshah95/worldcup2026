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
      <Route path="/pick-em" element={<ProtectedRoute><PickEmPage /></ProtectedRoute>} />
      <Route path="/captain" element={<ProtectedRoute><CaptainPage /></ProtectedRoute>} />
      <Route path="/bingo" element={<ProtectedRoute><BingoPage /></ProtectedRoute>} />
      <Route path="/trivia" element={<ProtectedRoute><TriviaPage /></ProtectedRoute>} />
      <Route path="/leaderboard" element={<ProtectedRoute><LeaderboardPage /></ProtectedRoute>} />
      <Route path="/scoring" element={<ProtectedRoute><ScoringPage /></ProtectedRoute>} />
      <Route path="/attendance" element={<ProtectedRoute><AttendancePage /></ProtectedRoute>} />
      {/* Legacy routes redirect to universal screens */}
      <Route path="/game/:gameId/pick-em" element={<Navigate to="/pick-em" replace />} />
      <Route path="/game/:gameId/captain" element={<Navigate to="/captain" replace />} />
      <Route path="/game/:gameId/bingo" element={<Navigate to="/bingo" replace />} />
      <Route path="/game/:gameId/trivia" element={<Navigate to="/trivia" replace />} />
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
