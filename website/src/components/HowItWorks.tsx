export const HowItWorks = () => {
  return (
    <section className="page-section">
      <div className="container">
        <h1 className="page-title">How AgriGuard Works</h1>
        
        <div className="workflow-container">
          <div className="workflow-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <div className="step-icon large">🌿📱</div>
              <h3>Capture Crop Image</h3>
              <p>Take a high-quality photo of the affected plant leaf or crop area using your smartphone. Our AI works best with clear, well-lit images of diseased or suspicious plant tissue.</p>
              <div className="step-tips">
                <strong>Best Practices:</strong>
                <ul>
                  <li>Use natural lighting when possible</li>
                  <li>Focus on diseased leaf areas</li>
                  <li>Avoid shadows and reflections</li>
                  <li>Include healthy tissue for comparison</li>
                  <li>Hold camera steady for sharp images</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="workflow-arrow">↓</div>

          <div className="workflow-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <div className="step-icon large">🔬🌱</div>
              <h3>AI Pipeline Analysis</h3>
              <p>Your image flows through our LangGraph-orchestrated pipeline with PyTorch CNN models for binary classification (healthy/diseased) and multi-class disease identification, followed by SHAP explainability analysis.</p>
              <div className="step-features">
                <div className="feature-item">
                  <span className="feature-icon">🔍</span>
                  <span>Binary Health Classification</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">🦠</span>
                  <span>Multi-Class Disease Detection</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">🔥</span>
                  <span>SHAP Heatmap Generation</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">⚡</span>
                  <span>Real-time Pipeline Processing</span>
                </div>
              </div>
            </div>
          </div>

          <div className="workflow-arrow">↓</div>

          <div className="workflow-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <div className="step-icon large">🚜💡</div>
              <h3>AI-Powered Insights & Chat</h3>
              <p>Gemini AI analyzes your results, searches the web for latest treatments using SerpAPI, and provides farmer-friendly summaries. Chat with the AI assistant for personalized advice on disease management and prevention.</p>
              <div className="recommendation-types">
                <div className="rec-card">
                  <div className="rec-icon">🤖</div>
                  <div className="rec-title">Gemini AI Summary</div>
                </div>
                <div className="rec-card">
                  <div className="rec-icon">🌐</div>
                  <div className="rec-title">Web-Sourced Solutions</div>
                </div>
                <div className="rec-card">
                  <div className="rec-icon">💬</div>
                  <div className="rec-title">Interactive Chat</div>
                </div>
                <div className="rec-card">
                  <div className="rec-icon">📊</div>
                  <div className="rec-title">Severity Assessment</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="technology-info">
          <h2>Our Technology</h2>
          <div className="tech-grid">
            <div className="tech-card">
              <h4>LangGraph Pipeline</h4>
              <p>Orchestrated workflow connecting image preprocessing, binary classification, disease detection, SHAP analysis, and LLM summarization</p>
            </div>
            <div className="tech-card">
              <h4>PyTorch CNNs</h4>
              <p>Custom CNN architectures for binary health classification and multi-class disease identification trained on agricultural datasets</p>
            </div>
            <div className="tech-card">
              <h4>SHAP Explainability</h4>
              <p>SHAP heatmaps show which leaf regions influenced the disease diagnosis for transparent AI decisions</p>
            </div>
            <div className="tech-card">
              <h4>Gemini AI + Web Search</h4>
              <p>Gemini AI powered chat assistant with SerpAPI integration for real-time agricultural treatment research</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};