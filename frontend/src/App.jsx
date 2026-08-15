import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import { Shield, LayoutDashboard } from 'lucide-react';

// No real auth — this just gates the landing experience so /login shows first each session.
export const SESSION_KEY = 'deepguard_entered';

function RequireEntry({ children }) {
  const entered = sessionStorage.getItem(SESSION_KEY) === 'true';
  return entered ? children : <Navigate to="/login" replace />;
}

function AppLayout() {
  const location = useLocation();
  const isLogin = location.pathname === '/login';

  return (
    <div className="min-h-screen bg-background text-gray-100 font-sans">
      {/* Navigation Bar */}
      {!isLogin && (
        <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <Shield className="w-8 h-8 text-accent" />
                <span className="font-bold text-xl tracking-tight text-white">DeepGuard</span>
              </div>
              <div className="flex gap-4">
                <Link to="/" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
                  Detector
                </Link>
                <Link to="/dashboard" className="text-sm font-medium flex items-center gap-1 text-gray-300 hover:text-white transition-colors">
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </Link>
              </div>
            </div>
          </div>
        </nav>
      )}

      {/* Main Content */}
      <main className={isLogin ? '' : 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'}>
        <Routes>
          <Route path="/" element={<RequireEntry><Home /></RequireEntry>} />
          <Route path="/dashboard" element={<RequireEntry><Dashboard /></RequireEntry>} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}

export default App;
