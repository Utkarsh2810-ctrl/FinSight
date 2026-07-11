import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './styles.css';
import AuthPage from './pages/AuthPage';
import QaPage from './pages/QaPage';
import ForecastPage from './pages/ForecastPage';
import EvaluationPage from './pages/EvaluationPage';
import Navbar from './components/Navbar';

const isAuthenticated = () => Boolean(localStorage.getItem('finsight_token')?.trim());

const ProtectedLayout = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return (
    <>
      <Navbar />
      {children}
    </>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={isAuthenticated() ? <Navigate to="/qa" replace /> : <AuthPage />} />
        <Route path="/login" element={isAuthenticated() ? <Navigate to="/qa" replace /> : <AuthPage />} />
        <Route path="/register" element={isAuthenticated() ? <Navigate to="/qa" replace /> : <AuthPage />} />
        <Route path="/qa" element={<ProtectedLayout><QaPage /></ProtectedLayout>} />
        <Route path="/forecast" element={<ProtectedLayout><ForecastPage /></ProtectedLayout>} />
        <Route path="/evaluate" element={<ProtectedLayout><EvaluationPage /></ProtectedLayout>} />
      </Routes>
    </BrowserRouter>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
