import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Tickets from './pages/Tickets';
import AdminPanel from './pages/AdminPanel'; // <--- IMPORTACIÓN DEL NUEVO PANEL
import Verificacion from './pages/Verificacion'; // Centro de verificación para la demostración
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/tickets" element={<Tickets />} />
        
        {/* NUEVA RUTA PARA EL ADMIN */}
        <Route path="/admin" element={<AdminPanel />} />

        {/* Centro de verificación: prueba visual de cada requisito del curso (solo staff) */}
        <Route path="/verificacion" element={<Verificacion />} />
      </Routes>
    </Router>
  );
}

export default App;