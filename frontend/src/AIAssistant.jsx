
import { useEffect, useRef, useState } from 'react'
import {
  Bot,
  Send,
  Plus,
  Sparkles,
  User,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  TrendingUp,
  Activity,
  Info,
} from 'lucide-react'
import './AIAssistant.css'

const API_URL = 'http://127.0.0.1:8000'

const initialMessage = {
  role: 'assistant',
  text: "Hello! I'm TradeSim AI. Describe a trading idea, ask me to calculate a position size, or request a historical backtest. I'll interpret your instructions and use the Python engine for calculations.",
}

function formatNumber(value, maximumFractionDigits = 2) {
  if (value === null || value === undefined) return '—'

  const number = Number(value)

  if (!Number.isFinite(number)) return String(value)

  return number.toLocaleString('en-US', {
    maximumFractionDigits,
  })
}

// POSITION SIZING RESULT

function ResultCard({ calculation }) {
  if (!calculation) return null

  const successful = calculation.status === 'success'

  return (
    <div className="ai-result-card">
      <div className="ai-result-heading">
        <div>
          <span className="ai-result-eyebrow">PYTHON CALCULATION</span>
          <h3>Position sizing result</h3>
        </div>

        {successful ? (
          <span className="ai-result-status success">
            <CheckCircle2 size={14} /> Successful
          </span>
        ) : (
          <span className="ai-result-status warning">
            <AlertCircle size={14} /> Not completed
          </span>
        )}
      </div>

      {successful ? (
        <>
          <div className="ai-result-quantity">
            <strong>{formatNumber(calculation.position_quantity, 8)}</strong>
            <span>{calculation.symbol} quantity</span>
          </div>

          <div className="ai-result-grid">
            <div>
              <span>Position value</span>
              <strong>
                {formatNumber(calculation.position_value)} {calculation.quote_asset}
              </strong>
            </div>

            <div>
              <span>Risk budget</span>
              <strong>
                {formatNumber(calculation.risk_budget)} {calculation.quote_asset}
              </strong>
            </div>

            <div>
              <span>Estimated total loss</span>
              <strong className="ai-loss-value">
                {formatNumber(calculation.estimated_total_loss)} {calculation.quote_asset}
              </strong>
            </div>

            <div>
              <span>Margin required</span>
              <strong>
                {formatNumber(calculation.margin_required_estimate)} {calculation.quote_asset}
              </strong>
            </div>

            <div>
              <span>Estimated fees</span>
              <strong>
                {formatNumber(calculation.estimated_fees)} {calculation.quote_asset}
              </strong>
            </div>

            <div>
              <span>Leverage</span>
              <strong>{formatNumber(calculation.leverage)}x</strong>
            </div>
          </div>

          <div className="ai-validation-list">
            {[
              ['Risk budget respected', calculation.risk_budget_respected],
              ['Capital constraint', calculation.capital_constraint_respected],
              ['Quantity filter', calculation.quantity_filter_respected],
              ['Notional filter', calculation.notional_filter_respected],
            ].map(([label, passed]) => (
              <div className="ai-validation-row" key={label}>
                <span>{label}</span>
                <span className={passed ? 'passed' : 'failed'}>
                  {passed ? 'Passed' : 'Not passed'}
                </span>
              </div>
            ))}
          </div>

          {calculation.liquidation_note && (
            <div className="ai-result-note">
              <AlertCircle size={15} />
              <span>{calculation.liquidation_note}</span>
            </div>
          )}

          {calculation.liquidation_estimation_status === 'not_loaded' && (
            <div className="ai-result-note">
              <AlertCircle size={15} />
              <span>
                Account-specific liquidation estimation is unavailable.
                This result does not include a verified liquidation price.
              </span>
            </div>
          )}

          <div className="ai-result-disclaimer">
            <ShieldCheck size={14} />
            Simulation only. No orders have been sent to Binance.
          </div>
        </>
      ) : (
        <p className="ai-inline-error">
          {calculation.error || 'The calculation did not complete.'}
        </p>
      )}
    </div>
  )
}

// BACKTEST CONFIGURATION

function BacktestPreparationCard({ config, defaults, onConfirm, loading }) {
  const fields = [
    ['Asset', config.asset],
    ['Market', config.market_type],
    ['Timeframe', config.timeframe],
    ['Strategy', config.strategy_type],
    ['Fast SMA', config.fast_period],
    ['Slow SMA', config.slow_period],
    ['Stop loss', `${config.stop_loss_percentage}%`],
    ['Take profit', `${config.take_profit_percentage}%`],
    ['Initial capital', `${formatNumber(config.initial_capital)} USDT`],
    ['Amount per trade', `${formatNumber(config.quote_per_trade)} USDT`],
    ['Fee per side', `${config.fee_percentage_per_side}%`],
    ['Slippage', `${config.slippage_bps} bps`],
  ]

  return (
    <div className="ai-result-card" style={{ marginTop: 14 }}>
      <div className="ai-result-heading">
        <div>
          <span className="ai-result-eyebrow">CONFIGURATION REVIEW</span>
          <h3>Backtest ready for confirmation</h3>
        </div>
        <span className="ai-result-status success">
          <CheckCircle2 size={14} /> Validated
        </span>
      </div>

      <div className="ai-result-grid">
        {fields.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value ?? '—'}</strong>
          </div>
        ))}
      </div>

      {defaults.length > 0 && (
        <div className="ai-result-note" style={{ marginTop: 14 }}>
          <Info size={15} />
          <span>
            Defaults applied: {defaults.map(
              (item) => `${item.field}: ${item.value}`
            ).join(' · ')}
          </span>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <button
          type="button"
          className="ai-new-chat"
          onClick={onConfirm}
          disabled={loading}
        >
          {loading ? (
            <LoaderCircle size={16} className="ai-spinner" />
          ) : (
            <Activity size={16} />
          )}
          {loading ? 'Starting backtest...' : 'Confirm & run backtest'}
        </button>
      </div>
    </div>
  )
}

// BACKTEST EXECUTION AND REPORT

function BacktestReportCard({ job }) {
  if (!job) return null

  if (job.status === 'queued' || job.status === 'running') {
    return (
      <div className="ai-result-card" style={{ marginTop: 14 }}>
        <div className="ai-result-heading">
          <div>
            <span className="ai-result-eyebrow">BACKTEST EXECUTION</span>
            <h3>
              {job.status === 'queued'
                ? 'Waiting to execute'
                : 'Backtest running'}
            </h3>
          </div>
          <LoaderCircle size={20} className="ai-spinner" />
        </div>

        <p>
          {job.status === 'queued'
            ? 'Your backtest has been accepted and is waiting for execution.'
            : 'The Python engine is processing historical market data.'}
        </p>

        <small>Run ID: {job.run_id}</small>
      </div>
    )
  }

  if (job.status === 'failed') {
    return (
      <div className="ai-result-card" style={{ marginTop: 14 }}>
        <div className="ai-inline-error">
          <AlertCircle size={16} />
          Backtest failed: {job.error || 'Unknown execution error'}
        </div>
      </div>
    )
  }

  if (job.status !== 'completed' || !job.results) return null

  const result = job.results
  const pnl = Number(result.total_pnl)
  const positive = pnl >= 0

  return (
    <div className="ai-result-card" style={{ marginTop: 14 }}>
      <div className="ai-result-heading">
        <div>
          <span className="ai-result-eyebrow">PYTHON BACKTEST ENGINE</span>
          <h3>Backtest report</h3>
        </div>
        <span className="ai-result-status success">
          <CheckCircle2 size={14} /> Completed
        </span>
      </div>

      <div className="ai-result-quantity">
        <strong className={positive ? 'passed' : 'ai-loss-value'}>
          {positive ? '+' : ''}{formatNumber(pnl)} USDT
        </strong>
        <span>Net profit / loss</span>
      </div>

      <div className="ai-result-grid">
        <div>
          <span>Total return</span>
          <strong>{formatNumber(result.total_return_percentage, 4)}%</strong>
        </div>

        <div>
          <span>Initial capital</span>
          <strong>{formatNumber(result.initial_capital)} USDT</strong>
        </div>

        <div>
          <span>Final equity</span>
          <strong>{formatNumber(result.final_equity)} USDT</strong>
        </div>

        <div>
          <span>Closed trades</span>
          <strong>{result.closed_trade_count}</strong>
        </div>

        <div>
          <span>Winning trades</span>
          <strong>{result.winning_trades}</strong>
        </div>

        <div>
          <span>Losing trades</span>
          <strong>{result.losing_trades}</strong>
        </div>

        <div>
          <span>Win rate</span>
          <strong>{formatNumber(result.win_rate_percentage)}%</strong>
        </div>

        <div>
          <span>Max drawdown</span>
          <strong>{formatNumber(result.max_drawdown_percentage, 4)}%</strong>
        </div>

        <div>
          <span>Profit factor</span>
          <strong>{formatNumber(result.profit_factor, 3)}</strong>
        </div>

        <div>
          <span>Candles processed</span>
          <strong>{job.candles_processed}</strong>
        </div>

        <div>
          <span>Engine execution</span>
          <strong>{job.execution_time_seconds} sec</strong>
        </div>

        <div>
          <span>Dataset</span>
          <strong>{job.dataset || '—'}</strong>
        </div>
      </div>

      {result.open_position && (
        <div className="ai-result-note" style={{ marginTop: 14 }}>
          <Info size={15} />
          <span>
            A position remains open at the end of the dataset.
            Unrealized P&L: {formatNumber(
              result.open_position.unrealized_pnl
            )} USDT. It is included in final equity.
          </span>
        </div>
      )}

      <div className="ai-result-disclaimer">
        <ShieldCheck size={14} />
        Historical simulation only. No live orders were placed.
      </div>
    </div>
  )
}

// CHAT MESSAGE

function AssistantMessage({ message }) {
  return (
    <div className={`ai-message ${message.role}`}>
      <div className="ai-message-avatar">
        {message.role === 'assistant' ? (
          <Bot size={17} />
        ) : (
          <User size={17} />
        )}
      </div>

      <div className="ai-message-content">
        <div className="ai-message-author">
          {message.role === 'assistant' ? 'TradeSim AI' : 'You'}
        </div>

        {message.text && (
          <div className="ai-message-text">{message.text}</div>
        )}

        {message.question && (
          <div className="ai-question">
            <Sparkles size={15} />
            {message.question}
          </div>
        )}

        {message.calculation && (
          <ResultCard calculation={message.calculation} />
        )}

        {message.calculationError && (
          <div className="ai-inline-error">
            <AlertCircle size={15} />
            {message.calculationError}
          </div>
        )}

        {message.explanation && (
          <div className="ai-explanation">
            <div className="ai-explanation-heading">
              <Sparkles size={14} />
              Calculation explanation
            </div>
            <p>{message.explanation}</p>
          </div>
        )}
      </div>
    </div>
  )
}

// MAIN AI ASSISTANT

function AIAssistant() {
  const [messages, setMessages] = useState([initialMessage])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const [sessionId, setSessionId] = useState(
    () => sessionStorage.getItem('tradesim_ai_session') || null
  )

  const [apiError, setApiError] = useState('')

  // Backtest state
  const [backtestConfig, setBacktestConfig] = useState(null)
  const [backtestDefaults, setBacktestDefaults] = useState([])
  const [backtestJob, setBacktestJob] = useState(null)
  const [backtestStarting, setBacktestStarting] = useState(false)

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, backtestConfig, backtestJob])

  // PREPARE BACKTEST

  async function prepareBacktest(prompt) {
    const response = await fetch(`${API_URL}/api/backtests/prepare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ prompt }),
    })

    const data = await response.json()

    if (!response.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map((item) => item.msg).join(', ')
        : data.detail

      throw new Error(detail || 'Could not prepare the backtest.')
    }

    if (!data.ready || !data.config) {
      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: data.interpretation?.user_explanation
            || 'I need some more information before preparing this backtest.',
          question: data.interpretation?.clarification_question
            || data.interpretation?.missing_information?.join(', ')
            || null,
        },
      ])
      return
    }

    setBacktestConfig(data.config)
    setBacktestDefaults(data.defaults_applied || [])
    setBacktestJob(null)

    setMessages((previous) => [
      ...previous,
      {
        role: 'assistant',
        text: data.message
          || 'I have prepared and validated your backtest configuration. Review the settings below before execution.',
      },
    ])
  }

  // START BACKTEST

  async function confirmBacktest() {
    if (!backtestConfig || backtestStarting) return

    setBacktestStarting(true)
    setApiError('')

    try {
      const response = await fetch(`${API_URL}/api/backtests/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ config: backtestConfig }),
      })

      const data = await response.json()

      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item) => item.msg).join(', ')
          : data.detail

        throw new Error(detail || 'Could not start the backtest.')
      }

      setBacktestJob(data.job)
      setBacktestConfig(null)

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: 'Your backtest has been submitted to the Python engine. I will retrieve its result automatically.',
        },
      ])
    } catch (error) {
      setApiError(error.message)
    } finally {
      setBacktestStarting(false)
    }
  }

  // AUTOMATIC BACKTEST STATUS CHECK

  useEffect(() => {
    const runId = backtestJob?.run_id

    if (
      !runId ||
      !['queued', 'running'].includes(backtestJob.status)
    ) {
      return
    }

    let cancelled = false

    async function checkStatus() {
      try {
        const response = await fetch(
          `${API_URL}/api/backtests/${encodeURIComponent(runId)}`
        )

        if (!response.ok) {
          throw new Error('Unable to retrieve backtest status.')
        }

        const data = await response.json()

        if (!cancelled) {
          setBacktestJob(data)
        }
      } catch (error) {
        if (!cancelled) {
          setApiError(error.message)
        }
      }
    }

    const intervalId = setInterval(checkStatus, 1000)
    checkStatus()

    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [backtestJob?.run_id, backtestJob?.status])

  // SEND MESSAGE

  async function sendMessage(event) {
    event.preventDefault()

    const message = input.trim()

    if (!message || loading) return

    setInput('')
    setApiError('')
    setLoading(true)

    setMessages((previous) => [
      ...previous,
      { role: 'user', text: message },
    ])

    // Backtest requests use the dedicated backtest API.
    const isBacktestRequest =
      /\b(backtest|back-testing|back testing|historical test)\b/i.test(message)

    if (isBacktestRequest) {
      try {
        await prepareBacktest(message)
      } catch (error) {
        setMessages((previous) => [
          ...previous,
          {
            role: 'assistant',
            text: `I couldn't prepare the backtest: ${error.message}`,
            isError: true,
          },
        ])

        setApiError(error.message)
      } finally {
        setLoading(false)
        inputRef.current?.focus()
      }

      return
    }

    // Existing AI chat and position sizing flow.

    try {
      const response = await fetch(`${API_URL}/api/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item) => item.msg).join(', ')
          : data.detail

        throw new Error(detail || 'The AI request failed.')
      }

      if (data.session_id) {
        setSessionId(data.session_id)
        sessionStorage.setItem('tradesim_ai_session', data.session_id)
      }

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: data.user_explanation || 'I processed your request.',
          question: data.needs_clarification
            ? data.clarification_question
            : null,
          calculation: data.calculation,
          calculationError: data.calculation_error,
          explanation: data.ai_explanation,
          missingInformation: data.missing_information,
        },
      ])
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: `I couldn't complete that request: ${error.message}`,
          isError: true,
        },
      ])

      setApiError(error.message)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  // NEW CHAT

  async function startNewChat() {
    if (loading || backtestStarting) return

    try {
      if (sessionId) {
        await fetch(
          `${API_URL}/api/ai/reset/${encodeURIComponent(sessionId)}`,
          { method: 'POST' }
        )
      }
    } catch {
      // A new local conversation can still begin if reset fails.
    }

    sessionStorage.removeItem('tradesim_ai_session')

    setSessionId(null)
    setMessages([initialMessage])
    setInput('')
    setApiError('')

    setBacktestConfig(null)
    setBacktestDefaults([])
    setBacktestJob(null)

    inputRef.current?.focus()
  }

  const suggestions = [
    'Calculate a BTC position with 1% risk',
    'Explain how leverage affects margin',
    'Backtest Bitcoin spot using a 10 and 30 SMA crossover',
  ]

  return (
    <div className="ai-page">
      <div className="ai-page-heading">
        <div>
          <div className="ai-page-eyebrow">
            <Sparkles size={14} /> INTELLIGENT TRADING WORKSPACE
          </div>

          <h1>AI Assistant</h1>

          <p>
            Describe your trading ideas. TradeSim interprets them and
            uses its Python engine for verified calculations and backtesting.
          </p>
        </div>

        <button
          type="button"
          className="ai-new-chat"
          onClick={startNewChat}
          disabled={loading || backtestStarting}
        >
          <Plus size={16} />
          New chat
        </button>
      </div>

      <div className="ai-workspace">
        <div className="ai-chat-top">
          <div className="ai-chat-identity">
            <div className="ai-chat-icon">
              <Bot size={21} />
            </div>

            <div>
              <strong>TradeSim AI</strong>
              <span><i /> AI engine connected through backend</span>
            </div>
          </div>

          <div className="ai-chat-mode">
            <TrendingUp size={14} />
            SIMULATION MODE
          </div>
        </div>

        <div className="ai-messages">
          {messages.map((message, index) => (
            <AssistantMessage
              key={`${index}-${message.role}`}
              message={message}
            />
          ))}

          {backtestConfig && (
            <div className="ai-message assistant">
              <div className="ai-message-avatar">
                <Bot size={17} />
              </div>

              <div className="ai-message-content">
                <div className="ai-message-author">TradeSim AI</div>

                <BacktestPreparationCard
                  config={backtestConfig}
                  defaults={backtestDefaults}
                  onConfirm={confirmBacktest}
                  loading={backtestStarting}
                />
              </div>
            </div>
          )}

          {backtestJob && (
            <div className="ai-message assistant">
              <div className="ai-message-avatar">
                <Bot size={17} />
              </div>

              <div className="ai-message-content">
                <div className="ai-message-author">TradeSim AI</div>

                <BacktestReportCard job={backtestJob} />
              </div>
            </div>
          )}

          {loading && (
            <div className="ai-message assistant">
              <div className="ai-message-avatar">
                <Bot size={17} />
              </div>

              <div className="ai-message-content">
                <div className="ai-message-author">TradeSim AI</div>

                <div className="ai-thinking">
                  <LoaderCircle size={16} className="ai-spinner" />
                  Understanding your request and processing...
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="ai-composer-area">
          {messages.length === 1 && (
            <div className="ai-suggestions">
              {suggestions.map((suggestion) => (
                <button
                  type="button"
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          {apiError && (
            <div className="ai-api-status">
              <AlertCircle size={14} />
              Last request failed: {apiError}
            </div>
          )}

          <form className="ai-composer" onSubmit={sendMessage}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  sendMessage(event)
                }
              }}
              placeholder="Describe your trading idea or ask TradeSim..."
              rows={2}
              maxLength={5000}
              disabled={loading}
            />

            <div className="ai-composer-footer">
              <span>
                AI can make mistakes. Verify trading parameters before proceeding.
              </span>

              <button
                type="submit"
                disabled={!input.trim() || loading}
                aria-label="Send message"
              >
                {loading ? (
                  <LoaderCircle size={17} className="ai-spinner" />
                ) : (
                  <Send size={17} />
                )}
              </button>
            </div>
          </form>

          <div className="ai-bottom-note">
            <ShieldCheck size={13} />
            Python performs calculations. No live orders are placed.
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIAssistant
