import { useState, useEffect } from 'react'
import { useUser } from '@clerk/clerk-react'
import { agriGuardAPI } from '../services/api'
import type { DashboardStats } from '../services/api'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar, Pie } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

export function DashboardSystem() {
  const { user } = useUser()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const data = await agriGuardAPI.getDashboardStats()
      console.log('[DASHBOARD] Received stats:', data)
      setStats(data)
    } catch (err) {
      console.error('[DASHBOARD ERROR]', err)
      setError(err instanceof Error ? err.message : 'Failed to load dashboard statistics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <p>Loading dashboard statistics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-error">
          <h2>⚠️ Error Loading Dashboard</h2>
          <p>{error}</p>
          <button onClick={fetchDashboardStats} className="retry-button">
            🔄 Retry
          </button>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-error">
          <h2>📊 No Data Available</h2>
          <p>Dashboard statistics are currently unavailable.</p>
        </div>
      </div>
    )
  }

  // Prepare chart data
  const diseaseModel = stats.disease_model
  const perClassMetrics = diseaseModel?.per_class_metrics || []

  // Top 10 diseases by accuracy
  const topDiseases = [...perClassMetrics]
    .sort((a, b) => b.accuracy - a.accuracy)
    .slice(0, 10)

  const accuracyChartData = {
    labels: topDiseases.map(m => m.class_name.split('___')[1]?.replace(/_/g, ' ') || m.class_name),
    datasets: [{
      label: 'Accuracy (%)',
      data: topDiseases.map(m => m.accuracy * 100),
      backgroundColor: 'rgba(74, 222, 128, 0.6)',
      borderColor: 'rgba(74, 222, 128, 1)',
      borderWidth: 2
    }]
  }

  // Confidence distribution
  const confDistribution = diseaseModel?.confidence_distribution || { low: 0, medium: 0, high: 0 }
  const confidenceChartData = {
    labels: ['High Confidence (>80%)', 'Medium Confidence (50-80%)', 'Low Confidence (<50%)'],
    datasets: [{
      data: [confDistribution.high, confDistribution.medium, confDistribution.low],
      backgroundColor: [
        'rgba(74, 222, 128, 0.8)',
        'rgba(251, 191, 36, 0.8)',
        'rgba(248, 113, 113, 0.8)'
      ],
      borderWidth: 2
    }]
  }

  // Crop statistics
  const cropStats = diseaseModel?.crop_statistics || {}
  const cropChartData = {
    labels: Object.keys(cropStats),
    datasets: [{
      label: 'Number of Detectable Diseases',
      data: Object.values(cropStats),
      backgroundColor: 'rgba(96, 165, 250, 0.6)',
      borderColor: 'rgba(96, 165, 250, 1)',
      borderWidth: 2
    }]
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>📊 AgriGuard Model Dashboard</h1>
        <p className="dashboard-subtitle">
          Comprehensive model performance and system capabilities
        </p>
      </div>

      {/* Overview Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>🎯 Overall Accuracy</h3>
          <p className="stat-value">
            {((diseaseModel?.metrics?.accuracy || 0) * 100).toFixed(2)}%
          </p>
          <p className="stat-label">Disease Classification Accuracy</p>
        </div>

        <div className="stat-card">
          <h3>🌱 Supported Crops</h3>
          <p className="stat-value">{Object.keys(cropStats).length}</p>
          <p className="stat-label">Different crop types</p>
        </div>

        <div className="stat-card">
          <h3>🦠 Detectable Diseases</h3>
          <p className="stat-value">{diseaseModel?.training_info?.num_classes || 0}</p>
          <p className="stat-label">Across all crops</p>
        </div>

        <div className="stat-card">
          <h3>📈 F1 Score (Macro)</h3>
          <p className="stat-value">
            {((diseaseModel?.metrics?.f1_macro || 0) * 100).toFixed(2)}%
          </p>
          <p className="stat-label">Balanced performance metric</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3>🏆 Top 10 Diseases by Detection Accuracy</h3>
          <div className="chart-container">
            <Bar 
              data={accuracyChartData} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  title: { display: false }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                      callback: (value) => `${value}%`
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        <div className="chart-card">
          <h3>🎲 Model Confidence Distribution</h3>
          <div className="chart-container">
            <Pie 
              data={confidenceChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: 'bottom' }
                }
              }}
            />
          </div>
        </div>

        <div className="chart-card full-width">
          <h3>🌾 Diseases per Crop Type</h3>
          <div className="chart-container">
            <Bar 
              data={cropChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      stepSize: 1
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="system-info">
        <h2>🔧 System Capabilities</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>Framework:</strong> {diseaseModel?.training_info?.framework || 'N/A'}
          </div>
          <div className="info-item">
            <strong>Validation Samples:</strong> {diseaseModel?.training_info?.validation_samples?.toLocaleString() || 'N/A'}
          </div>
          <div className="info-item">
            <strong>Last Trained:</strong> Epoch {diseaseModel?.training_info?.last_epoch || 'N/A'}
          </div>
          <div className="info-item">
            <strong>Deployment:</strong> {stats.pipeline_info?.deployment || 'N/A'}
          </div>
        </div>
      </div>

      {/* Model Architecture */}
      <div className="architecture-info">
        <h2>🏗️ Model Architecture</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>Total Parameters:</strong> {diseaseModel?.architecture?.total_parameters?.toLocaleString() || 'N/A'}
          </div>
          <div className="info-item">
            <strong>Layers:</strong> {diseaseModel?.architecture?.num_layers || 'N/A'}
          </div>
          <div className="info-item">
            <strong>Input Size:</strong> {diseaseModel?.architecture?.input_size || 'N/A'}
          </div>
          <div className="info-item">
            <strong>Output Classes:</strong> {diseaseModel?.architecture?.output_classes || 'N/A'}
          </div>
        </div>
      </div>
    </div>
  )
}