import { useState } from 'react'

function SampleSizeCalculator() {
  const [testType, setTestType] = useState('binary')
  const [formData, setFormData] = useState({
    current_rate: 5,
    lift_percent: 10,
    confidence: 95,
    power: 80,
    daily_visitors: '',
    current_mean: 50,
    current_std: 25,
  })
  const [result, setResult] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value === '' ? '' : parseFloat(value)
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    const endpoint = testType === 'binary' 
      ? '/api/binary/sample-size'
      : '/api/continuous/sample-size'
    
    const summaryEndpoint = testType === 'binary'
      ? '/api/binary/sample-size/summary'
      : '/api/continuous/sample-size/summary'
    
    const payload = testType === 'binary'
      ? {
          current_rate: formData.current_rate,
          lift_percent: formData.lift_percent,
          confidence: formData.confidence,
          power: formData.power,
          daily_visitors: formData.daily_visitors || null,
        }
      : {
          current_mean: formData.current_mean,
          current_std: formData.current_std,
          lift_percent: formData.lift_percent,
          confidence: formData.confidence,
          power: formData.power,
          daily_visitors: formData.daily_visitors || null,
        }
    
    try {
      const [dataRes, summaryRes] = await Promise.all([
        fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }),
        fetch(summaryEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      ])
      
      if (!dataRes.ok) {
        const data = await dataRes.json()
        throw new Error(data.detail || 'Calculation failed')
      }
      
      const data = await dataRes.json()
      const summaryText = await summaryRes.text()
      
      setResult(data)
      setSummary(summaryText)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatNumber = (val) => val?.toLocaleString() || '-'

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Sample Size Calculator</h1>
        <p className="page-description">
          Find out how many visitors you need to run a reliable A/B test.
        </p>
      </div>

      <div className="card">
        <div className="card-title">What are you testing?</div>
        <div className="toggle-group" style={{ maxWidth: '500px' }}>
          <button 
            className={`toggle-option ${testType === 'binary' ? 'active' : ''}`}
            onClick={() => setTestType('binary')}
          >
            Conversion Rate
          </button>
          <button 
            className={`toggle-option ${testType === 'continuous' ? 'active' : ''}`}
            onClick={() => setTestType('continuous')}
          >
            Revenue / Average Value
          </button>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
          {testType === 'binary' 
            ? 'Use this for click-through rates, sign-up rates, purchase rates, etc.' 
            : 'Use this for average order value, revenue per user, time on page, etc.'}
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">Your Current Numbers</div>
          <div className="form-grid">
            {testType === 'binary' ? (
              <div className="form-group">
                <label className="form-label">Current Conversion Rate (%)</label>
                <input
                  type="number"
                  name="current_rate"
                  className="form-input"
                  value={formData.current_rate}
                  onChange={handleChange}
                  step="0.1"
                  min="0.01"
                  max="100"
                  placeholder="e.g., 5 for 5%"
                />
                <span className="form-hint">What % of visitors currently convert?</span>
              </div>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Current Average Value</label>
                  <input
                    type="number"
                    name="current_mean"
                    className="form-input"
                    value={formData.current_mean}
                    onChange={handleChange}
                    step="0.01"
                    placeholder="e.g., 50"
                  />
                  <span className="form-hint">Current AOV, revenue, or metric value</span>
                </div>
                <div className="form-group">
                  <label className="form-label">Standard Deviation</label>
                  <input
                    type="number"
                    name="current_std"
                    className="form-input"
                    value={formData.current_std}
                    onChange={handleChange}
                    step="0.01"
                    min="0.01"
                    placeholder="e.g., 25"
                  />
                  <span className="form-hint">How much does it vary? (ask your analyst)</span>
                </div>
              </>
            )}

            <div className="form-group">
              <label className="form-label">Minimum Lift to Detect (%)</label>
              <input
                type="number"
                name="lift_percent"
                className="form-input"
                value={formData.lift_percent}
                onChange={handleChange}
                step="1"
                min="1"
                placeholder="e.g., 10"
              />
              <span className="form-hint">Smallest improvement worth detecting</span>
            </div>

            <div className="form-group">
              <label className="form-label">Daily Visitors (optional)</label>
              <input
                type="number"
                name="daily_visitors"
                className="form-input"
                value={formData.daily_visitors}
                onChange={handleChange}
                step="100"
                min="1"
                placeholder="e.g., 10000"
              />
              <span className="form-hint">To estimate test duration</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Statistical Settings</div>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Confidence Level</label>
              <select
                name="confidence"
                className="form-select"
                value={formData.confidence}
                onChange={handleChange}
              >
                <option value={90}>90% (faster, less certain)</option>
                <option value={95}>95% (recommended)</option>
                <option value={99}>99% (slower, more certain)</option>
              </select>
              <span className="form-hint">How sure do you want to be?</span>
            </div>

            <div className="form-group">
              <label className="form-label">Statistical Power</label>
              <select
                name="power"
                className="form-select"
                value={formData.power}
                onChange={handleChange}
              >
                <option value={70}>70% (risky)</option>
                <option value={80}>80% (standard)</option>
                <option value={90}>90% (conservative)</option>
              </select>
              <span className="form-hint">Chance of detecting a real effect</span>
            </div>
          </div>

          <div style={{ marginTop: '2rem' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Calculating...' : 'Calculate Sample Size'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && (
        <div className="card results-card">
          <div className="card-title">📊 Results</div>
          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Per Variant</div>
              <div className="result-value">{formatNumber(result.visitors_per_variant)}</div>
              <div className="result-unit">visitors</div>
            </div>
            <div className="result-item">
              <div className="result-label">Total Needed</div>
              <div className="result-value">{formatNumber(result.total_visitors)}</div>
              <div className="result-unit">visitors</div>
            </div>
            {result.test_duration_days && (
              <div className="result-item">
                <div className="result-label">Estimated Duration</div>
                <div className="result-value">
                  {result.test_duration_days < 7 
                    ? `${result.test_duration_days}` 
                    : Math.ceil(result.test_duration_days / 7)}
                </div>
                <div className="result-unit">
                  {result.test_duration_days < 7 ? 'days' : 'weeks'}
                </div>
              </div>
            )}
            <div className="result-item">
              <div className="result-label">Expected Variant</div>
              <div className="result-value">
                {testType === 'binary' 
                  ? `${(result.expected_rate * 100).toFixed(2)}%`
                  : `$${result.expected_mean?.toFixed(2)}`
                }
              </div>
            </div>
          </div>

          {summary && (
            <div style={{ marginTop: '2rem' }}>
              <div className="form-label" style={{ marginBottom: '0.5rem' }}>Summary for Stakeholders</div>
              <pre style={{ 
                background: 'var(--bg-tertiary)', 
                padding: '1.5rem', 
                borderRadius: 'var(--radius-md)',
                fontSize: '0.85rem',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                fontFamily: 'var(--font-mono)',
                overflow: 'auto'
              }}>
                {summary}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SampleSizeCalculator
