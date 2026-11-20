
import { useCallback, useEffect, useState } from 'react'
import AIAssistant from './AIAssistant'
import LandingPage from './LandingPage'
import PositionCalculator from './PositionCalculator'
import BacktestHistory from './BacktestHistory'
import {
  Activity,
  ArrowUpRight,
  Bell,
  Bot,
  CandlestickChart,
  ChevronDown,
  CircleHelp,
  Clock3,
  House,
  LayoutDashboard,
  LineChart,
  Search,
  Settings,
  ShieldCheck,
  Wallet,
  Zap,
  LogOut,
} from 'lucide-react'
import './App.css'

const navigation = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'AI Assistant', icon: Bot },
  { label: 'Position Calculator', icon: Wallet },
  { label: 'Strategy Lab', icon: Zap },
  { label: 'Backtesting', icon: CandlestickChart },
  { label: 'Reports', icon: LineChart },
]

const watchlist = [
  { symbol: 'BTC', name: 'Bitcoin', price: '$91,284.50', change: '+2.41%', positive: true, points: '0,22 12,18 24,21 36,10 48,15 60,5 72,11 84,2' },
  { symbol: 'ETH', name: 'Ethereum', price: '$3,124.80', change: '+1.82%', positive: true, points: '0,20 12,14 24,18 36,8 48,13 60,7 72,10 84,3' },
  { symbol: 'SOL', name: 'Solana', price: '$142.65', change: '-0.64%', positive: false, points: '0,5 12,9 24,6 36,15 48,10 60,18 72,14 84,22' },
  { symbol: 'BNB', name: 'BNB', price: '$612.30', change: '+0.95%', positive: true, points: '0,19 12,13 24,17 36,11 48,14 60,5 72,9 84,3' },
]

const activities = [
  { pair: 'BTC/USDT', type: 'Long position', detail: 'SMA Crossover · 1H', result: '+$124.80', positive: true, time: 'Today, 10:42 AM' },
  { pair: 'ETH/USDT', type: 'Short position', detail: 'Manual simulation · 4H', result: '+$68.20', positive: true, time: 'Today, 09:18 AM' },
  { pair: 'SOL/USDT', type: 'Long position', detail: 'SMA Crossover · 1H', result: '-$32.50', positive: false, time: 'Yesterday, 06:35 PM' },
]


function App() {
  const [showLanding, setShowLanding] = useState(true)
  const [activeNav, setActiveNav] = useState('Dashboard')
  const [timeframe, setTimeframe] = useState('1D')
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      try {
        const response = await fetch('/api/auth/me', {
          credentials: 'include',
        })

        if (!response.ok) return

        const data = await response.json()

        if (!cancelled) {
          setUser(data.user)
        }
      } catch (error) {
        console.error('Session restoration failed:', error)
      } finally {
        if (!cancelled) {
          setAuthLoading(false)
        }
      }
    }

    restoreSession()

    return () => {
      cancelled = true
    }
  }, [])

  const handleLoginSuccess = useCallback((loggedInUser) => {
    setUser(loggedInUser)
    setShowLanding(false)
  }, [])

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Logout failed.')
      }

      setUser(null)
      setShowLanding(true)
      setActiveNav('Dashboard')
    } catch (error) {
      console.error(error)
      alert('Unable to sign out. Please try again.')
    }
  }

  const handleLaunch = () => {
    if (user) {
      setShowLanding(false)
    } else {
      document.getElementById('google-signin')?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }

  if (authLoading) {
    return (
      <div className="auth-loading-screen">
        <h2>TradeSim</h2>
        <p>Restoring your session...</p>
      </div>
    )
  }

  if (!user || showLanding) {
    return (
      <LandingPage
        onLaunch={handleLaunch}
        user={user}
        onLoginSuccess={handleLoginSuccess}
      />
    )
  }


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Activity size={21} />
          </div>
          <div>
            <span className="brand-name">TradeSim</span>
            <span className="brand-caption">TRADING INTELLIGENCE</span>
          </div>
        </div>

        {/* Home navigation */}
        <button
          className="nav-item home-nav-item"
          type="button"
          onClick={() => {
            setActiveNav('Dashboard')
            setShowLanding(true)
          }}
        >
          <House size={18} strokeWidth={1.8} />
          <span>Home</span>
        </button>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="nav-list">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              className={`nav-item ${activeNav === label ? 'active' : ''}`}
              key={label}
              onClick={() => setActiveNav(label)}
              type="button"
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>

              {label === 'Strategy Lab' && (
                <span className="nav-soon">Soon</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot" />
            <div>
              <strong>Simulation engine</strong>
              <span>Frontend preview</span>
            </div>
          </div>

          <button className="nav-item utility-item" type="button">
            <Settings size={18} />
            Settings
          </button>

          <button className="nav-item utility-item" type="button">
            <CircleHelp size={18} />
            Help & support
          </button>

          
<div className="user-profile">
  {user.picture ? (
    <img
      className="avatar"
      src={user.picture}
      alt="Profile"
    />
  ) : (
    <div className="avatar">
      {(user.name || user.email || 'U').charAt(0).toUpperCase()}
    </div>
  )}

  <div className="user-details">
    <strong>{user.name}</strong>
    <span>{user.email}</span>
  </div>

  <button
    className="profile-logout"
    type="button"
    onClick={handleLogout}
    title="Sign out"
    aria-label="Sign out"
  >
    <LogOut size={17} />
  </button>
</div>

        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-divider">/</span>
            <strong>{activeNav}</strong>
          </div>

          <div className="topbar-actions">
            <div className="environment-tag">
              <span />
              SIMULATION MODE
            </div>

            <button
              className="icon-button"
              type="button"
              aria-label="Search"
            >
              <Search size={18} />
            </button>

            <button
              className="icon-button notification-button"
              type="button"
              aria-label="Notifications"
            >
              <Bell size={18} />
              <i />
            </button>

            {user.picture ? (
  <img
    className="top-avatar"
    src={user.picture}
    alt="Profile"
  />
) : (
  <div className="top-avatar">
    {(user.name || user.email || 'U').charAt(0).toUpperCase()}
  </div>
)}
          </div>
        </header>

        {activeNav === 'AI Assistant' ? (
          <AIAssistant key={user.id} user={user} />
        ) : activeNav === 'Position Calculator' ? (
          <PositionCalculator />
        ) : activeNav === 'Backtesting' ? (
          <BacktestHistory view="backtesting" />
        ) : activeNav === 'Reports' ? (
          <BacktestHistory view="reports" />
        ) : (
          <div className="dashboard">
            <section className="page-heading">
              <div>
                <div className="eyebrow">
                  MONDAY, NOVEMBER 16, 2026
                </div>
                <h1>Market overview</h1>
                <p>
                  Monitor your simulated portfolio and market activity.
                </p>
              </div>

              <div className="heading-actions">
                <span className="preview-label">SAMPLE DATA</span>
                <button className="date-button" type="button">
                  <Clock3 size={16} />
                  Last 30 days
                  <ChevronDown size={15} />
                </button>
              </div>
            </section>

            <section className="stats-grid">
              <article className="stat-card">
                <div className="stat-top">
                  <span>Portfolio balance</span>
                  <div className="stat-icon">
                    <Wallet size={18} />
                  </div>
                </div>
                <div className="stat-value">$20,000.00</div>
                <div className="stat-foot">
                  <span className="neutral-change">Starting capital</span>
                  <span>USDT</span>
                </div>
              </article>

              <article className="stat-card">
                <div className="stat-top">
                  <span>Total simulated P&L</span>
                  <div className="stat-icon green">
                    <ArrowUpRight size={18} />
                  </div>
                </div>
                <div className="stat-value positive-text">
                  +$1,284.50
                </div>
                <div className="stat-foot">
                  <span className="positive-change">
                    <ArrowUpRight size={14} /> +6.42%
                  </span>
                  <span>Sample return</span>
                </div>
              </article>

              <article className="stat-card">
                <div className="stat-top">
                  <span>Active positions</span>
                  <div className="stat-icon blue">
                    <Activity size={18} />
                  </div>
                </div>
                <div className="stat-value">03</div>
                <div className="stat-foot">
                  <span className="neutral-change">Across 2 assets</span>
                  <span>Simulated</span>
                </div>
              </article>

              <article className="stat-card">
                <div className="stat-top">
                  <span>Risk exposure</span>
                  <div className="stat-icon orange">
                    <ShieldCheck size={18} />
                  </div>
                </div>
                <div className="stat-value">2.0%</div>
                <div className="stat-foot">
                  <span className="positive-change">
                    Within risk limit
                  </span>
                  <span>Per trade</span>
                </div>
              </article>
            </section>

            <section className="content-grid">
              <article className="panel chart-panel">
                <div className="panel-heading">
                  <div>
                    <div className="panel-title">
                      Portfolio performance
                    </div>
                    <div className="chart-balance">
                      $21,284.50
                      <span className="positive-change">
                        <ArrowUpRight size={14} /> 6.42%
                      </span>
                    </div>
                    <div className="muted-caption">
                      Simulated portfolio value
                    </div>
                  </div>

                  <div className="timeframe-switch">
                    {['1D', '1W', '1M', '3M', '1Y', 'ALL'].map((item) => (
                      <button
                        type="button"
                        key={item}
                        className={timeframe === item ? 'selected' : ''}
                        onClick={() => setTimeframe(item)}
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="chart-wrap">
                  <div className="chart-y-labels">
                    <span>$22k</span>
                    <span>$21k</span>
                    <span>$20k</span>
                    <span>$19k</span>
                    <span>$18k</span>
                  </div>

                  <div className="chart-area">
                    <div className="chart-grid-lines">
                      <span />
                      <span />
                      <span />
                      <span />
                      <span />
                    </div>

                    <svg
                      className="performance-chart"
                      viewBox="0 0 760 230"
                      preserveAspectRatio="none"
                      role="img"
                      aria-label="Illustrative portfolio performance line chart"
                    >
                      <defs>
                        <linearGradient
                          id="chartFill"
                          x1="0"
                          x2="0"
                          y1="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#27c99a"
                            stopOpacity=".22"
                          />
                          <stop
                            offset="100%"
                            stopColor="#27c99a"
                            stopOpacity="0"
                          />
                        </linearGradient>
                      </defs>

                      <path
                        d="M0 185 C35 170 45 180 75 155 S120 165 150 137 S195 148 225 125 S270 143 300 108 S345 120 375 100 S420 116 450 82 S495 98 525 75 S570 89 600 58 S645 73 675 48 S720 55 760 20 L760 230 L0 230 Z"
                        fill="url(#chartFill)"
                      />

                      <path
                        d="M0 185 C35 170 45 180 75 155 S120 165 150 137 S195 148 225 125 S270 143 300 108 S345 120 375 100 S420 116 450 82 S495 98 525 75 S570 89 600 58 S645 73 675 48 S720 55 760 20"
                        fill="none"
                        stroke="#27c99a"
                        strokeWidth="2.8"
                        vectorEffect="non-scaling-stroke"
                      />

                      <circle cx="760" cy="20" r="5" fill="#27c99a" />
                    </svg>

                    <div className="chart-x-labels">
                      <span>Oct 18</span>
                      <span>Oct 24</span>
                      <span>Oct 30</span>
                      <span>Nov 05</span>
                      <span>Nov 11</span>
                      <span>Nov 16</span>
                    </div>
                  </div>
                </div>

                <div className="chart-footer">
                  <span>
                    <i className="legend-dot" />
                    Portfolio value
                  </span>
                  <span>
                    Illustrative chart · Not connected to live data
                  </span>
                </div>
              </article>

              <article className="panel watchlist-panel">
                <div className="panel-heading">
                  <div>
                    <div className="panel-title">Market watchlist</div>
                    <div className="muted-caption">Tracked assets</div>
                  </div>
                  <button className="text-button" type="button">
                    View all
                  </button>
                </div>

                <div className="watchlist">
                  {watchlist.map((coin) => (
                    <div className="coin-row" key={coin.symbol}>
                      <div className="coin-identity">
                        <div className={`coin-icon ${coin.symbol.toLowerCase()}`}>
                          {coin.symbol.slice(0, 1)}
                        </div>
                        <div>
                          <strong>{coin.symbol}</strong>
                          <span>{coin.name}</span>
                        </div>
                      </div>

                      <svg
                        className={`sparkline ${
                          coin.positive
                            ? 'spark-positive'
                            : 'spark-negative'
                        }`}
                        viewBox="0 0 84 26"
                        preserveAspectRatio="none"
                        aria-hidden="true"
                      >
                        <polyline
                          points={coin.points}
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>

                      <div className="coin-price">
                        <strong>{coin.price}</strong>
                        <span
                          className={
                            coin.positive
                              ? 'positive-text'
                              : 'negative-text'
                          }
                        >
                          {coin.change}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="watchlist-note">
                  <span className="status-dot" />
                  Sample market values
                </div>
              </article>
            </section>

            <section className="panel activity-panel">
              <div className="panel-heading">
                <div>
                  <div className="panel-title">Recent activity</div>
                  <div className="muted-caption">
                    Your latest simulated trades
                  </div>
                </div>

                <button className="text-button" type="button">
                  View history <ArrowUpRight size={14} />
                </button>
              </div>

              <div className="activity-table-wrap">
                <table className="activity-table">
                  <thead>
                    <tr>
                      <th>MARKET</th>
                      <th>TYPE</th>
                      <th>STRATEGY / SOURCE</th>
                      <th>RESULT</th>
                      <th>TIME</th>
                    </tr>
                  </thead>

                  <tbody>
                    {activities.map((trade, index) => (
                      <tr key={`${trade.pair}-${index}`}>
                        <td>
                          <strong>{trade.pair}</strong>
                        </td>
                        <td>
                          <span
                            className={`trade-type ${
                              trade.type.startsWith('Long')
                                ? 'long'
                                : 'short'
                            }`}
                          >
                            {trade.type}
                          </span>
                        </td>
                        <td className="muted-cell">{trade.detail}</td>
                        <td
                          className={
                            trade.positive
                              ? 'positive-text'
                              : 'negative-text'
                          }
                        >
                          {trade.result}
                        </td>
                        <td className="muted-cell">{trade.time}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <footer className="dashboard-footer">
              <span>
                TradeSim
                <span className="footer-separator">·</span>
                Built for disciplined simulation
              </span>

              <span>
                <span className="status-dot" />
                Prototype environment
                <span className="footer-separator">·</span>
                No live orders
              </span>
            </footer>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
