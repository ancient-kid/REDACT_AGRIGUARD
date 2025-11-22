export const Home = () => {
  return (
    <>
      {/* Hero Section */}
      <section id="home" className="hero">
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              AgriGuard: AI-Powered Plant Disease Detection
            </h1>
            <p className="hero-subtitle">
              LangGraph pipeline with PyTorch CNNs, SHAP explainability, and Gemini AI chat for comprehensive disease diagnosis and treatment guidance.
            </p>
            <div className="hero-buttons">
              <button className="btn btn-primary">Try Demo</button>
              <button className="btn btn-secondary">View GitHub Repo</button>
            </div>
          </div>
          <div className="hero-image">
            <div className="placeholder-image">
              🌱 AI Plant Doctor
              <div className="scan-overlay">
                <div className="scan-line"></div>
                <div className="scan-points">
                  <span className="scan-point"></span>
                  <span className="scan-point"></span>
                  <span className="scan-point"></span>
                </div>
              </div>
              <div className="plant-health-indicator">
                <div className="health-icon">🔬</div>
                <div className="health-status">Analyzing...</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Stats Section */}
      <section className="quick-stats">
        <div className="container">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number">8</div>
              <div className="stat-label">Pipeline Nodes</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">2</div>
              <div className="stat-label">CNN Models</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">💬</div>
              <div className="stat-label">AI Chat Assistant</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">🔥</div>
              <div className="stat-label">SHAP Heatmaps</div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};