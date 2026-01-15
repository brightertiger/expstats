import { useState } from 'react'

function SignificanceCalculator() {
  const [testType, setTestType] = useState('binary')
  const [formData, setFormData] = useState({
    control_visitors: 10000,
    control_conversions: 500,
    variant_visitors: 10000,
    variant_conversions: 550,
    confidence: 95,
    test_name: 'Homepage Button Test',
    control_mean: 50,
    control_std: 25,
    variant_mean: 52.5,
    variant_std: 25,
    metric_name: 'Average Order Value',
    currency: '$',
  })
  const [result, setResult] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    const endpoint = testType === 'binary' 
      ? '/api/binary/analyze'
      : '/api/continuous/analyze'
    
    const summaryEndpoint = testType === 'binary'
      ? '/api/binary/analyze/summary'
      : '/api/continuous/analyze/summary'
    
    const payload = testType === 'binary'
      ? {
          control_visitors: formData.control_visitors,
          control_conversions: formData.control_conversions,
          variant_visitors: formData.variant_visitors,
          variant_conversions: formData.variant_conversions,
          confidence: formData.confidence,
          test_name: formData.test_name,
        }
      : {
          control_visitors: formData.control_visitors,
          control_mean: formData.control_mean,
          control_std: formData.control_std,
          variant_visitors: formData.variant_visitors,
          variant_mean: formData.variant_mean,
          variant_std: formData.variant_std,
          confidence: formData.confidence,
          test_name: formData.test_name,
          metric_name: formData.metric_name,
          currency: formData.currency,
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
        throw new Error(data.detail || 'Analysis failed')
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

  const controlRate = formData.control_conversions / formData.control_visitors
  const variantRate = formData.variant_conversions / formData.variant_visitors

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analyze Test Results</h1>
        <p className="page-description">
          Enter your A/B test data to see if there's a statistically significant winner.
        </p>
      </div>

      <div className="card">
        <div className="card-title">What did you test?</div>
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
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">Test Name</div>
          <div className="form-group" style={{ maxWidth: '400px' }}>
            <input
              type="text"
              name="test_name"
              className="form-input"
              value={formData.test_name}
              onChange={handleChange}
              placeholder="e.g., Homepage Button Test"
            />
            <span className="form-hint">For your summary report</span>
          </div>
        </div>

        {testType === 'binary' ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div className="card">
              <div className="card-title">🔵 Control (Original)</div>
              <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
                <div className="form-group">
                  <label className="form-label">Total Visitors</label>
                  <input
                    type="number"
                    name="control_visitors"
                    className="form-input"
                    value={formData.control_visitors}
                    onChange={handleChange}
                    min="1"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Conversions</label>
                  <input
                    type="number"
                    name="control_conversions"
                    className="form-input"
                    value={formData.control_conversions}
                    onChange={handleChange}
                    min="0"
                  />
                </div>
                <div style={{ 
                  padding: '1rem', 
                  background: 'var(--bg-tertiary)', 
                  borderRadius: 'var(--radius-md)',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                    Conversion Rate
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    {(controlRate * 100).toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-title">🟢 Variant (New Version)</div>
              <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
                <div className="form-group">
                  <label className="form-label">Total Visitors</label>
                  <input
                    type="number"
                    name="variant_visitors"
                    className="form-input"
                    value={formData.variant_visitors}
                    onChange={handleChange}
                    min="1"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Conversions</label>
                  <input
                    type="number"
                    name="variant_conversions"
                    className="form-input"
                    value={formData.variant_conversions}
                    onChange={handleChange}
                    min="0"
                  />
                </div>
                <div style={{ 
                  padding: '1rem', 
                  background: 'var(--bg-tertiary)', 
                  borderRadius: 'var(--radius-md)',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                    Conversion Rate
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    {(variantRate * 100).toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="card">
              <div className="card-title">Metric Settings</div>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Metric Name</label>
                  <input
                    type="text"
                    name="metric_name"
                    className="form-input"
                    value={formData.metric_name}
                    onChange={handleChange}
                    placeholder="e.g., Average Order Value"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Currency Symbol</label>
                  <input
                    type="text"
                    name="currency"
                    className="form-input"
                    value={formData.currency}
                    onChange={handleChange}
                    style={{ maxWidth: '100px' }}
                  />
                </div>
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div className="card">
                <div className="card-title">🔵 Control (Original)</div>
                <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
                  <div className="form-group">
                    <label className="form-label">Sample Size</label>
                    <input
                      type="number"
                      name="control_visitors"
                      className="form-input"
                      value={formData.control_visitors}
                      onChange={handleChange}
                      min="2"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Average Value</label>
                    <input
                      type="number"
                      name="control_mean"
                      className="form-input"
                      value={formData.control_mean}
                      onChange={handleChange}
                      step="0.01"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Standard Deviation</label>
                    <input
                      type="number"
                      name="control_std"
                      className="form-input"
                      value={formData.control_std}
                      onChange={handleChange}
                      step="0.01"
                      min="0"
                    />
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-title">🟢 Variant (New Version)</div>
                <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
                  <div className="form-group">
                    <label className="form-label">Sample Size</label>
                    <input
                      type="number"
                      name="variant_visitors"
                      className="form-input"
                      value={formData.variant_visitors}
                      onChange={handleChange}
                      min="2"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Average Value</label>
                    <input
                      type="number"
                      name="variant_mean"
                      className="form-input"
                      value={formData.variant_mean}
                      onChange={handleChange}
                      step="0.01"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Standard Deviation</label>
                    <input
                      type="number"
                      name="variant_std"
                      className="form-input"
                      value={formData.variant_std}
                      onChange={handleChange}
                      step="0.01"
                      min="0"
                    />
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        <div className="card">
          <div className="card-title">Settings</div>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Confidence Level</label>
              <select
                name="confidence"
                className="form-select"
                value={formData.confidence}
                onChange={handleChange}
              >
                <option value={90}>90%</option>
                <option value={95}>95% (recommended)</option>
                <option value={99}>99%</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop: '2rem' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze Results'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && (
        <div className="card results-card">
          <div className="card-title">
            {result.is_significant 
              ? (result.winner === 'variant' ? '🏆 Variant Wins!' : '🏆 Control Wins!')
              : '⏳ No Winner Yet'
            }
          </div>
          
          <div style={{ 
            padding: '1.5rem', 
            background: result.is_significant 
              ? (result.winner === 'variant' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)')
              : 'rgba(245, 158, 11, 0.1)',
            border: `1px solid ${result.is_significant 
              ? (result.winner === 'variant' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)')
              : 'rgba(245, 158, 11, 0.3)'}`,
            borderRadius: 'var(--radius-md)',
            textAlign: 'center',
            marginBottom: '1.5rem'
          }}>
            <div style={{ 
              fontSize: '2rem', 
              fontWeight: 700,
              fontFamily: 'var(--font-mono)',
              color: result.lift_percent > 0 ? 'var(--success)' : 'var(--error)'
            }}>
              {result.lift_percent > 0 ? '+' : ''}{result.lift_percent.toFixed(1)}%
            </div>
            <div style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              lift in {testType === 'binary' ? 'conversion rate' : formData.metric_name.toLowerCase()}
            </div>
          </div>

          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Control</div>
              <div className="result-value">
                {testType === 'binary' 
                  ? `${(result.control_rate * 100).toFixed(2)}%`
                  : `${formData.currency}${result.control_mean.toFixed(2)}`
                }
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Variant</div>
              <div className="result-value">
                {testType === 'binary' 
                  ? `${(result.variant_rate * 100).toFixed(2)}%`
                  : `${formData.currency}${result.variant_mean.toFixed(2)}`
                }
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">P-Value</div>
              <div className={`result-value ${result.p_value < 0.05 ? 'success' : ''}`}>
                {result.p_value < 0.0001 ? '< 0.0001' : result.p_value.toFixed(4)}
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Confidence</div>
              <div className="result-value">{result.confidence}%</div>
            </div>
          </div>

          <div className="interpretation">
            <div className="interpretation-title">Recommendation</div>
            <p className="interpretation-text" style={{ fontSize: '1.1rem' }}>
              {result.recommendation}
            </p>
          </div>

          {summary && (
            <div style={{ marginTop: '2rem' }}>
              <div className="form-label" style={{ marginBottom: '0.5rem' }}>📋 Summary for Stakeholders (copy & paste)</div>
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
              <button 
                className="btn btn-secondary" 
                style={{ marginTop: '0.75rem' }}
                onClick={() => navigator.clipboard.writeText(summary)}
              >
                Copy to Clipboard
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SignificanceCalculator
