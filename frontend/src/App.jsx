import React, { useState } from 'react'
import './styles.css'

export default function App() {
  const [jobUrl, setJobUrl] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [resume, setResume] = useState(null)
  const [log, setLog] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'

  function validateInputs() {
    if (!jobUrl.trim()) {
      setError('Job URL is required')
      return false
    }
    if (!resume) {
      setError('Resume PDF is required')
      return false
    }
    if (!jobUrl.startsWith('http://') && !jobUrl.startsWith('https://')) {
      setError('Job URL must start with http:// or https://')
      return false
    }
    setError('')
    return true
  }

  async function handleSubmit(e) {
    e.preventDefault()
    
    if (!validateInputs()) {
      return
    }

    const fd = new FormData()
    fd.append('job_url', jobUrl.trim())
    fd.append('name', name.trim())
    fd.append('email', email.trim())
    fd.append('phone', phone.trim())
    fd.append('resume', resume)

    setLoading(true)
    setLog(null)
    
    try {
      const res = await fetch(`${BACKEND_URL}/submit`, {
        method: 'POST',
        body: fd,
      })
      
      const json = await res.json()
      
      if (!res.ok) {
        json.error = json.error || `Server error: ${res.status}`
      }
      
      setLog(json)
    } catch (err) {
      setLog({
        job_url: jobUrl,
        status: 'error',
        submitted_at: null,
        notes: [String(err)]
      })
      setError(`Connection error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setJobUrl('')
    setName('')
    setEmail('')
    setPhone('')
    setResume(null)
    setLog(null)
    setError('')
  }

  const isSuccess = log?.status === 'submitted'
  const isFailed = log?.status === 'failed'
  const isError = log?.status === 'error'

  return (
    <div className="container">
      <header className="header">
        <h1>🤖 AI Resume Auto-Submission</h1>
        <p>Automate your job application submissions</p>
      </header>

      <main>
        <form onSubmit={handleSubmit} className="form">
          <fieldset>
            <legend>Job Application Details</legend>
            
            <div className="form-group">
              <label htmlFor="jobUrl">
                Job Posting URL <span className="required">*</span>
              </label>
              <input
                id="jobUrl"
                type="url"
                value={jobUrl}
                onChange={e => setJobUrl(e.target.value)}
                placeholder="https://greenhouse.io/... or https://ashby.com/..."
                disabled={loading}
              />
              <small>Support for Greenhouse, Ashby, and similar ATS platforms</small>
            </div>

            <div className="form-group">
              <label htmlFor="resume">
                Resume PDF <span className="required">*</span>
              </label>
              <input
                id="resume"
                type="file"
                accept="application/pdf"
                onChange={e => setResume(e.target.files[0])}
                disabled={loading}
              />
              {resume && <small className="success">✓ {resume.name}</small>}
            </div>

            <fieldset className="optional-fields">
              <legend>Optional Information</legend>
              
              <div className="form-group">
                <label htmlFor="name">Name</label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Your full name"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="phone">Phone</label>
                <input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="(555) 123-4567"
                  disabled={loading}
                />
              </div>
            </fieldset>
          </fieldset>

          <div className="form-actions">
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? '⏳ Submitting...' : '📤 Submit Application'}
            </button>
            <button type="button" onClick={handleReset} disabled={loading} className="btn-secondary">
              Clear Form
            </button>
          </div>
        </form>

        {error && (
          <div className="alert alert-error">
            <strong>⚠️ Error:</strong> {error}
          </div>
        )}

        {log && (
          <section className="log-section">
            <div className={`log-header ${log.status}`}>
              <h2>
                {isSuccess && '✅ Submission Successful'}
                {isFailed && '❌ Submission Failed'}
                {isError && '⚠️ Error'}
                {!isSuccess && !isFailed && !isError && '📋 Submission Log'}
              </h2>
              {isSuccess && (
                <p className="timestamp">
                  Submitted at: {new Date(log.submitted_at).toLocaleString()}
                </p>
              )}
            </div>
            
            <div className="log-content">
              <div className="log-item">
                <strong>Status:</strong> <span className={`status-${log.status}`}>{log.status.toUpperCase()}</span>
              </div>
              
              {log.submitted_at && (
                <div className="log-item">
                  <strong>Submitted At:</strong> {new Date(log.submitted_at).toLocaleString()}
                </div>
              )}
              
              {log.fields_filled && (
                <div className="log-item">
                  <strong>Fields Filled:</strong>
                  <ul className="fields-list">
                    {Object.entries(log.fields_filled).map(([field, filled]) => (
                      <li key={field}>
                        {filled ? '✓' : '✗'} {field}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {log.notes && log.notes.length > 0 && (
                <div className="log-item">
                  <strong>Execution Log:</strong>
                  <ul className="notes-list">
                    {log.notes.map((note, idx) => (
                      <li key={idx}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {log.error && (
                <div className="log-item error">
                  <strong>Error:</strong> {log.error}
                </div>
              )}
            </div>

            <details className="log-raw">
              <summary>Raw JSON</summary>
              <pre>{JSON.stringify(log, null, 2)}</pre>
            </details>
          </section>
        )}
      </main>

      <footer className="footer">
        <p>Backend: <code>{BACKEND_URL}</code></p>
        <p>⚠️ Note: Automation success depends on website structure. Custom job boards may not be supported.</p>
      </footer>
    </div>
  )
}
