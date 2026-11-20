
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Bot,
  CandlestickChart,
  ChartNoAxesCombined,
  ShieldCheck,
  Wallet,
  Zap,
  ChevronRight,
} from 'lucide-react'
import './LandingPage.css'
import GoogleSignInButton from './GoogleSignInButton'

const features = [
  {
    icon: Bot,
    number: '01',
    title: 'AI Strategy Builder',
    description:
      'Describe your trading idea in natural language. TradeSim AI interprets your instructions and prepares a structured strategy.',
  },
  {
    icon: CandlestickChart,
    number: '02',
    title: 'Historical Backtesting',
    description:
      'Test executable strategies against historical market data and understand how they would have performed.',
  },
  {
    icon: Wallet,
    number: '03',
    title: 'Position Calculator',
    description:
      'Calculate position sizes using capital, entry price, stop loss, risk percentage and market constraints.',
  },
  {
    icon: ShieldCheck,
    number: '04',
    title: 'Risk Management',
    description:
      'Understand potential losses, margin requirements, fees and exposure before making a simulated decision.',
  },
  {
    icon: ChartNoAxesCombined,
    number: '05',
    title: 'Performance Reports',
    description:
      'Review backtest results, equity curves, drawdown, win rate and other performance metrics.',
  },
  {
    icon: Zap,
    number: '06',
    title: 'Strategy Analysis',
    description:
      'Turn trading concepts into testable rules and identify which strategy components are supported.',
  },
]

function LandingPage({ onLaunch, user, onLoginSuccess }) {
  return (
    <div className="landing-page">
      <div className="landing-glow landing-glow-one" />
      <div className="landing-glow landing-glow-two" />

      <header className="landing-navbar">
        <a className="landing-brand" href="#home">
          <span className="landing-brand-icon">
            <Activity size={21} />
          </span>
          <span>
            <strong>TradeSim</strong>
            <small>TRADING INTELLIGENCE</small>
          </span>
        </a>

        <nav className="landing-nav">
          <a href="#features">Features</a>
          <a href="#workflow">How it works</a>
          <a href="#about">About</a>
        </nav>

        <button
          className="landing-nav-cta"
          onClick={onLaunch}
          type="button"
        >
          Launch app <ArrowUpRight size={16} />
        </button>
      </header>

      <main id="home">
        <section className="landing-hero">
          <div className="landing-hero-copy">
            <div className="landing-status">
              <span className="landing-status-dot" />
              AI-POWERED TRADING SIMULATION
            </div>

            <h1>
              Test your strategy.
              <br />
              <span>Understand your risk.</span>
              <br />
              Trade with clarity.
            </h1>

            <p className="landing-hero-description">
              An intelligent trading simulation platform that turns
              trading ideas into structured strategies, calculates risk,
              and tests performance against historical market data.
            </p>

            <div className="landing-hero-actions">
              <button
                className="landing-primary-button"
                onClick={onLaunch}
                type="button"
              >
                Launch TradeSim <ArrowRight size={18} />
              </button>

              <a className="landing-secondary-button" href="#features">
                Explore features <ChevronRight size={17} />
              </a>
            </div>

<div className="landing-auth-area" id="google-signin">
  {user ? (
    <p className="landing-auth-message">
      Signed in as <strong>{user.name}</strong>
    </p>
  ) : (
    <>
      <p className="landing-auth-message">
        Sign in to access your personal trading workspace
      </p>
      <GoogleSignInButton onSuccess={onLoginSuccess} />
    </>
  )}
</div>

            <div className="landing-trust-line">
              <ShieldCheck size={16} />
              <span>Simulation only. No live trading orders.</span>
            </div>
          </div>

          <div className="landing-visual">
            <div className="visual-topbar">
              <div className="visual-window-dots">
                <i />
                <i />
                <i />
              </div>
              <span>TRADESIM INTELLIGENCE</span>
              <span className="visual-live-indicator">SYSTEM READY</span>
            </div>

            <div className="visual-content">
              <div className="visual-greeting">
                <div className="visual-ai-icon">
                  <Bot size={20} />
                </div>
                <div>
                  <strong>TradeSim AI</strong>
                  <span>Strategy assistant</span>
                </div>
              </div>

              <div className="visual-user-message">
                Backtest a BTC moving average crossover strategy
                using the 10 and 30 period SMA.
              </div>

              <div className="visual-ai-response">
                <div className="visual-response-heading">
                  <span className="visual-response-dot" />
                  Strategy interpreted
                </div>
                <div className="visual-strategy-row">
                  <span>Market</span>
                  <strong>BTC / USDT</strong>
                </div>
                <div className="visual-strategy-row">
                  <span>Strategy</span>
                  <strong>SMA Crossover</strong>
                </div>
                <div className="visual-strategy-row">
                  <span>Fast / Slow SMA</span>
                  <strong>10 / 30</strong>
                </div>
                <div className="visual-strategy-row">
                  <span>Execution</span>
                  <strong className="visual-supported">Ready to validate</strong>
                </div>
              </div>

              <div className="visual-bottom">
                <span>Describe a strategy...</span>
                <div><ArrowUpRight size={17} /></div>
              </div>
            </div>

            <div className="visual-decoration visual-decoration-one">
              <Activity size={17} />
              <span>Risk-aware calculations</span>
            </div>
            <div className="visual-decoration visual-decoration-two">
              <ChartNoAxesCombined size={17} />
              <span>Historical analysis</span>
            </div>
          </div>
        </section>

        <section className="landing-metrics">
          <div>
            <strong>AI</strong>
            <span>Natural language strategy interpretation</span>
          </div>
          <div>
            <strong>Python</strong>
            <span>Calculation and backtesting engine</span>
          </div>
          <div>
            <strong>Risk-first</strong>
            <span>Built around disciplined simulation</span>
          </div>
        </section>

        <section className="landing-features" id="features">
          <div className="landing-section-heading">
            <span className="landing-section-label">THE PLATFORM</span>
            <h2>Everything starts with a better decision.</h2>
            <p>
              Tools to interpret, calculate, test and analyse trading
              strategies in one environment.
            </p>
          </div>

          <div className="landing-feature-grid">
            {features.map((feature) => {
              const Icon = feature.icon

              return (
                <article className="landing-feature-card" key={feature.number}>
                  <div className="landing-feature-top">
                    <div className="landing-feature-icon">
                      <Icon size={21} />
                    </div>
                    <span>{feature.number}</span>
                  </div>
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                </article>
              )
            })}
          </div>
        </section>

        <section className="landing-workflow" id="workflow">
          <div className="landing-section-heading">
            <span className="landing-section-label">THE WORKFLOW</span>
            <h2>From idea to evidence.</h2>
            <p>A structured process for evaluating a trading idea.</p>
          </div>

          <div className="landing-steps">
            <div className="landing-step">
              <span>01</span>
              <h3>Describe</h3>
              <p>Explain your strategy to the AI assistant.</p>
            </div>
            <div className="landing-step-arrow"><ArrowRight size={20} /></div>
            <div className="landing-step">
              <span>02</span>
              <h3>Validate</h3>
              <p>Convert the idea into supported strategy rules.</p>
            </div>
            <div className="landing-step-arrow"><ArrowRight size={20} /></div>
            <div className="landing-step">
              <span>03</span>
              <h3>Simulate</h3>
              <p>Run calculations and historical backtests.</p>
            </div>
            <div className="landing-step-arrow"><ArrowRight size={20} /></div>
            <div className="landing-step">
              <span>04</span>
              <h3>Analyse</h3>
              <p>Review performance and understand risk.</p>
            </div>
          </div>
        </section>

        <section className="landing-final-cta" id="about">
          <div>
            <span className="landing-section-label">YOUR SIMULATION WORKSPACE</span>
            <h2>Ideas deserve to be tested.</h2>
            <p>
              Explore your trading strategies in a controlled simulation
              environment.
            </p>
          </div>
          <button
            className="landing-primary-button"
            onClick={onLaunch}
            type="button"
          >
            Enter TradeSim <ArrowRight size={18} />
          </button>
        </section>
      </main>

      <footer className="landing-footer">
        <a className="landing-brand" href="#home">
          <span className="landing-brand-icon">
            <Activity size={19} />
          </span>
          <span>
            <strong>TradeSim</strong>
            <small>TRADING INTELLIGENCE</small>
          </span>
        </a>
        <span>Built for disciplined simulation.</span>
        <span className="landing-footer-disclaimer">
          No live trading orders.
        </span>
      </footer>
    </div>
  )
}

export default LandingPage
