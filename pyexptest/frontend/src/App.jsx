import { Routes, Route, NavLink } from 'react-router-dom'
import SampleSizeCalculator from './pages/SampleSizeCalculator'
import ConfidenceIntervalCalculator from './pages/PowerCalculator'
import SignificanceCalculator from './pages/SignificanceCalculator'

function App() {
  return (
    <div className="app-container">
      <nav className="sidebar">
        <div className="sidebar-header">
          <div className="logo">pyexptest</div>
          <div className="logo-subtitle">A/B Testing Made Simple</div>
        </div>
        
        <div className="nav-section">
          <div className="nav-section-title">Calculators</div>
          <NavLink 
            to="/" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            end
          >
            <span className="nav-icon">📐</span>
            Sample Size
          </NavLink>
          <NavLink 
            to="/analyze" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📊</span>
            Analyze Results
          </NavLink>
          <NavLink 
            to="/confidence" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📏</span>
            Confidence Interval
          </NavLink>
        </div>
        
        <div className="nav-section" style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          <div className="nav-section-title">Resources</div>
          <a 
            href="https://github.com/pyexptest/pyexptest" 
            target="_blank" 
            rel="noopener noreferrer"
            className="nav-link"
          >
            <span className="nav-icon">📦</span>
            GitHub
          </a>
          <a 
            href="https://pypi.org/project/pyexptest" 
            target="_blank" 
            rel="noopener noreferrer"
            className="nav-link"
          >
            <span className="nav-icon">🐍</span>
            PyPI
          </a>
        </div>
      </nav>
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<SampleSizeCalculator />} />
          <Route path="/analyze" element={<SignificanceCalculator />} />
          <Route path="/confidence" element={<ConfidenceIntervalCalculator />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
