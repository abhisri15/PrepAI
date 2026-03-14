import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Header from './components/Header'
import Ask from './pages/Ask'
import Upload from './pages/Upload'
import Prep from './pages/Prep'
import Demo from './pages/Demo'

export default function App() {
  const [health, setHealth] = useState({ status: 'unknown' })

  const navClass = ({ isActive }) =>
    `px-4 py-2 rounded-lg transition-colors ${
      isActive ? 'bg-amber-500/20 text-amber-400' : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
    }`

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Header health={health} setHealth={setHealth} />
        <nav className="flex gap-2 p-4 border-b border-slate-800 bg-slate-900/50">
          <NavLink to="/" className={navClass} end>Ask</NavLink>
          <NavLink to="/upload" className={navClass}>Upload</NavLink>
          <NavLink to="/prep" className={navClass}>Prep Guide</NavLink>
          <NavLink to="/demo" className={navClass}>Demo</NavLink>
        </nav>
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<Ask />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/prep" element={<Prep />} />
            <Route path="/demo" element={<Demo />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
