
import { useCallback, useEffect, useState } from 'react'
import {
  Activity,
  AlertCircle,
  ArrowDown,
  ArrowUp,
  CandlestickChart,
  CheckCircle2,
  Clock,
  RefreshCw,
  TrendingUp,
} from 'lucide-react'
import { BacktestReportCard } from './AIAssistant'
import './BacktestHistory.css'

const API_URL = ''

function formatDate(value) {
  if (!value) return '—'

  return new Date(value).toLocaleString()
}

function getStrategy(config = {}) {
  if (config.strategy_type === 'sma_crossover') return 'SMA Crossover'
  if (config.strategy_type === 'condition_based') return 'Condition Based'

  return config.strategy_type || 'Unknown strategy'
}

function BacktestHistory({ view = 'backtesting' }) {
  const [jobs, setJobs] = useState([])
  const [selectedJob, setSelectedJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/backtests`, {
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Unable to load backtest history.')
      }

      const data = await response.json()
      const history = data.jobs || []

      setJobs(history)

      setSelectedJob((previous) => {
        if (!previous) return null

        return history.find(
          (job) => job.run_id === previous.run_id
        ) || null
      })

      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory()

    const interval = setInterval(fetchHistory, 3000)

    return () => clearInterval(interval)
  }, [fetchHistory])

  const completed = jobs.filter(
    (job) => job.status === 'completed'
  )

  const running = jobs.filter(
    (job) => ['queued', 'running'].includes(job.status)
  )

  const failed = jobs.filter(
    (job) => job.status === 'failed'
  )

  const isReports = view === 'reports'

  const displayedJobs = isReports ? completed : jobs

  return (
    <div className="dashboard backtest-history">

      <section className="page-heading">
        <div>
          <div className="eyebrow">
            TRADING SIMULATION WORKSPACE
          </div>

          <h1>{isReports ? 'Backtest Reports' : 'Backtesting'}</h1>

          <p>
            {isReports
              ? 'Review historical strategy performance and detailed reports.'
              : 'Monitor and review your historical strategy executions.'}
          </p>
        </div>

        <button
          className="history-refresh"
          onClick={fetchHistory}
          type="button"
          disabled={loading}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </section>

      <section className="stats-grid history-stats">

        <article className="stat-card">
          <div className="stat-top">
            <span>Total backtests</span>
            <Activity size={18} />
          </div>
          <div className="stat-value">{jobs.length}</div>
          <div className="stat-foot">All execution runs</div>
        </article>

        <article className="stat-card">
          <div className="stat-top">
            <span>Completed</span>
            <CheckCircle2 size={18} />
          </div>
          <div className="stat-value history-positive">
            {completed.length}
          </div>
          <div className="stat-foot">Successful executions</div>
        </article>

        <article className="stat-card">
          <div className="stat-top">
            <span>Running</span>
            <Clock size={18} />
          </div>
          <div className="stat-value">{running.length}</div>
          <div className="stat-foot">Queued or processing</div>
        </article>

        <article className="stat-card">
          <div className="stat-top">
            <span>Failed</span>
            <AlertCircle size={18} />
          </div>
          <div className="stat-value history-negative">
            {failed.length}
          </div>
          <div className="stat-foot">Execution errors</div>
        </article>

      </section>

      {error && (
        <div className="history-error">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <section className="panel history-panel">
        <div className="panel-heading">
          <div>
            <h3>{isReports ? 'Completed reports' : 'Execution history'}</h3>
            <p>
              {displayedJobs.length} runs available
            </p>
          </div>
        </div>

        {loading && jobs.length === 0 ? (
          <div className="history-empty">
            Loading backtest history...
          </div>
        ) : displayedJobs.length === 0 ? (
          <div className="history-empty">
            <CandlestickChart size={32} />
            <strong>No backtests found</strong>
            <span>
              Run a strategy from AI Assistant to see results here.
            </span>
          </div>
        ) : (
          <div className="history-table-wrap">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Asset / Strategy</th>
                  <th>Period</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Net P&L</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {displayedJobs.map((job) => {
                  const config = job.config || {}
                  const pnl = Number(job.results?.total_pnl)
                  const isCompleted = job.status === 'completed'

                  return (
                    <tr key={job.run_id}>
                      <td>
                        <strong>
                          {config.asset || config.symbol || 'BTCUSDT'}
                        </strong>
                        <span>{getStrategy(config)}</span>
                      </td>

                      <td>
                        <strong>{config.timeframe || '—'}</strong>
                        <span>
                          {config.start_date || '—'} – {config.end_date || '—'}
                        </span>
                      </td>

                      <td>{formatDate(job.created_at)}</td>

                      <td>
                        <span className={`history-status ${job.status}`}>
                          {job.status}
                        </span>
                      </td>

                      <td>
                        {isCompleted ? (
                          <strong className={
                            pnl >= 0
                              ? 'history-positive'
                              : 'history-negative'
                          }>
                            {pnl >= 0 ? '+' : ''}
                            {pnl.toFixed(2)} USDT
                          </strong>
                        ) : '—'}
                      </td>

                      <td>
                        <button
                          type="button"
                          className="history-view-button"
                          onClick={() => setSelectedJob(job)}
                          disabled={!isCompleted}
                        >
                          View report
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedJob && (
        <section className="history-selected-report">
          <div className="history-report-heading">
            <div>
              <span className="eyebrow">SELECTED EXECUTION</span>
              <h2>Detailed backtest report</h2>
              <p>Run ID: {selectedJob.run_id}</p>
            </div>

            <button
              type="button"
              className="history-close-button"
              onClick={() => setSelectedJob(null)}
            >
              Close report
            </button>
          </div>

          <BacktestReportCard job={selectedJob} />
        </section>
      )}

      <div className="history-disclaimer">
        <TrendingUp size={14} />
        Historical simulation only. No live orders were placed.
      </div>

    </div>
  )
}

export default BacktestHistory
