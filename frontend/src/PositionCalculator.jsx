
import { useState } from 'react'
import {
  Calculator,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  LoaderCircle,
} from 'lucide-react'
import './PositionCalculator.css'

const initialForm = {
  symbol: 'BTCUSDT',
  market_type: 'spot',
  order_type: 'MARKET',
  capital: '20000',
  capital_currency: 'USDT',
  risk_percentage: '1',
  entry_price: '90000',
  stop_loss: '88200',
  side: 'long',
  fee_percentage_per_side: '0.1',
  slippage_bps: '5',
  leverage: '1',
  additional_isolated_margin: '0',
}

function formatNumber(value, decimals = 4) {
  if (value === null || value === undefined) return '—'

  const number = Number(value)
  if (!Number.isFinite(number)) return '—'

  return number.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  })
}

function ResultCard({ label, value, description, highlight = false }) {
  return (
    <div className={`result-card ${highlight ? 'highlight-result' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {description && <small>{description}</small>}
    </div>
  )
}

function PositionCalculator() {
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const isFutures = form.market_type === 'futures'

  function updateField(event) {
    const { name, value } = event.target

    setForm((previous) => {
      const updated = { ...previous, [name]: value }

      if (name === 'market_type') {
        updated.side = 'long'
        updated.leverage = value === 'spot' ? '1' : '5'
        updated.additional_isolated_margin = '0'
      }

      return updated
    })

    setError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(
        '/api/calculator/position-size',
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify(form),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        const message = Array.isArray(data.detail)
          ? data.detail.map((item) => item.msg).join(', ')
          : data.detail || 'Calculation failed.'

        throw new Error(message)
      }

      setResult(data)
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? 'Cannot reach the TradeSim API. Make sure FastAPI is running on port 8000.'
          : err.message,
      )
    } finally {
      setLoading(false)
    }
  }

  function resetForm() {
    setForm(initialForm)
    setResult(null)
    setError('')
  }

  return (
    <div className="position-page">
      <div className="position-heading">
        <div>
          <div className="eyebrow">TRADE MANAGEMENT / RISK TOOLS</div>
          <h1>Position Calculator</h1>
          <p>
            Calculate position size using risk, capital and Binance exchange
            rules.
          </p>
        </div>

        <div className="calculator-status">
          <span className="status-dot" />
          PYTHON ENGINE
        </div>
      </div>

      <div className="calculator-layout">
        <section className="calculator-panel">
          <div className="calculator-panel-heading">
            <div className="calculator-heading-icon">
              <Calculator size={19} />
            </div>
            <div>
              <h2>Trade parameters</h2>
              <p>Configure your simulated trade</p>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-section">
              <div className="form-section-title">MARKET CONFIGURATION</div>

              <div className="form-grid">
                <label className="field">
                  <span>Trading pair</span>
                  <input
                    name="symbol"
                    value={form.symbol}
                    onChange={updateField}
                    placeholder="BTCUSDT"
                    required
                  />
                </label>

                <label className="field">
                  <span>Market type</span>
                  <select
                    name="market_type"
                    value={form.market_type}
                    onChange={updateField}
                  >
                    <option value="spot">Spot</option>
                    <option value="futures">USD-M Futures</option>
                  </select>
                </label>

                <label className="field">
                  <span>Order type</span>
                  <select
                    name="order_type"
                    value={form.order_type}
                    onChange={updateField}
                  >
                    <option value="MARKET">Market</option>
                    <option value="LIMIT">Limit</option>
                  </select>
                </label>

                <label className="field">
                  <span>Position side</span>
                  <select
                    name="side"
                    value={form.side}
                    onChange={updateField}
                  >
                    <option value="long">Long</option>
                    {isFutures && <option value="short">Short</option>}
                  </select>
                </label>
              </div>
            </div>

            <div className="form-section">
              <div className="form-section-title">CAPITAL & RISK</div>

              <div className="form-grid">
                <label className="field">
                  <span>Available capital</span>
                  <input
                    name="capital"
                    type="number"
                    min="0.00000001"
                    step="any"
                    value={form.capital}
                    onChange={updateField}
                    required
                  />
                </label>

                <label className="field">
                  <span>Capital currency</span>
                  <input
                    name="capital_currency"
                    value={form.capital_currency}
                    onChange={updateField}
                    required
                  />
                </label>

                <label className="field">
                  <span>Risk percentage (%)</span>
                  <input
                    name="risk_percentage"
                    type="number"
                    min="0.00000001"
                    max="100"
                    step="any"
                    value={form.risk_percentage}
                    onChange={updateField}
                    required
                  />
                </label>

                <div className="risk-preview">
                  <span>Risk budget</span>
                  <strong>
                    {formatNumber(
                      Number(form.capital) * Number(form.risk_percentage) / 100,
                      2,
                    )}{' '}
                    {form.capital_currency || 'USDT'}
                  </strong>
                </div>
              </div>
            </div>

            <div className="form-section">
              <div className="form-section-title">ENTRY & EXIT</div>

              <div className="form-grid">
                <label className="field">
                  <span>Entry price</span>
                  <input
                    name="entry_price"
                    type="number"
                    min="0.00000001"
                    step="any"
                    value={form.entry_price}
                    onChange={updateField}
                    required
                  />
                </label>

                <label className="field">
                  <span>Stop-loss price</span>
                  <input
                    name="stop_loss"
                    type="number"
                    min="0.00000001"
                    step="any"
                    value={form.stop_loss}
                    onChange={updateField}
                    required
                  />
                </label>
              </div>
            </div>

            {isFutures && (
              <div className="form-section">
                <div className="form-section-title">FUTURES CONFIGURATION</div>

                <div className="form-grid">
                  <label className="field">
                    <span>Leverage (x)</span>
                    <input
                      name="leverage"
                      type="number"
                      min="1"
                      step="1"
                      value={form.leverage}
                      onChange={updateField}
                      required
                    />
                  </label>

                  <label className="field">
                    <span>Additional isolated margin</span>
                    <input
                      name="additional_isolated_margin"
                      type="number"
                      min="0"
                      step="any"
                      value={form.additional_isolated_margin}
                      onChange={updateField}
                    />
                  </label>
                </div>
                <p className="field-hint">
                  Additional margin is quote-asset collateral allocated to
                  this isolated Futures position.
                </p>
              </div>
            )}

            <div className="form-section">
              <div className="form-section-title">EXECUTION ASSUMPTIONS</div>

              <div className="form-grid">
                <label className="field">
                  <span>Fee per side (%)</span>
                  <input
                    name="fee_percentage_per_side"
                    type="number"
                    min="0"
                    step="any"
                    value={form.fee_percentage_per_side}
                    onChange={updateField}
                    required
                  />
                </label>

                <label className="field">
                  <span>Slippage (basis points)</span>
                  <input
                    name="slippage_bps"
                    type="number"
                    min="0"
                    step="any"
                    value={form.slippage_bps}
                    onChange={updateField}
                    required
                  />
                </label>
              </div>
            </div>

            {error && (
              <div className="calculator-error" role="alert">
                <AlertTriangle size={17} />
                <span>{error}</span>
              </div>
            )}

            <div className="calculator-actions">
              <button
                className="reset-button"
                type="button"
                onClick={resetForm}
                disabled={loading}
              >
                <RefreshCw size={15} />
                Reset
              </button>

              <button
                className="calculate-button"
                type="submit"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <LoaderCircle className="spin" size={17} />
                    Calculating...
                  </>
                ) : (
                  <>
                    <Calculator size={17} />
                    Calculate position
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        <section className="results-column">
          {!result && !loading && (
            <div className="empty-result">
              <div className="empty-result-icon">
                <Calculator size={27} />
              </div>
              <h2>Calculation results</h2>
              <p>
                Your position sizing, risk and execution estimates will appear
                here after calculation.
              </p>
              <div className="empty-result-note">
                <ShieldCheck size={16} />
                Calculations performed by the Python engine
              </div>
            </div>
          )}

          {loading && (
            <div className="empty-result loading-result">
              <LoaderCircle className="spin" size={30} />
              <h2>Calculating your position</h2>
              <p>Fetching Binance exchange rules and running the Python engine.</p>
            </div>
          )}

          {result && (
            <>
              <div className="result-header">
                <div>
                  <div className="eyebrow">CALCULATION COMPLETE</div>
                  <h2>{result.symbol} <span>{result.market_type.toUpperCase()}</span></h2>
                </div>
                <div className="success-icon"><ShieldCheck size={20} /></div>
              </div>

              <div className="primary-result">
                <span>POSITION QUANTITY</span>
                <strong>{formatNumber(result.position_quantity, 8)}</strong>
                <small>{result.symbol.replace(result.quote_asset, '')} · {result.side.toUpperCase()}</small>
              </div>

              <div className="results-grid">
                <ResultCard
                  label="Position value"
                  value={`${formatNumber(result.position_value, 2)} ${result.quote_asset}`}
                />
                <ResultCard
                  label="Risk budget"
                  value={`${formatNumber(result.risk_budget, 2)} ${result.quote_asset}`}
                />
                <ResultCard
                  label="Estimated total loss"
                  value={`${formatNumber(result.estimated_total_loss, 2)} ${result.quote_asset}`}
                  highlight
                />
                <ResultCard
                  label="Estimated fees"
                  value={`${formatNumber(result.estimated_fees, 2)} ${result.quote_asset}`}
                />
                <ResultCard
                  label="Margin required"
                  value={`${formatNumber(result.margin_required_estimate, 2)} ${result.quote_asset}`}
                />
                <ResultCard
                  label="Capital required"
                  value={`${formatNumber(result.capital_required_estimate, 2)} ${result.quote_asset}`}
                />
              </div>

              <div className="validation-panel">
                <h3>Risk & exchange validation</h3>

                <div className="validation-row">
                  <span>Risk budget respected</span>
                  <strong className={result.risk_budget_respected ? 'valid' : 'invalid'}>
                    {result.risk_budget_respected ? 'Passed' : 'Failed'}
                  </strong>
                </div>
                <div className="validation-row">
                  <span>Capital constraint</span>
                  <strong className={result.capital_constraint_respected ? 'valid' : 'invalid'}>
                    {result.capital_constraint_respected ? 'Passed' : 'Failed'}
                  </strong>
                </div>
                <div className="validation-row">
                  <span>Quantity filters</span>
                  <strong className={result.quantity_filter_respected ? 'valid' : 'invalid'}>
                    {result.quantity_filter_respected ? 'Passed' : 'Failed'}
                  </strong>
                </div>
                <div className="validation-row">
                  <span>Notional filters</span>
                  <strong className={result.notional_filter_respected ? 'valid' : 'invalid'}>
                    {result.notional_filter_respected ? 'Passed' : 'Failed'}
                  </strong>
                </div>
              </div>

              <div className="liquidation-panel">
                <h3>Liquidation estimate</h3>
                <div className="liquidation-value">
                  {result.liquidation_price_estimate
                    ? `${formatNumber(result.liquidation_price_estimate, 4)} ${result.quote_asset}`
                    : 'Unavailable'}
                </div>
                <p>
                  {result.liquidation_note ||
                    (result.liquidation_estimation_status === 'estimated_from_account_brackets'
                      ? 'Estimated using account-specific Binance leverage brackets.'
                      : result.liquidation_estimation_status === 'not_applicable'
                        ? 'Liquidation estimation does not apply to Spot positions.'
                        : 'Account-specific leverage brackets are required for this estimate.')}
                </p>
              </div>

              <div className="result-disclaimer">
                <AlertTriangle size={15} />
                Estimates only. Slippage, fees, funding, mark price and
                liquidation conditions can differ from actual exchange outcomes.
                No orders are sent to Binance.
              </div>

              <button
                className="recalculate-button"
                type="button"
                onClick={() => setResult(null)}
              >
                <RefreshCw size={15} />
                Change parameters
              </button>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

export default PositionCalculator
