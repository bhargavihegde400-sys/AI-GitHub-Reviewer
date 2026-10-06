import { useState } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const analyzeRepository = async () => {
    if (!url.trim()) {
      setError('Please enter a GitHub repository URL.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed')
      }

      setResult(data)
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    } finally {
      setLoading(false)
    }
  }

  const parseReview = (review) => {
  if (!review) {
    return {
      quality: 'No review available.',
      issues: [],
      suggestions: [],
      patterns: 'No information available.',
      skill: 'No information available.',
      score: 'N/A',
    }
  }

  try {
    const data = typeof review === 'string' ? JSON.parse(review) : review

    return {
      quality: data.code_quality || 'No information available.',
      issues: Array.isArray(data.issues) ? data.issues : [],
      suggestions: Array.isArray(data.suggestions) ? data.suggestions : [],
      patterns: data.design_patterns || 'No information available.',
      skill: data.developer_skill || 'No information available.',
      score: data.code_quality_score ?? 'N/A',
    }
  } catch (error) {
    return {
      quality: 'Unable to read AI review.',
      issues: [],
      suggestions: [],
      patterns: 'Unable to read AI review.',
      skill: 'Unable to read AI review.',
      score: 'N/A',
    }
  }
}
  const review = result ? parseReview(result.ai_review) : null

  return (
    <div className="app">
      <header className="header">
        <h1>AI GitHub Reviewer</h1>
        <p>Analyze GitHub repositories with AI</p>
      </header>

      <main>
        <section className="hero">
          <h2>Understand any GitHub project</h2>
          <p>
            Get technology detection, code quality analysis, design patterns,
            suggestions, and developer skill estimation.
          </p>

          <div className="search-box">
            <input
              type="text"
              placeholder="Paste GitHub repository URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />

            <button onClick={analyzeRepository} disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze Repository'}
            </button>
          </div>

          {error && <p className="error">{error}</p>}
        </section>

        {result && review && (
          <section className="results">
            <h2>{result.name}</h2>

            <p className="description">
              {result.description || 'No repository description available.'}
            </p>

            <div className="stats">
              <div>
                <strong>{result.language || 'Unknown'}</strong>
                <span>Language</span>
              </div>

              <div>
                <strong>{result.stars}</strong>
                <span>Stars</span>
              </div>

              <div>
                <strong>{result.forks}</strong>
                <span>Forks</span>
              </div>

              <div>
                <strong>{result.total_files}</strong>
                <span>Files</span>
              </div>
            </div>

            <div className="card">
              <h3>Technologies</h3>

              <div className="tags">
                {result.technologies?.map((tech) => (
                  <span key={tech}>{tech}</span>
                ))}
              </div>
            </div>
            <div className="card">
              <h3>README</h3>
              <p>
                <strong>Status:</strong> {result.readme_status}
              </p>

              {result.generated_readme ? (
                <>
                  <h4>AI Generated README</h4>
                  <pre className="readme-preview">
                    {result.generated_readme}
                  </pre>
                </>
              ) : (
                <>
                  <h4>README Preview</h4>
                  <pre className="readme-preview">
                    {result.readme_preview || 'No README available.'}
                  </pre>
                </>
              )}
            </div>

            <div className="score-card"><strong>{review.score}</strong><span>/ 100</span><p>Code Quality Score</p></div>

            <div className="review-grid">
              <div className="review-card">
                <h3>Code Quality</h3>
                <p>{review.quality}</p>
              </div>

              <div className="review-card">
                <h3>Developer Skill</h3>
                <p>{review.skill}</p>
              </div>

              <div className="review-card">
                <h3>Issues</h3>

                {review.issues.length > 0 ? (
                  <ul>
                    {review.issues.map((issue, index) => (
                      <li key={index}>{issue}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No major issues identified.</p>
                )}
              </div>

              <div className="review-card">
                <h3>Suggestions</h3>

                {review.suggestions.length > 0 ? (
                  <ul>
                    {review.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No suggestions available.</p>
                )}
              </div>

              <div className="review-card">
                <h3>Design Patterns</h3>
                <p>{review.patterns}</p>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
