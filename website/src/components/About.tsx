export const About = () => {
  return (
    <section className="page-section">
      <div className="container">
        <h1 className="page-title">About AgriGuard</h1>
        
        <div className="about-content-detailed">
          <div className="about-intro">
            <div className="intro-text">
              <h2>Revolutionizing Agricultural Disease Management</h2>
              <p>
                AgriGuard is an innovative AI-powered crop protection solution designed to help farmers, 
                agricultural extension workers, and plant pathologists detect plant diseases early 
                and accurately. Built with cutting-edge computer vision technology, our platform 
                makes advanced agricultural diagnostics accessible to farming communities worldwide.
              </p>
              <p>
                This project demonstrates how modern artificial intelligence can be applied 
                to solve critical agricultural challenges, potentially helping prevent crop 
                losses, reduce pesticide use, and improve global food security through early disease detection.
              </p>
            </div>
            <div className="intro-image">
              <div className="about-illustration">
                🌾🤖
                <div className="ai-plants">
                  <span className="plant">🌱</span>
                  <span className="plant">🌿</span>
                  <span className="plant">🍃</span>
                </div>
                <div className="farm-elements">
                  <span className="farm-icon">🚜</span>
                  <span className="farm-icon">🔬</span>
                </div>
              </div>
            </div>
          </div>

          <div className="project-details">
            <h2>Project Background</h2>
            <div className="detail-cards">
              <div className="detail-card">
                <div className="card-icon">🏆</div>
                <h3>Hackathon Project</h3>
                <p>
                  Built during a technology hackathon to showcase the potential of AI 
                  in agricultural innovation. Our team focused on creating a practical, 
                  user-friendly solution that could have real-world impact.
                </p>
              </div>
              
              <div className="detail-card">
                <div className="card-icon">📚</div>
                <h3>Dataset & Training</h3>
                <p>
                  Our model is trained on the comprehensive PlantVillage dataset from Kaggle, 
                  which contains over 50,000 images of healthy and diseased plant leaves 
                  across 14 crop species and 26 diseases.
                </p>
              </div>
              
              <div className="detail-card">
                <div className="card-icon">🎯</div>
                <h3>Mission</h3>
                <p>
                  To democratize access to plant disease diagnosis technology, making it 
                  available to farmers worldwide regardless of their technical background 
                  or geographic location.
                </p>
              </div>
            </div>
          </div>

          <div className="technology-stack">
            <h2>Technology Stack</h2>
            <div className="tech-categories">
              <div className="tech-category">
                <h4>Machine Learning</h4>
                <div className="tech-tags">
                  <span className="tech-tag">TensorFlow</span>
                  <span className="tech-tag">PyTorch</span>
                  <span className="tech-tag">OpenCV</span>
                  <span className="tech-tag">Grad-CAM</span>
                </div>
              </div>
              
              <div className="tech-category">
                <h4>Frontend</h4>
                <div className="tech-tags">
                  <span className="tech-tag">React</span>
                  <span className="tech-tag">TypeScript</span>
                  <span className="tech-tag">Vite</span>
                  <span className="tech-tag">CSS3</span>
                </div>
              </div>
              
              <div className="tech-category">
                <h4>Backend & Deployment</h4>
                <div className="tech-tags">
                  <span className="tech-tag">Python</span>
                  <span className="tech-tag">FastAPI</span>
                  <span className="tech-tag">Docker</span>
                  <span className="tech-tag">AWS</span>
                </div>
              </div>
            </div>
          </div>

          <div className="team-section">
            <h2>Development Team</h2>
            <div className="team-info">
              <p>
                AgriGuard was developed by a passionate team of software engineers, 
                data scientists, and agricultural technology enthusiasts committed to 
                leveraging AI for social good.
              </p>
              
              <div className="team-values">
                <div className="value-item">
                  <span className="value-icon">🌱</span>
                  <span><strong>Sustainability:</strong> Supporting environmentally conscious farming</span>
                </div>
                <div className="value-item">
                  <span className="value-icon">🤝</span>
                  <span><strong>Accessibility:</strong> Making technology available to all farmers</span>
                </div>
                <div className="value-item">
                  <span className="value-icon">🔬</span>
                  <span><strong>Innovation:</strong> Pushing the boundaries of agricultural AI</span>
                </div>
                <div className="value-item">
                  <span className="value-icon">🎯</span>
                  <span><strong>Accuracy:</strong> Providing reliable, actionable insights</span>
                </div>
              </div>
            </div>
          </div>

          <div className="future-roadmap">
            <h2>Future Development</h2>
            <div className="roadmap-items">
              <div className="roadmap-item">
                <div className="roadmap-icon">📊</div>
                <h4>Advanced Analytics</h4>
                <p>Crop health monitoring and yield prediction capabilities</p>
              </div>
              <div className="roadmap-item">
                <div className="roadmap-icon">🌍</div>
                <h4>Global Expansion</h4>
                <p>Support for more crop types and regional disease variants</p>
              </div>
              <div className="roadmap-item">
                <div className="roadmap-icon">📱</div>
                <h4>Mobile App</h4>
                <p>Native iOS and Android applications with offline capabilities</p>
              </div>
              <div className="roadmap-item">
                <div className="roadmap-icon">🤝</div>
                <h4>Expert Network</h4>
                <p>Connect with agricultural experts and plant pathologists</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};