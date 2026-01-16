import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import FormField from '../components/FormField'
import { RateComparisonChart, SurvivalPlot } from '../components/charts'

const ANALYSIS_TYPES = {
  survival: {
    id: 'survival',
    label: 'Survival / Time-to-Event',
    description: 'Compare how long until an event occurs between groups',
    examples: 'Time to first purchase, time to churn, time to conversion',
    icon: '⏱️',
  },
  rates: {
    id: 'rates',
    label: 'Event Rates (Poisson)',
    description: 'Compare how often events occur per unit of time',
    examples: 'Support tickets per day, errors per hour, purchases per week',
    icon: '📊',
  },
}

function TimingCalculator() {
  const [analysisType, setAnalysisType] = useState('rates')
  
  const [ratesData, setRatesData] = useState({
    control_events: 45,
    control_exposure: 100,
    treatment_events: 38,
    treatment_exposure: 100,
    confidence: 95,
    exposure_unit: 'days',
  })

  const [survivalData, setSurvivalData] = useState({
    control_times: '5, 8, 12, 15, 18, 22, 25, 30, 35, 40',
    control_events: '1, 1, 1, 0, 1, 1, 0, 1, 0, 1',
    treatment_times: '3, 6, 9, 12, 14, 16, 20, 24, 28, 32',
    treatment_events: '1, 1, 1, 1, 0, 1, 1, 0, 1, 1',
    confidence: 95,
  })

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleRatesChange = (e) => {
    const { name, value } = e.target
    setRatesData(prev => ({
      ...prev,
      [name]: name === 'exposure_unit' ? value : parseFloat(value) || 0
    }))
  }

  const handleSurvivalChange = (e) => {
    const { name, value } = e.target
    setSurvivalData(prev => ({
      ...prev,
      [name]: name === 'confidence' ? parseFloat(value) : value
    }))
  }

  const parseArray = (str) => {
    return str.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      let endpoint, payload

      if (analysisType === 'rates') {
        endpoint = '/api/timing/rates/analyze'
        payload = {
          control_events: ratesData.control_events,
          control_exposure: ratesData.control_exposure,
          treatment_events: ratesData.treatment_events,
          treatment_exposure: ratesData.treatment_exposure,
          confidence: ratesData.confidence,
        }
      } else {
        endpoint = '/api/timing/analyze'
        const controlTimes = parseArray(survivalData.control_times)
        const controlEvents = parseArray(survivalData.control_events).map(e => Math.round(e))
        const treatmentTimes = parseArray(survivalData.treatment_times)
        const treatmentEvents = parseArray(survivalData.treatment_events).map(e => Math.round(e))

        if (controlTimes.length !== controlEvents.length) {
          throw new Error('Control times and events must have the same number of values')
        }
        if (treatmentTimes.length !== treatmentEvents.length) {
          throw new Error('Treatment times and events must have the same number of values')
        }

        payload = {
          control_times: controlTimes,
          control_events: controlEvents,
          treatment_times: treatmentTimes,
          treatment_events: treatmentEvents,
          confidence: survivalData.confidence,
        }
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResult({ ...data, type: analysisType })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const controlRate = ratesData.control_events / ratesData.control_exposure
  const treatmentRate = ratesData.treatment_events / ratesData.treatment_exposure

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Timing & Rate Analysis</h1>
        <p className="page-description">
          Analyze time-to-event data (survival analysis) or compare event rates between groups.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">⏱️</span>
        <div className="info-box-content">
          <div className="info-box-title">When to use timing analysis?</div>
          <div className="info-box-text">
            Use <strong>Survival Analysis</strong> when measuring "time until something happens" (first purchase, churn, conversion).
            Use <strong>Event Rate Analysis</strong> when counting "how many events per time period" (support tickets, errors, transactions).
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Analysis Type</div>
        <div className="test-type-options">
          {Object.values(ANALYSIS_TYPES).map((type) => (
            <button
              key={type.id}
              type="button"
              className={`test-type-option ${analysisType === type.id ? 'active' : ''}`}
              onClick={() => { setAnalysisType(type.id); setResult(null); }}
            >
              <span className="test-type-icon">{type.icon}</span>
              <div className="test-type-content">
                <div className="test-type-label">{type.label}</div>
                <div className="test-type-description">{type.description}</div>
              </div>
            </button>
          ))}
        </div>
        <div className="test-type-example">
          <span className="example-label">Example:</span> {ANALYSIS_TYPES[analysisType].examples}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {analysisType === 'rates' ? (
          <>
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control</span>
                </div>
                <FormField
                  label="Number of Events"
                  hint="Total events observed in control group"
                >
                  <input
                    type="number"
                    name="control_events"
                    className="form-input"
                    value={ratesData.control_events}
                    onChange={handleRatesChange}
                    min="0"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField
                    label="Exposure Time"
                    hint={`Total observation time (in ${ratesData.exposure_unit})`}
                  >
                    <input
                      type="number"
                      name="control_exposure"
                      className="form-input"
                      value={ratesData.control_exposure}
                      onChange={handleRatesChange}
                      min="0.01"
                      step="any"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
                    {controlRate.toFixed(4)} per {ratesData.exposure_unit.slice(0, -1)}
                  </span>
                </div>
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Treatment</span>
                </div>
                <FormField
                  label="Number of Events"
                  hint="Total events observed in treatment group"
                >
                  <input
                    type="number"
                    name="treatment_events"
                    className="form-input"
                    value={ratesData.treatment_events}
                    onChange={handleRatesChange}
                    min="0"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField
                    label="Exposure Time"
                    hint={`Total observation time (in ${ratesData.exposure_unit})`}
                  >
                    <input
                      type="number"
                      name="treatment_exposure"
                      className="form-input"
                      value={ratesData.treatment_exposure}
                      onChange={handleRatesChange}
                      min="0.01"
                      step="any"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
                    {treatmentRate.toFixed(4)} per {ratesData.exposure_unit.slice(0, -1)}
                  </span>
                </div>
              </div>
            </div>

            <div className="card" style={{ marginTop: '16px' }}>
              <div className="form-grid">
                <FormField label="Time Unit" hint="Unit of your exposure time">
                  <select
                    name="exposure_unit"
                    className="form-select"
                    value={ratesData.exposure_unit}
                    onChange={handleRatesChange}
                  >
                    <option value="hours">Hours</option>
                    <option value="days">Days</option>
                    <option value="weeks">Weeks</option>
                    <option value="months">Months</option>
                  </select>
                </FormField>
                <FormField label="Confidence Level">
                  <select
                    name="confidence"
                    className="form-select"
                    value={ratesData.confidence}
                    onChange={handleRatesChange}
                  >
                    <option value={90}>90%</option>
                    <option value={95}>95%</option>
                    <option value={99}>99%</option>
                  </select>
                </FormField>
              </div>
              <div style={{ marginTop: '16px' }}>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze Rates'}
                </button>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control Group</span>
                </div>
                <FormField
                  label="Times (comma-separated)"
                  hint="Time values for each subject (e.g., days until event)"
                >
                  <textarea
                    name="control_times"
                    className="form-input"
                    value={survivalData.control_times}
                    onChange={handleSurvivalChange}
                    rows={3}
                    style={{ resize: 'vertical' }}
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField
                    label="Events (comma-separated)"
                    hint="1 = event occurred, 0 = censored (dropped out/study ended)"
                  >
                    <textarea
                      name="control_events"
                      className="form-input"
                      value={survivalData.control_events}
                      onChange={handleSurvivalChange}
                      rows={3}
                      style={{ resize: 'vertical' }}
                    />
                  </FormField>
                </div>
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Treatment Group</span>
                </div>
                <FormField
                  label="Times (comma-separated)"
                  hint="Time values for each subject (e.g., days until event)"
                >
                  <textarea
                    name="treatment_times"
                    className="form-input"
                    value={survivalData.treatment_times}
                    onChange={handleSurvivalChange}
                    rows={3}
                    style={{ resize: 'vertical' }}
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField
                    label="Events (comma-separated)"
                    hint="1 = event occurred, 0 = censored (dropped out/study ended)"
                  >
                    <textarea
                      name="treatment_events"
                      className="form-input"
                      value={survivalData.treatment_events}
                      onChange={handleSurvivalChange}
                      rows={3}
                      style={{ resize: 'vertical' }}
                    />
                  </FormField>
                </div>
              </div>
            </div>

            <div className="card" style={{ marginTop: '16px' }}>
              <FormField label="Confidence Level">
                <select
                  name="confidence"
                  className="form-select"
                  value={survivalData.confidence}
                  onChange={handleSurvivalChange}
                  style={{ maxWidth: '200px' }}
                >
                  <option value={90}>90%</option>
                  <option value={95}>95%</option>
                  <option value={99}>99%</option>
                </select>
              </FormField>
              <div style={{ marginTop: '16px' }}>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze Survival'}
                </button>
              </div>
            </div>
          </>
        )}
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && result.type === 'rates' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? (result.rate_ratio < 1 ? 'tag-green' : 'tag-red') : 'tag-yellow'}`}>
              {result.is_significant
                ? (result.rate_ratio < 1 ? '✓ Treatment Reduces Rate' : '✓ Treatment Increases Rate')
                : '○ No Significant Difference'
              }
            </span>
            <span style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              {result.rate_difference_percent > 0 ? '+' : ''}{result.rate_difference_percent.toFixed(1)}%
            </span>
          </div>

          <RateComparisonChart
            controlRate={result.control_rate}
            treatmentRate={result.treatment_rate}
            controlCI={result.control_rate_ci}
            treatmentCI={result.treatment_rate_ci}
            label="Event Rate"
            unit={ratesData.exposure_unit.slice(0, -1)}
          />

          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Control Rate</div>
              <div className="result-value">{result.control_rate.toFixed(4)}</div>
              <div className="result-unit">per {ratesData.exposure_unit.slice(0, -1)}</div>
            </div>
            <div className="result-item">
              <div className="result-label">Treatment Rate</div>
              <div className="result-value">{result.treatment_rate.toFixed(4)}</div>
              <div className="result-unit">per {ratesData.exposure_unit.slice(0, -1)}</div>
            </div>
            <div className="result-item">
              <div className="result-label">Rate Ratio</div>
              <div className="result-value">{result.rate_ratio.toFixed(3)}</div>
            </div>
            <div className="result-item">
              <div className="result-label">P-Value</div>
              <div className="result-value">{result.p_value.toFixed(4)}</div>
            </div>
          </div>

          <div className="stats-explanation">
            <div className="stats-card">
              <div className="stats-card-label">Rate Ratio Explained</div>
              <div className="stats-card-value">{result.rate_ratio.toFixed(3)}</div>
              <div className="stats-card-explanation">
                {result.rate_ratio < 1
                  ? `Treatment reduces event rate by ${((1 - result.rate_ratio) * 100).toFixed(1)}%`
                  : result.rate_ratio > 1
                    ? `Treatment increases event rate by ${((result.rate_ratio - 1) * 100).toFixed(1)}%`
                    : 'No difference in event rates'
                }
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">95% Confidence Interval</div>
              <div className="stats-card-value">[{result.rate_ratio_ci[0].toFixed(3)}, {result.rate_ratio_ci[1].toFixed(3)}]</div>
              <div className="stats-card-explanation">
                The true rate ratio likely falls within this range.
                {result.rate_ratio_ci[0] > 1 && ' (Both bounds > 1: treatment increases rate)'}
                {result.rate_ratio_ci[1] < 1 && ' (Both bounds < 1: treatment decreases rate)'}
                {result.rate_ratio_ci[0] <= 1 && result.rate_ratio_ci[1] >= 1 && ' (Includes 1: effect uncertain)'}
              </div>
            </div>
          </div>

          <div className={`callout ${result.is_significant ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '16px' }}>
            <div className="callout-text markdown-content">
              <ReactMarkdown>{result.recommendation}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {result && result.type === 'survival' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? (result.hazard_ratio < 1 ? 'tag-green' : 'tag-blue') : 'tag-yellow'}`}>
              {result.is_significant
                ? (result.hazard_ratio < 1 ? '✓ Treatment Slows Events' : '✓ Treatment Speeds Events')
                : '○ No Significant Difference'
              }
            </span>
            <span style={{ fontSize: '20px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              HR = {result.hazard_ratio.toFixed(3)}
            </span>
          </div>

          {result.control_median_time && result.treatment_median_time && (
            <SurvivalPlot
              controlMedian={result.control_median_time}
              treatmentMedian={result.treatment_median_time}
              controlEvents={result.control_events}
              treatmentEvents={result.treatment_events}
              hazardRatio={result.hazard_ratio}
            />
          )}

          <div className="card-title">Survival Summary</div>
          <div className="summary-table-wrapper">
          <table className="summary-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Control</th>
                <th>Treatment</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Median Time</td>
                <td className="mono">{result.control_median_time?.toFixed(1) || 'Not reached'}</td>
                <td className="mono">{result.treatment_median_time?.toFixed(1) || 'Not reached'}</td>
              </tr>
              <tr>
                <td>Events</td>
                <td className="mono">{result.control_events}</td>
                <td className="mono">{result.treatment_events}</td>
              </tr>
              <tr>
                <td>Censored</td>
                <td className="mono">{result.control_censored}</td>
                <td className="mono">{result.treatment_censored}</td>
              </tr>
            </tbody>
          </table>
          </div>

          <div className="stats-explanation" style={{ marginTop: '20px' }}>
            <div className="stats-card">
              <div className="stats-card-label">Hazard Ratio</div>
              <div className="stats-card-value">
                {result.hazard_ratio.toFixed(3)}
                <span style={{ fontSize: '12px', fontWeight: 400, marginLeft: '8px' }}>
                  [{result.hazard_ratio_ci[0].toFixed(2)} - {result.hazard_ratio_ci[1].toFixed(2)}]
                </span>
              </div>
              <div className="stats-card-explanation">
                {result.hazard_ratio < 1
                  ? 'HR < 1 means treatment reduces the rate of events (protective effect)'
                  : result.hazard_ratio > 1
                    ? 'HR > 1 means treatment increases the rate of events'
                    : 'HR = 1 means no effect on timing'
                }
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Time Difference</div>
              <div className="stats-card-value">
                {result.time_saved !== null
                  ? `${result.time_saved > 0 ? '' : '+'}${Math.abs(result.time_saved).toFixed(1)} units`
                  : 'N/A'
                }
              </div>
              <div className="stats-card-explanation">
                {result.time_saved !== null
                  ? result.time_saved > 0
                    ? `Events occur ${result.time_saved.toFixed(1)} units faster in treatment (${Math.abs(result.time_saved_percent).toFixed(1)}% faster)`
                    : `Events occur ${Math.abs(result.time_saved).toFixed(1)} units slower in treatment (${Math.abs(result.time_saved_percent).toFixed(1)}% slower)`
                  : 'Median time not reached in one or both groups'
                }
              </div>
            </div>
          </div>

          <div className="result-grid" style={{ marginTop: '20px' }}>
            <div className="result-item">
              <div className="result-label">P-Value</div>
              <div className="result-value">{result.p_value.toFixed(4)}</div>
            </div>
            <div className="result-item">
              <div className="result-label">Confidence</div>
              <div className="result-value">{result.confidence}%</div>
            </div>
          </div>

          <div className={`callout ${result.is_significant ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '16px' }}>
            <div className="callout-text markdown-content">
              <ReactMarkdown>{result.recommendation}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TimingCalculator
