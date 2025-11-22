export const Features = () => {
  return (
    <section className="page-section">
      <div className="container">
        <h1 className="page-title">Features & Capabilities</h1>
        
        <div className="features-detailed">
          <div className="feature-detailed">
            <div className="feature-header">
              <div className="feature-icon-large">🔍</div>
              <h2>Disease Classification</h2>
            </div>
            <div className="feature-body">
              <p>Advanced multi-class classification system that can identify various plant diseases with high precision.</p>
              <div className="feature-specs">
                <div className="spec-item">
                  <strong>Classes:</strong> Healthy, Diseased, Disease Type
                </div>
                <div className="spec-item">
                  <strong>Diseases Covered:</strong> 15+ common plant diseases
                </div>
                <div className="spec-item">
                  <strong>Supported Plants:</strong> Tomato, Potato, Corn, Apple, and more
                </div>
              </div>
            </div>
          </div>

          <div className="feature-detailed">
            <div className="feature-header">
              <div className="feature-icon-large">📊</div>
              <h2>Severity Scoring</h2>
            </div>
            <div className="feature-body">
              <p>Intelligent severity assessment helps prioritize treatment urgency and resource allocation.</p>
              <div className="severity-levels">
                <div className="severity-item mild">
                  <span className="severity-badge">Mild</span>
                  <span>Early intervention recommended</span>
                </div>
                <div className="severity-item moderate">
                  <span className="severity-badge">Moderate</span>
                  <span>Immediate treatment required</span>
                </div>
                <div className="severity-item severe">
                  <span className="severity-badge">Severe</span>
                  <span>Urgent action needed</span>
                </div>
              </div>
            </div>
          </div>

          <div className="feature-detailed">
            <div className="feature-header">
              <div className="feature-icon-large">🧠</div>
              <h2>Explainable AI</h2>
            </div>
            <div className="feature-body">
              <p>Transparent AI decisions with visual explanations using Grad-CAM technology.</p>
              <div className="explainable-features">
                <div className="explain-item">
                  <span className="explain-icon">🎯</span>
                  <span>Highlights affected regions</span>
                </div>
                <div className="explain-item">
                  <span className="explain-icon">📈</span>
                  <span>Confidence scoring</span>
                </div>
                <div className="explain-item">
                  <span className="explain-icon">🔬</span>
                  <span>Decision reasoning</span>
                </div>
              </div>
            </div>
          </div>

          <div className="feature-detailed">
            <div className="feature-header">
              <div className="feature-icon-large">🔒</div>
              <h2>Data Integrity</h2>
            </div>
            <div className="feature-body">
              <p>Robust data security and integrity checks ensure reliable and tamper-proof analysis.</p>
              <div className="security-features">
                <div className="security-item">
                  <strong>SHA-256 Hashing:</strong> Cryptographic verification of uploaded images
                </div>
                <div className="security-item">
                  <strong>Privacy Protection:</strong> Images processed locally when possible
                </div>
                <div className="security-item">
                  <strong>Data Validation:</strong> Comprehensive input validation and sanitization
                </div>
              </div>
            </div>
          </div>

          <div className="feature-detailed">
            <div className="feature-header">
              <div className="feature-icon-large">📱</div>
              <h2>Mobile & Edge Ready</h2>
            </div>
            <div className="feature-body">
              <p>Optimized for deployment on mobile devices and edge computing environments.</p>
              <div className="mobile-specs">
                <div className="mobile-spec">
                  <span className="spec-label">Model Size:</span>
                  <span className="spec-value">&lt; 50MB</span>
                </div>
                <div className="mobile-spec">
                  <span className="spec-label">Inference Time:</span>
                  <span className="spec-value">&lt; 2 seconds</span>
                </div>
                <div className="mobile-spec">
                  <span className="spec-label">Compatibility:</span>
                  <span className="spec-value">iOS, Android, Web</span>
                </div>
                <div className="mobile-spec">
                  <span className="spec-label">Offline Mode:</span>
                  <span className="spec-value">Available</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="performance-metrics">
          <h2>Model Performance</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-value">94.2%</div>
              <div className="metric-label">Overall Accuracy</div>
              <div className="metric-bar">
                <div className="metric-fill" style={{width: '94.2%'}}></div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-value">92.8%</div>
              <div className="metric-label">Precision</div>
              <div className="metric-bar">
                <div className="metric-fill" style={{width: '92.8%'}}></div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-value">91.5%</div>
              <div className="metric-label">Recall</div>
              <div className="metric-bar">
                <div className="metric-fill" style={{width: '91.5%'}}></div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-value">92.1%</div>
              <div className="metric-label">F1-Score</div>
              <div className="metric-bar">
                <div className="metric-fill" style={{width: '92.1%'}}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};