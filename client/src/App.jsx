import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import "./App.css";
import BoardDetails from "./pages/BoardDetails";
import ProtectedRoute from "./components/ProtectedRoute";
import Community from "./pages/Community";

function App() {
  return (
    <div className="app-shell">
      <Navbar />

      <main className="app-container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/community"
            element={
              <ProtectedRoute>
                <Community />
              </ProtectedRoute>
            }
          />
          <Route
              path="/boards/:boardId"
              element={
                <ProtectedRoute>
                  <BoardDetails />
                </ProtectedRoute>
              }
            />
        </Routes>
      </main>

      <footer className="site-footer" aria-label="Site footer">
        <p className="site-footer-text">
          Copyright {"\u00A9"} 2026 James Mounts. All rights reserved.
        </p>
      </footer>
    </div>
  );
}

export default App;