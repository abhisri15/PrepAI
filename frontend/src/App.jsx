import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Header from './components/Header'
import Ask from './pages/Ask'
import AtsScore from './pages/AtsScore'
import GapAnalysis from './pages/GapAnalysis'
import Prep from './pages/Prep'

export default function App() {
  const [health, setHealth] = useState({ status: 'unknown' })

  const navClass = ({ isActive }) =>
    `px-4 py-2 rounded-lg transition-colors text-sm ${
      isActive ? 'bg-amber-500/20 text-amber-400' : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
    }`

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Header health={health} setHealth={setHealth} />
        <nav className="flex gap-2 p-4 border-b border-slate-800 bg-slate-900/50">
          <NavLink to="/" className={navClass} end>Prep Guide</NavLink>
          <NavLink to="/ask" className={navClass}>Ask</NavLink>
          <NavLink to="/ats" className={navClass}>ATS Score</NavLink>
          <NavLink to="/gaps" className={navClass}>Gap Analysis</NavLink>
        </nav>
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<Prep />} />
            <Route path="/ask" element={<Ask />} />
            <Route path="/ats" element={<AtsScore />} />
            <Route path="/gaps" element={<GapAnalysis />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
