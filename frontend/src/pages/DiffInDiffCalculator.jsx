import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import TestTypeSelector from '../components/TestTypeSelector'
import FormField from '../components/FormField'
import { DiffInDiffChart } from '../components/charts'

function DiffInDiffCalculator() {
  const [testType, setTestType] = useState('conversion')
  const [formData, setFormData] = useState({
    control_pre_visitors: 5000,
    control_pre_conversions: 250,
    control_post_visitors: 5000,
    control_post_conversions: 260,
    treatment_pre_visitors: 5000,
    treatment_pre_conversions: 250,
    treatment_post_visitors: 5000,
    treatment_post_conversions: 300,
    control_pre_mean: 50,
    control_pre_std: 20,
    control_post_mean: 52,
    control_post_std: 20,
    treatment_pre_mean: 50,
    treatment_pre_std: 20,
    treatment_post_mean: 58,
    treatment_post_std: 21,
    confidence: 95,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    const endpoint = testType === 'conversion'
      ? '/api/conversion/diff-in-diff'
      : '/api/magnitude/diff-in-diff'
    
    const payload = testType === 'conversion'
      ? {
          control_pre_visitors: formData.control_pre_visitors,
          control_pre_conversions: formData.control_pre_conversions,
          control_post_visitors: formData.control_post_visitors,
          control_post_conversions: formData.control_post_conversions,
          treatment_pre_visitors: formData.treatment_pre_visitors,
          treatment_pre_conversions: formData.treatment_pre_conversions,
          treatment_post_visitors: formData.treatment_post_visitors,
          treatment_post_conversions: formData.treatment_post_conversions,
          confidence: formData.confidence,
        }
      : {
          control_pre_n: formData.control_pre_visitors,
          control_pre_mean: formData.control_pre_mean,
          control_pre_std: formData.control_pre_std,
          control_post_n: formData.control_post_visitors,
          control_post_mean: formData.control_post_mean,
          control_post_std: formData.control_post_std,
          treatment_pre_n: formData.treatment_pre_visitors,
          treatment_pre_mean: formData.treatment_pre_mean,
          treatment_pre_std: formData.treatment_pre_std,
          treatment_post_n: formData.treatment_post_visitors,
          treatment_post_mean: formData.treatment_post_mean,
          treatment_post_std: formData.treatment_post_std,
          confidence: formData.confidence,
        }
    
    try {
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
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const controlPreRate = formData.control_pre_conversions / formData.control_pre_visitors
  const controlPostRate = formData.control_post_conversions / formData.control_post_visitors
  const treatmentPreRate = formData.treatment_pre_conversions / formData.treatment_pre_visitors
  const treatmentPostRate = formData.treatment_post_conversions / formData.treatment_post_visitors

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Difference-in-Differences</h1>
        <p className="page-description">
          Measure causal impact by comparing changes over time between treatment and control groups.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">🔬</span>
        <div className="info-box-content">
          <div className="info-box-title">When to use Difference-in-Differences?</div>
          <div className="info-box-text">
            Use DiD when you can't run a traditional A/B test. It compares how the treatment group changed 
            relative to the control group over time. Perfect for measuring the impact of policy changes, 
            feature launches to specific regions, or before/after analyses.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">What are you measuring?</div>
        <TestTypeSelector value={testType} onChange={(val) => { setTestType(val); setResult(null); setError(null); }} />
      </div>

      <form onSubmit={handleSubmit}>
        <div className="period-grid">
          <div className="period-card">
            <div className="period-title">Control Group</div>
            <div style={{ marginBottom: '16px' }}>
              <div className="card-title" style={{ fontSize: '11px', marginBottom: '12px' }}>Pre-Period (Before Treatment)</div>
              {testType === 'conversion' ? (
                <div className="form-grid">
                  <FormField label="Visitors">
                    <input
                      type="number"
                      name="control_pre_visitors"
                      className="form-input"
                      value={formData.control_pre_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Conversions">
                    <input
                      type="number"
                      name="control_pre_conversions"
                      className="form-input"
                      value={formData.control_pre_conversions}
                      onChange={handleChange}
                      min="0"
                    />
                  </FormField>
                </div>
              ) : (
                <div className="form-grid">
                  <FormField label="Sample Size">
                    <input
                      type="number"
                      name="control_pre_visitors"
                      className="form-input"
                      value={formData.control_pre_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Mean">
                    <input
                      type="number"
                      name="control_pre_mean"
                      className="form-input"
                      value={formData.control_pre_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                  <FormField label="Std Dev">
                    <input
                      type="number"
                      name="control_pre_std"
                      className="form-input"
                      value={formData.control_pre_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              )}
            </div>
            
            <div>
              <div className="card-title" style={{ fontSize: '11px', marginBottom: '12px' }}>Post-Period (After Treatment)</div>
              {testType === 'conversion' ? (
                <div className="form-grid">
                  <FormField label="Visitors">
                    <input
                      type="number"
                      name="control_post_visitors"
                      className="form-input"
                      value={formData.control_post_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Conversions">
                    <input
                      type="number"
                      name="control_post_conversions"
                      className="form-input"
                      value={formData.control_post_conversions}
                      onChange={handleChange}
                      min="0"
                    />
                  </FormField>
                </div>
              ) : (
                <div className="form-grid">
                  <FormField label="Sample Size">
                    <input
                      type="number"
                      name="control_post_visitors"
                      className="form-input"
                      value={formData.control_post_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Mean">
                    <input
                      type="number"
                      name="control_post_mean"
                      className="form-input"
                      value={formData.control_post_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                  <FormField label="Std Dev">
                    <input
                      type="number"
                      name="control_post_std"
                      className="form-input"
                      value={formData.control_post_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              )}
            </div>

            {testType === 'conversion' && (
              <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Change: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
                  {(controlPreRate * 100).toFixed(2)}% → {(controlPostRate * 100).toFixed(2)}%
                  <span style={{ color: controlPostRate > controlPreRate ? 'var(--pastel-green-text)' : 'var(--pastel-red-text)', marginLeft: '8px' }}>
                    ({((controlPostRate - controlPreRate) * 100).toFixed(2)}pp)
                  </span>
                </span>
              </div>
            )}
          </div>

          <div className="period-card">
            <div className="period-title">Treatment Group</div>
            <div style={{ marginBottom: '16px' }}>
              <div className="card-title" style={{ fontSize: '11px', marginBottom: '12px' }}>Pre-Period (Before Treatment)</div>
              {testType === 'conversion' ? (
                <div className="form-grid">
                  <FormField label="Visitors">
                    <input
                      type="number"
                      name="treatment_pre_visitors"
                      className="form-input"
                      value={formData.treatment_pre_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Conversions">
                    <input
                      type="number"
                      name="treatment_pre_conversions"
                      className="form-input"
                      value={formData.treatment_pre_conversions}
                      onChange={handleChange}
                      min="0"
                    />
                  </FormField>
                </div>
              ) : (
                <div className="form-grid">
                  <FormField label="Sample Size">
                    <input
                      type="number"
                      name="treatment_pre_visitors"
                      className="form-input"
                      value={formData.treatment_pre_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Mean">
                    <input
                      type="number"
                      name="treatment_pre_mean"
                      className="form-input"
                      value={formData.treatment_pre_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                  <FormField label="Std Dev">
                    <input
                      type="number"
                      name="treatment_pre_std"
                      className="form-input"
                      value={formData.treatment_pre_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              )}
            </div>
            
            <div>
              <div className="card-title" style={{ fontSize: '11px', marginBottom: '12px' }}>Post-Period (After Treatment)</div>
              {testType === 'conversion' ? (
                <div className="form-grid">
                  <FormField label="Visitors">
                    <input
                      type="number"
                      name="treatment_post_visitors"
                      className="form-input"
                      value={formData.treatment_post_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Conversions">
                    <input
                      type="number"
                      name="treatment_post_conversions"
                      className="form-input"
                      value={formData.treatment_post_conversions}
                      onChange={handleChange}
                      min="0"
                    />
                  </FormField>
                </div>
              ) : (
                <div className="form-grid">
                  <FormField label="Sample Size">
                    <input
                      type="number"
                      name="treatment_post_visitors"
                      className="form-input"
                      value={formData.treatment_post_visitors}
                      onChange={handleChange}
                      min="1"
                    />
                  </FormField>
                  <FormField label="Mean">
                    <input
                      type="number"
                      name="treatment_post_mean"
                      className="form-input"
                      value={formData.treatment_post_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                  <FormField label="Std Dev">
                    <input
                      type="number"
                      name="treatment_post_std"
                      className="form-input"
                      value={formData.treatment_post_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              )}
            </div>

            {testType === 'conversion' && (
              <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Change: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
                  {(treatmentPreRate * 100).toFixed(2)}% → {(treatmentPostRate * 100).toFixed(2)}%
                  <span style={{ color: treatmentPostRate > treatmentPreRate ? 'var(--pastel-green-text)' : 'var(--pastel-red-text)', marginLeft: '8px' }}>
                    ({((treatmentPostRate - treatmentPreRate) * 100).toFixed(2)}pp)
                  </span>
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="card" style={{ marginTop: '16px' }}>
          <FormField 
            label="Confidence Level" 
            hint="Higher confidence = stricter threshold for significance"
          >
            <select
              name="confidence"
              className="form-select"
              value={formData.confidence}
              onChange={handleChange}
              style={{ maxWidth: '200px' }}
            >
              <option value={90}>90%</option>
              <option value={95}>95%</option>
              <option value={99}>99%</option>
            </select>
          </FormField>
          <div style={{ marginTop: '16px' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Analyzing...' : 'Calculate DiD Effect'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? 'tag-green' : 'tag-yellow'}`}>
              {result.is_significant 
                ? '✓ Significant Treatment Effect'
                : '○ No Significant Effect'
              }
            </span>
            <span style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              {result.diff_in_diff > 0 ? '+' : ''}
              {testType === 'conversion' 
                ? `${(result.diff_in_diff * 100).toFixed(2)}pp`
                : `$${result.diff_in_diff.toFixed(2)}`
              }
            </span>
          </div>

          <DiffInDiffChart
            controlPre={testType === 'conversion' ? result.control_pre_rate : result.control_pre_mean}
            controlPost={testType === 'conversion' ? result.control_post_rate : result.control_post_mean}
            treatmentPre={testType === 'conversion' ? result.treatment_pre_rate : result.treatment_pre_mean}
            treatmentPost={testType === 'conversion' ? result.treatment_post_rate : result.treatment_post_mean}
            isConversion={testType === 'conversion'}
            diffInDiff={result.diff_in_diff}
          />

          <div className="card-title">How the groups changed</div>
          <div className="summary-table-wrapper">
          <table className="summary-table">
            <thead>
              <tr>
                <th>Group</th>
                <th>Pre-Period</th>
                <th>Post-Period</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Control</td>
                <td className="mono">
                  {testType === 'conversion'
                    ? `${(result.control_pre_rate * 100).toFixed(2)}%`
                    : `$${result.control_pre_mean.toFixed(2)}`
                  }
                </td>
                <td className="mono">
                  {testType === 'conversion'
                    ? `${(result.control_post_rate * 100).toFixed(2)}%`
                    : `$${result.control_post_mean.toFixed(2)}`
                  }
                </td>
                <td className="mono">
                  {testType === 'conversion'
                    ? `${(result.control_change * 100).toFixed(2)}pp`
                    : `$${result.control_change.toFixed(2)}`
                  }
                </td>
              </tr>
              <tr>
                <td>Treatment</td>
                <td className="mono">
                  {testType === 'conversion'
                    ? `${(result.treatment_pre_rate * 100).toFixed(2)}%`
                    : `$${result.treatment_pre_mean.toFixed(2)}`
                  }
                </td>
                <td className="mono">
                  {testType === 'conversion'
                    ? `${(result.treatment_post_rate * 100).toFixed(2)}%`
                    : `$${result.treatment_post_mean.toFixed(2)}`
                  }
                </td>
                <td className="mono" style={{ fontWeight: 600 }}>
                  {testType === 'conversion'
                    ? `${(result.treatment_change * 100).toFixed(2)}pp`
                    : `$${result.treatment_change.toFixed(2)}`
                  }
                </td>
              </tr>
            </tbody>
          </table>
          </div>

          <div className="stats-explanation" style={{ marginTop: '20px' }}>
            <div className="stats-card">
              <div className="stats-card-label">Difference-in-Differences</div>
              <div className="stats-card-value">
                {result.diff_in_diff > 0 ? '+' : ''}
                {testType === 'conversion'
                  ? `${(result.diff_in_diff * 100).toFixed(2)}pp`
                  : `$${result.diff_in_diff.toFixed(2)}`
                }
                <span style={{ fontSize: '14px', fontWeight: 400, marginLeft: '8px' }}>
                  ({result.diff_in_diff_percent > 0 ? '+' : ''}{result.diff_in_diff_percent.toFixed(1)}%)
                </span>
              </div>
              <div className="stats-card-explanation">
                The treatment group changed by {testType === 'conversion'
                  ? `${Math.abs(result.diff_in_diff * 100).toFixed(2)}pp`
                  : `$${Math.abs(result.diff_in_diff).toFixed(2)}`
                } {result.diff_in_diff > 0 ? 'more' : 'less'} than the control group.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">P-Value</div>
              <div className="stats-card-value">{result.p_value.toFixed(4)}</div>
              <div className="stats-card-explanation">
                {result.is_significant 
                  ? `The effect is statistically significant at the ${result.confidence}% confidence level.`
                  : `The effect is not statistically significant. The observed difference could be due to chance.`
                }
              </div>
            </div>
          </div>

          <div className="result-grid" style={{ marginTop: '20px' }}>
            <div className="result-item">
              <div className="result-label">{testType === 'conversion' ? 'Z-Statistic' : 'T-Statistic'}</div>
              <div className="result-value">{(result.z_statistic || result.t_statistic).toFixed(2)}</div>
            </div>
            <div className="result-item">
              <div className="result-label">Confidence</div>
              <div className="result-value">{result.confidence}%</div>
            </div>
            <div className="result-item">
              <div className="result-label">CI Lower</div>
              <div className="result-value">
                {testType === 'conversion'
                  ? `${(result.confidence_interval[0] * 100).toFixed(2)}pp`
                  : `$${result.confidence_interval[0].toFixed(2)}`
                }
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">CI Upper</div>
              <div className="result-value">
                {testType === 'conversion'
                  ? `${(result.confidence_interval[1] * 100).toFixed(2)}pp`
                  : `$${result.confidence_interval[1].toFixed(2)}`
                }
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
    </div>
  )
}

export default DiffInDiffCalculator
