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
              <h3>AI Pathology Analysis</h3>
              <p>Our specialized plant pathology AI model analyzes crop images using advanced computer vision trained on extensive agricultural datasets including the PlantVillage collection and real-world farm data.</p>
              <div className="step-features">
                <div className="feature-item">
                  <span className="feature-icon">🔍</span>
                  <span>Disease Pattern Recognition</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">📊</span>
                  <span>Severity Assessment</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">⚡</span>
                  <span>Real-time Processing</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">🌾</span>
                  <span>Crop-specific Analysis</span>
                </div>
              </div>
            </div>
          </div>

          <div className="workflow-arrow">↓</div>

          <div className="workflow-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <div className="step-icon large">🚜💡</div>
              <h3>Get Agricultural Treatment Plan</h3>
              <p>Receive comprehensive crop management recommendations including disease identification, severity assessment, and evidence-based treatment protocols from agricultural extension services and plant pathologists.</p>
              <div className="recommendation-types">
                <div className="rec-card">
                  <div className="rec-icon">🌱</div>
                  <div className="rec-title">Organic Treatment</div>
                </div>
                <div className="rec-card">
                  <div className="rec-icon">⚗️</div>
                  <div className="rec-title">Chemical Control</div>
                </div>
                <div className="rec-card">
                  <div className="rec-icon">🛡️</div>
                  <div className="rec-title">Prevention Strategy</div>
                </div>
                <div className="rec-card">
                  <div className="rec-icon">📈</div>
                  <div className="rec-title">Crop Monitoring</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="technology-info">
          <h2>Our Technology</h2>
          <div className="tech-grid">
            <div className="tech-card">
              <h4>Deep Learning</h4>
              <p>Convolutional Neural Networks (CNN) trained on diverse plant disease datasets</p>
            </div>
            <div className="tech-card">
              <h4>Edge Computing</h4>
              <p>Lightweight model optimized for mobile and edge device deployment</p>
            </div>
            <div className="tech-card">
              <h4>Explainable AI</h4>
              <p>Grad-CAM visualizations show which parts of the image influenced the diagnosis</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};