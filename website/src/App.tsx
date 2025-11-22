import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { SignInButton, SignUpButton, UserButton, useUser } from '@clerk/clerk-react'
import './App.css'
import { Home } from './components/Home'
import { HowItWorks } from './components/HowItWorks'
import { Features } from './components/Features'
import { About } from './components/About'
import { Dashboard } from './components/Dashboard'
import { agriGuardAPI, formatFileSize, getFileType } from './services/api'
import type { ImageValidationResult, PipelineResult, GradCAMResult } from './services/api'
import { ChatPanel } from './components/ChatComponent.tsx'
import { dashboardStorage } from './services/dashboardStorage'

interface AnalysisState {
  isAnalyzing: boolean;
  validation?: ImageValidationResult;
  pipeline?: PipelineResult;
  error?: string;
  showChat?: boolean;
  gradcam?: GradCAMResult;
}

function NavBar() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisState>({ isAnalyzing: false })
  const location = useLocation()
  const { isSignedIn, user } = useUser()

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return;

    setSelectedFile(file)
    setAnalysis({ isAnalyzing: true })

    try {
      // First validate the image
      const validation = await agriGuardAPI.validateImage(file)
      const gradcam = await agriGuardAPI.analyzeImageWithGradCAM(file)
      
      if (!validation.not_corrupted) {
        setAnalysis({
          isAnalyzing: false,
          validation,
          error: validation.errors.join(', ') || 'Image failed validation.'
        })
        return
      }

      const pipeline = await agriGuardAPI.analyzeImage(file)
      setAnalysis({
        isAnalyzing: false,
        validation,
        pipeline,
        gradcam
      })

      // Save to dashboard if user is signed in
      if (user?.id && user?.emailAddresses?.[0]?.emailAddress && pipeline) {
        await dashboardStorage.ensureUser(
          user.id,
          user.emailAddresses[0].emailAddress,
          user.firstName || undefined,
          user.lastName || undefined
        )
        
        await dashboardStorage.addUpload(user.id, {
          fileName: file.name,
          imagePath: pipeline.stored_image_path || null,
          predictionClass: pipeline.pred_class || 'Unknown',
          severity: pipeline.severity || 'Unknown',
          confidence: {
            healthy: pipeline.prob_healthy ?? 0,
            diseased: pipeline.prob_diseased ?? 0
          },
          summary: pipeline.summary
        })
      }
    } catch (error) {
      setAnalysis({
        isAnalyzing: false,
        error: error instanceof Error ? error.message : 'Analysis failed'
      })
    }
  }

  const triggerFileUpload = () => {
    const fileInput = document.getElementById('file-upload') as HTMLInputElement
    fileInput?.click()
  }

  const clearAnalysis = () => {
    setSelectedFile(null)
    setAnalysis({ isAnalyzing: false })
  }

  const handleStartChat = () => {
    setAnalysis(prev => ({ ...prev, showChat: true }))
  }

  const handleCloseChat = () => {
    setAnalysis(prev => ({ ...prev, showChat: false }))
  }

  const isActive = (path: string) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link'
  }

  return (
    <>
      <nav className="navbar">
        <div className="nav-container">
          <Link to="/" className="nav-logo">
            <span className="logo-icon">🍃</span>
            <span className="logo-text">AgriGuard</span>
          </Link>
          <div className="nav-menu">
            <Link to="/" className={isActive('/')}>Home</Link>
            <Link to="/how-it-works" className={isActive('/how-it-works')}>How It Works</Link>
            <Link to="/features" className={isActive('/features')}>Features</Link>
            <Link to="/about" className={isActive('/about')}>About</Link>
            {isSignedIn && (
              <Link to="/dashboard" className={isActive('/dashboard')}>Dashboard</Link>
            )}
            <button className="nav-upload-btn" onClick={triggerFileUpload}>
              📤 Upload Image
            </button>
            {!isSignedIn ? (
              <div className="auth-buttons">
                <SignInButton 
                  mode="modal"
                  signUpForceRedirectUrl="/"
                  forceRedirectUrl="/"
                >
                  <button className="nav-signin-btn">Sign In</button>
                </SignInButton>
                <SignUpButton 
                  mode="modal"
                  signInForceRedirectUrl="/"
                  forceRedirectUrl="/"
                >
                  <button className="nav-signup-btn">Sign Up</button>
                </SignUpButton>
              </div>
            ) : (
              <div className="user-section">
                <span className="welcome-text">Welcome, {user?.firstName || 'User'}!</span>
                <UserButton afterSignOutUrl="/" />
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Hidden File Input */}
      <input
        type="file"
        id="file-upload"
        accept="image/*"
        onChange={handleFileUpload}
        style={{ display: 'none' }}
      />

      {/* Analysis Results */}
      {selectedFile && (
        <div className="analysis-overlay">
          <div className="analysis-modal">
            <div className="analysis-header">
              <h3>🌱 AgriGuard Analysis Results</h3>
              <button className="close-btn" onClick={clearAnalysis}>✕</button>
            </div>
            
            <div className="file-info">
              <div className="file-details">
                <span className="file-name">📁 {selectedFile.name}</span>
                <span className="file-meta">{getFileType(selectedFile)} • {formatFileSize(selectedFile.size)}</span>
              </div>
            </div>

            {analysis.isAnalyzing && (
              <div className="analyzing-state">
                <div className="spinner"></div>
                <p>🔬 Analyzing plant health...</p>
                <div className="analysis-steps">
                  <div className="step">✓ Image uploaded</div>
                  <div className="step active">🔍 Validating image integrity</div>
                  <div className="step">🤖 Running AI disease detection pipeline</div>
                  <div className="step">📊 Generating report</div>
                </div>
              </div>
            )}

            {analysis.error && (
              <div className="error-state">
                <div className="error-icon">❌</div>
                <h4>Analysis Failed</h4>
                <p>{analysis.error}</p>
                <button className="retry-btn" onClick={triggerFileUpload}>Try Another Image</button>
              </div>
            )}

            {analysis.validation && !analysis.isAnalyzing && !analysis.error && (
              <div className="results-container">
                {/* Image Validation Results */}
                <div className="validation-section">
                  <h4>🔒 Image Validation</h4>
                  <div className="validation-grid">
                    <div className={`validation-item ${analysis.validation.not_corrupted ? 'success' : 'error'}`}>
                      <span className="icon">{analysis.validation.not_corrupted ? '✅' : '❌'}</span>
                      <span>Image Integrity</span>
                    </div>
                    <div className={`validation-item ${analysis.validation.format_valid ? 'success' : 'error'}`}>
                      <span className="icon">{analysis.validation.format_valid ? '✅' : '❌'}</span>
                      <span>Format Valid</span>
                    </div>
                    <div className="validation-item">
                      <span className="icon">🔐</span>
                      <span>SHA-256: {analysis.validation.hash ? analysis.validation.hash.substring(0, 16) + '...' : 'N/A'}</span>
                    </div>
                  </div>
                  {analysis.validation.warnings && analysis.validation.warnings.length > 0 && (
                    <div className="warnings">
                      <h5>⚠️ Warnings:</h5>
                      {analysis.validation.warnings.map((warning, i) => (
                        <p key={i} className="warning">{warning}</p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Pipeline Results */}
                {analysis.pipeline && (
                  <div className="disease-section">
                    <h4>🌿 AI Disease Pipeline Output</h4>
                    <div className="disease-result">
                      <div className="disease-header">
                        <span className="status-icon">
                          {analysis.pipeline.pred_class?.toLowerCase() === 'healthy' ? '✅' : '🚨'}
                        </span>
                        <div>
                          <h5>{analysis.pipeline.pred_class || 'Prediction unavailable'}</h5>
                          <p>
                            Healthy: {((analysis.pipeline.prob_healthy ?? 0) * 100).toFixed(1)}% •
                            Diseased: {((analysis.pipeline.prob_diseased ?? 0) * 100).toFixed(1)}%
                          </p>
                        </div>
                        {analysis.pipeline.severity && (
                          <div className={`severity-badge ${analysis.pipeline.severity.toLowerCase().replace(/\s+/g, '-')}`}>
                            {analysis.pipeline.severity.toUpperCase()}
                          </div>
                        )}
                      </div>

                      {analysis.pipeline.summary && (
                        <div className="summary-card">
                          <h5>📝 LLM Summary</h5>
                          <p>{analysis.pipeline.summary}</p>
                        </div>
                      )}

                      {analysis.pipeline.prediction_breakdown && (
                        <div className="summary-card prediction-breakdown">
                          <h5>📈 Model Confidence Breakdown</h5>
                          <pre>{JSON.stringify(analysis.pipeline.prediction_breakdown, null, 2)}</pre>
                        </div>
                      )}

                      {analysis.pipeline.recommendations && analysis.pipeline.recommendations.length > 0 && (
                        <div className="treatments">
                          <h5>💊 Recommended Actions:</h5>
                          <ul>
                            {analysis.pipeline.recommendations.map((treatment, i) => (
                              <li key={i}>{treatment}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {analysis.gradcam && (
                          <div className="gradcam-visual">
                            <h5>🎯 Disease Localization (Grad-CAM)</h5>
                            <img
                              src={`data:image/${analysis.gradcam.image_format};base64,${analysis.gradcam.annotated_image_base64}`}
                              alt="Grad-CAM annotated plant"
                              style={{ maxWidth: '100%', borderRadius: '12px' }}
                            />
                            <p className="gradcam-note">
                              Red bounding box shows the region most influential for predicting: <strong>{analysis.gradcam.prediction}</strong> (confidence: {(analysis.gradcam.confidence * 100).toFixed(1)}%)
                            </p>
                          </div>
                        )}

                      {analysis.pipeline.report && (
                        <div className="report-card">
                          <h5>📄 Report Snapshot</h5>
                          <p><strong>Severity:</strong> {analysis.pipeline.report.severity || 'N/A'}</p>
                          {analysis.pipeline.report.recommendations && (
                            <ul>
                              {analysis.pipeline.report.recommendations.map((rec, index) => (
                                <li key={index}>{rec}</li>
                              ))}
                            </ul>
                          )}
                          {analysis.pipeline.report_path && (
                            <p className="report-path">Stored at: {analysis.pipeline.report_path}</p>
                          )}
                        </div>
                      )}

                      {/* Chat Action Button */}
                      <div className="chat-action">
                        <button className="start-chat-btn" onClick={handleStartChat}>
                          💬 Chat with AgriGuard Assistant
                        </button>
                        <p className="chat-hint">
                          Have questions? Ask our AI assistant about treatments, prevention, or plant care!
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Chat Panel */}
      {analysis.showChat && analysis.pipeline && (
        <ChatPanel 
          analysisContext={analysis.pipeline}
          onClose={handleCloseChat}
        />
      )}
    </>
  )
}

function App() {
  return (
    <Router>
      <div className="app">
        <NavBar />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/features" element={<Features />} />
            <Route path="/about" element={<About />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>

        {/* Footer - appears on all pages */}
        <footer className="footer">
          <div className="container">
            <div className="footer-content">
              <div className="team-info">
                <h3>Team AgriGuard</h3>
                <p>Built with ❤️ for agricultural innovation</p>
              </div>
              <div className="footer-links">
                <a href="https://github.com" className="footer-link">
                  📂 GitHub Repository
                </a>
                <div className="hackathon-badge">
                  🏆 Hackathon 2025
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App