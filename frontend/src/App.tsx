import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import SubmitPage from './pages/SubmitPage'
import DashboardPage from './pages/DashboardPage'
import StatsPage from './pages/StatsPage'
import ProvidersPage from './pages/ProvidersPage'


export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <NavLink to="/">Submit</NavLink>
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/stats">Stats</NavLink>
        <NavLink to="/providers">Providers</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<SubmitPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/providers" element={<ProvidersPage />} />
      </Routes>
    </BrowserRouter>
  )
}