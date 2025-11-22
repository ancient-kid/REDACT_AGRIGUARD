export const Home = () => {
  return (
    <>
      {/* Hero Section */}
      <section id="home" className="hero">
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              AgriGuard: AI-Powered Early Plant Disease Triage
            </h1>
            <p className="hero-subtitle">
              Detect plant diseases early using AI and mobile-ready vision models.
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
              <div className="stat-number">94.2%</div>
              <div className="stat-label">Disease Detection</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">25+</div>
              <div className="stat-label">Plant Diseases</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">&lt;3s</div>
              <div className="stat-label">Analysis Time</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">🌾</div>
              <div className="stat-label">Farm Ready</div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};