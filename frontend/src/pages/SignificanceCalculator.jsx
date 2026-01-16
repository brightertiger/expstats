import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import TestTypeSelector from '../components/TestTypeSelector'
import FormField from '../components/FormField'
import { CIComparisonChart, DistributionChart } from '../components/charts'

function SignificanceCalculator() {
  const [testType, setTestType] = useState('conversion')
  const [analysisMode, setAnalysisMode] = useState('ab')
  const [formData, setFormData] = useState({
    control_visitors: 10000,
    control_conversions: 500,
    variant_visitors: 10000,
    variant_conversions: 550,
    confidence: 95,
    control_mean: 50,
    control_std: 25,
    variant_mean: 52.5,
    variant_std: 25,
  })
  const [variants, setVariants] = useState([
    { name: 'Control', visitors: 10000, conversions: 500, mean: 50, std: 25 },
    { name: 'Variant A', visitors: 10000, conversions: 550, mean: 52.5, std: 25 },
    { name: 'Variant B', visitors: 10000, conversions: 480, mean: 49, std: 24 },
  ])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }))
  }

  const handleVariantChange = (index, field, value) => {
    setVariants(prev => prev.map((v, i) => 
      i === index ? { ...v, [field]: field === 'name' ? value : parseFloat(value) || 0 } : v
    ))
  }

  const addVariant = () => {
    const letter = String.fromCharCode(65 + variants.length - 1)
    setVariants(prev => [...prev, { 
      name: `Variant ${letter}`, 
      visitors: 10000, 
      conversions: 500, 
      mean: 50, 
      std: 25 
    }])
  }

  const removeVariant = (index) => {
    if (variants.length > 2) {
      setVariants(prev => prev.filter((_, i) => i !== index))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    let endpoint, payload

    if (analysisMode === 'ab') {
      endpoint = testType === 'conversion' 
        ? '/api/conversion/analyze'
        : '/api/magnitude/analyze'
      
      payload = testType === 'conversion'
        ? {
            control_visitors: formData.control_visitors,
            control_conversions: formData.control_conversions,
            variant_visitors: formData.variant_visitors,
            variant_conversions: formData.variant_conversions,
            confidence: formData.confidence,
          }
        : {
            control_visitors: formData.control_visitors,
            control_mean: formData.control_mean,
            control_std: formData.control_std,
            variant_visitors: formData.variant_visitors,
            variant_mean: formData.variant_mean,
            variant_std: formData.variant_std,
            confidence: formData.confidence,
          }
    } else {
      endpoint = testType === 'conversion'
        ? '/api/conversion/analyze-multi'
        : '/api/magnitude/analyze-multi'
      
      payload = testType === 'conversion'
        ? {
            variants: variants.map(v => ({
              name: v.name,
              visitors: v.visitors,
              conversions: v.conversions,
            })),
            confidence: formData.confidence,
            correction: 'bonferroni',
          }
        : {
            variants: variants.map(v => ({
              name: v.name,
              visitors: v.visitors,
              mean: v.mean,
              std: v.std,
            })),
            confidence: formData.confidence,
            correction: 'bonferroni',
          }
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
      setResult({ ...data, mode: analysisMode })
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
        <h1 className="page-title">Analyze Results</h1>
        <p className="page-description">
          Check if your A/B test has a statistically significant winner.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">📊</span>
        <div className="info-box-content">
          <div className="info-box-title">What is statistical significance?</div>
          <div className="info-box-text">
            Statistical significance tells you whether the difference you observe is real or just due to random chance.
            A "significant" result means you can confidently say the variant performs differently from the control.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">What are you measuring?</div>
        <TestTypeSelector value={testType} onChange={(val) => { setTestType(val); setResult(null); setError(null); }} />
      </div>

      <div className="card">
        <div className="card-title">Analysis Type</div>
        <div className="tabs">
          <button 
            type="button"
            className={`tab ${analysisMode === 'ab' ? 'active' : ''}`}
            onClick={() => { setAnalysisMode('ab'); setResult(null); }}
          >
            A/B Test (2 variants)
          </button>
          <button 
            type="button"
            className={`tab ${analysisMode === 'multi' ? 'active' : ''}`}
            onClick={() => { setAnalysisMode('multi'); setResult(null); }}
          >
            Multi-Variant (3+ variants)
          </button>
        </div>
        <div className="form-hint" style={{ marginTop: '-8px' }}>
          {analysisMode === 'ab' 
            ? 'Compare one variant against a control group'
            : 'Compare multiple variants at once with automatic correction for multiple comparisons'
          }
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {analysisMode === 'ab' ? (
          testType === 'conversion' ? (
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control</span>
                </div>
                <FormField label="Visitors" hint="Number of users who saw the control">
                  <input
                    type="number"
                    name="control_visitors"
                    className="form-input"
                    value={formData.control_visitors}
                    onChange={handleChange}
                    min="1"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Conversions" hint="Number of users who converted">
                    <input
                      type="number"
                      name="control_conversions"
                      className="form-input"
                      value={formData.control_conversions}
                      onChange={handleChange}
                      min="0"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Conversion Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{(controlRate * 100).toFixed(2)}%</span>
                </div>
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Variant</span>
                </div>
                <FormField label="Visitors" hint="Number of users who saw the variant">
                  <input
                    type="number"
                    name="variant_visitors"
                    className="form-input"
                    value={formData.variant_visitors}
                    onChange={handleChange}
                    min="1"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Conversions" hint="Number of users who converted">
                    <input
                      type="number"
                      name="variant_conversions"
                      className="form-input"
                      value={formData.variant_conversions}
                      onChange={handleChange}
                      min="0"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Conversion Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{(variantRate * 100).toFixed(2)}%</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control</span>
                </div>
                <FormField label="Sample Size" hint="Number of observations">
                  <input
                    type="number"
                    name="control_visitors"
                    className="form-input"
                    value={formData.control_visitors}
                    onChange={handleChange}
                    min="2"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Mean" hint="Average value (e.g., avg order value)">
                    <input
                      type="number"
                      name="control_mean"
                      className="form-input"
                      value={formData.control_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Standard Deviation" hint="Spread of the data">
                    <input
                      type="number"
                      name="control_std"
                      className="form-input"
                      value={formData.control_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Variant</span>
                </div>
                <FormField label="Sample Size" hint="Number of observations">
                  <input
                    type="number"
                    name="variant_visitors"
                    className="form-input"
                    value={formData.variant_visitors}
                    onChange={handleChange}
                    min="2"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Mean" hint="Average value (e.g., avg order value)">
                    <input
                      type="number"
                      name="variant_mean"
                      className="form-input"
                      value={formData.variant_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Standard Deviation" hint="Spread of the data">
                    <input
                      type="number"
                      name="variant_std"
                      className="form-input"
                      value={formData.variant_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              </div>
            </div>
          )
        ) : (
          <div className="card">
            <div className="card-title">Variant Data</div>
            <div className="variant-list">
              {variants.map((variant, index) => (
                <div key={index} className="variant-row">
                  <FormField label={index === 0 ? 'Name' : ''}>
                    <input
                      type="text"
                      className="form-input variant-name-input"
                      value={variant.name}
                      onChange={(e) => handleVariantChange(index, 'name', e.target.value)}
                      placeholder="Variant name"
                    />
                  </FormField>
                  <FormField label={index === 0 ? 'Visitors' : ''}>
                    <input
                      type="number"
                      className="form-input"
                      value={variant.visitors}
                      onChange={(e) => handleVariantChange(index, 'visitors', e.target.value)}
                      min="1"
                    />
                  </FormField>
                  {testType === 'conversion' ? (
                    <FormField label={index === 0 ? 'Conversions' : ''}>
                      <input
                        type="number"
                        className="form-input"
                        value={variant.conversions}
                        onChange={(e) => handleVariantChange(index, 'conversions', e.target.value)}
                        min="0"
                      />
                    </FormField>
                  ) : (
                    <>
                      <FormField label={index === 0 ? 'Mean' : ''}>
                        <input
                          type="number"
                          className="form-input"
                          value={variant.mean}
                          onChange={(e) => handleVariantChange(index, 'mean', e.target.value)}
                          step="any"
                        />
                      </FormField>
                      <FormField label={index === 0 ? 'Std Dev' : ''}>
                        <input
                          type="number"
                          className="form-input"
                          value={variant.std}
                          onChange={(e) => handleVariantChange(index, 'std', e.target.value)}
                          step="any"
                          min="0"
                        />
                      </FormField>
                    </>
                  )}
                  <div style={{ paddingBottom: index === 0 ? '0' : '0' }}>
                    <button
                      type="button"
                      className="remove-variant-btn"
                      onClick={() => removeVariant(index)}
                      disabled={variants.length <= 2}
                      title={variants.length <= 2 ? 'Minimum 2 variants required' : 'Remove variant'}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="add-variant-btn" onClick={addVariant}>
              <span>+</span> Add Variant
            </button>
          </div>
        )}

        <div className="card" style={{ marginTop: '16px' }}>
          <FormField 
            label="Confidence Level" 
            hint="Higher confidence = stricter threshold. 95% is industry standard."
          >
            <select
              name="confidence"
              className="form-select"
              value={formData.confidence}
              onChange={handleChange}
              style={{ maxWidth: '200px' }}
            >
              <option value={90}>90% (α = 0.10)</option>
              <option value={95}>95% (α = 0.05)</option>
              <option value={99}>99% (α = 0.01)</option>
            </select>
          </FormField>
          <div style={{ marginTop: '16px' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze Results'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && result.mode === 'ab' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? (result.winner === 'variant' ? 'tag-green' : 'tag-red') : 'tag-yellow'}`}>
              {result.is_significant 
                ? (result.winner === 'variant' ? '✓ Variant Wins' : '✓ Control Wins')
                : '○ Not Significant'
              }
            </span>
            <span style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              {result.lift_percent > 0 ? '+' : ''}{result.lift_percent.toFixed(2)}%
            </span>
          </div>

          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Control</div>
              <div className="result-value">
                {testType === 'conversion' 
                  ? `${(result.control_rate * 100).toFixed(2)}%`
                  : `$${result.control_mean.toFixed(2)}`
                }
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Variant</div>
              <div className="result-value">
                {testType === 'conversion' 
                  ? `${(result.variant_rate * 100).toFixed(2)}%`
                  : `$${result.variant_mean.toFixed(2)}`
                }
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">P-Value</div>
              <div className="result-value">{result.p_value < 0.0001 ? '<0.0001' : result.p_value.toFixed(4)}</div>
            </div>
            <div className="result-item">
              <div className="result-label">Confidence</div>
              <div className="result-value">{result.confidence}%</div>
            </div>
          </div>

          <CIComparisonChart
            controlValue={testType === 'conversion' ? result.control_rate : result.control_mean}
            variantValue={testType === 'conversion' ? result.variant_rate : result.variant_mean}
            controlCI={result.control_ci}
            variantCI={result.variant_ci}
            label={testType === 'conversion' ? 'Conversion Rate' : 'Average Value'}
            formatValue={(v) => testType === 'conversion' ? `${(v * 100).toFixed(2)}%` : `$${v.toFixed(2)}`}
            isConversion={testType === 'conversion'}
          />

          <DistributionChart
            controlMean={testType === 'conversion' ? result.control_rate : result.control_mean}
            variantMean={testType === 'conversion' ? result.variant_rate : result.variant_mean}
            controlStd={testType === 'conversion' ? null : formData.control_std}
            variantStd={testType === 'conversion' ? null : formData.variant_std}
            controlN={formData.control_visitors}
            variantN={formData.variant_visitors}
            isConversion={testType === 'conversion'}
          />

          <div className="stats-explanation">
            <div className="stats-card">
              <div className="stats-card-label">P-Value Explained</div>
              <div className="stats-card-value">{result.p_value < 0.0001 ? '<0.01%' : `${(result.p_value * 100).toFixed(2)}%`}</div>
              <div className="stats-card-explanation">
                {result.p_value < 0.05 
                  ? `There's only a ${(result.p_value * 100).toFixed(2)}% chance this result is due to random chance.`
                  : `There's a ${(result.p_value * 100).toFixed(1)}% chance this result is due to random chance—too high to be confident.`
                }
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Confidence Interval</div>
              <div className="stats-card-value">
                [{testType === 'conversion' 
                  ? `${(result.confidence_interval[0] * 100).toFixed(2)}%, ${(result.confidence_interval[1] * 100).toFixed(2)}%`
                  : `$${result.confidence_interval[0].toFixed(2)}, $${result.confidence_interval[1].toFixed(2)}`
                }]
              </div>
              <div className="stats-card-explanation">
                The true difference likely falls within this range with {result.confidence}% confidence.
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

      {result && result.mode === 'multi' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? 'tag-green' : 'tag-yellow'}`}>
              {result.is_significant 
                ? '✓ Significant Differences Found'
                : '○ No Significant Differences'
              }
            </span>
            {result.is_significant && (
              <span style={{ fontSize: '16px', fontWeight: 500 }}>
                Best: <strong>{result.best_variant}</strong>
              </span>
            )}
          </div>

          <div className="card-title">Variant Performance</div>
          <div className="summary-table-wrapper">
          <table className="summary-table">
            <thead>
              <tr>
                <th>Variant</th>
                <th>Visitors</th>
                <th>{testType === 'conversion' ? 'Conversions' : 'Mean'}</th>
                <th>{testType === 'conversion' ? 'Rate' : 'Std Dev'}</th>
              </tr>
            </thead>
            <tbody>
              {result.variants
                .sort((a, b) => testType === 'conversion' ? b.rate - a.rate : b.mean - a.mean)
                .map((v, i) => (
                  <tr key={v.name}>
                    <td>
                      {v.name}
                      {v.name === result.best_variant && <span style={{ marginLeft: '8px' }}>🏆</span>}
                    </td>
                    <td className="mono">{v.visitors.toLocaleString()}</td>
                    <td className="mono">
                      {testType === 'conversion' 
                        ? v.conversions.toLocaleString()
                        : `$${v.mean.toFixed(2)}`
                      }
                    </td>
                    <td className="mono">
                      {testType === 'conversion' 
                        ? `${(v.rate * 100).toFixed(2)}%`
                        : `$${v.std.toFixed(2)}`
                      }
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
          </div>

          {result.pairwise_comparisons.filter(p => p.is_significant).length > 0 && (
            <>
              <div className="card-title" style={{ marginTop: '24px' }}>Significant Pairwise Comparisons</div>
              <div className="summary-table-wrapper">
              <table className="summary-table">
                <thead>
                  <tr>
                    <th>Comparison</th>
                    <th>Lift</th>
                    <th>P-Value (adjusted)</th>
                  </tr>
                </thead>
                <tbody>
                  {result.pairwise_comparisons
                    .filter(p => p.is_significant)
                    .map((p, i) => {
                      const winner = p.lift_percent > 0 ? p.variant_b : p.variant_a
                      const loser = p.lift_percent > 0 ? p.variant_a : p.variant_b
                      return (
                        <tr key={i}>
                          <td><strong>{winner}</strong> beats {loser}</td>
                          <td className="mono">{Math.abs(p.lift_percent).toFixed(2)}%</td>
                          <td className="mono">{p.p_value_adjusted.toFixed(4)}</td>
                        </tr>
                      )
                    })}
                </tbody>
              </table>
              </div>
            </>
          )}

          <div className="stats-explanation" style={{ marginTop: '20px' }}>
            <div className="stats-card">
              <div className="stats-card-label">Overall Test P-Value</div>
              <div className="stats-card-value">{result.p_value.toFixed(4)}</div>
              <div className="stats-card-explanation">
                {testType === 'conversion' ? 'Chi-square test' : 'ANOVA'} for overall differences between variants.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Multiple Comparison Correction</div>
              <div className="stats-card-value">Bonferroni</div>
              <div className="stats-card-explanation">
                P-values are adjusted to prevent false positives when making multiple comparisons.
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

export default SignificanceCalculator
