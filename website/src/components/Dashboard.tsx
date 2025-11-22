import { useUser } from '@clerk/clerk-react'
import { useState, useEffect } from 'react'

interface UploadHistory {
  id: string
  fileName: string
  timestamp: Date
  predictionClass: string
  severity: string
  confidence: { healthy: number; diseased: number }
  summary?: string
}

interface ChatHistory {
  id: string
  timestamp: Date
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  relatedUpload?: string
}

interface DashboardData {
  uploads: UploadHistory[]
  chats: ChatHistory[]
  stats: {
    totalUploads: number
    healthyPlants: number
    diseasedPlants: number
    totalChats: number
  }
}

export const Dashboard = () => {
  const { user, isLoaded } = useUser()
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    uploads: [],
    chats: [],
    stats: {
      totalUploads: 0,
      healthyPlants: 0,
      diseasedPlants: 0,
      totalChats: 0
    }
  })
  const [activeTab, setActiveTab] = useState<'overview' | 'uploads' | 'chats'>('overview')

  const loadDashboardData = () => {
    // Load data from localStorage for this user
    const userDataKey = `agriguard_user_${user?.id}`
    const savedData = localStorage.getItem(userDataKey)
    
    if (savedData) {
      const data = JSON.parse(savedData) as DashboardData
      // Convert timestamp strings back to Date objects
      data.uploads = data.uploads.map((upload) => ({
        ...upload,
        timestamp: new Date(upload.timestamp)
      }))
      data.chats = data.chats.map((chat) => ({
        ...chat,
        timestamp: new Date(chat.timestamp)
      }))
      setDashboardData(data)
    }
  }

  useEffect(() => {
    if (isLoaded && user) {
      loadDashboardData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, user])

  if (!isLoaded || !user) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="user-welcome">
          <h1>Welcome back, {user.firstName || 'User'}! 🌿</h1>
          <p>Here's your AgriGuard activity dashboard</p>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📤</div>
          <div className="stat-content">
            <h3>{dashboardData.stats.totalUploads}</h3>
            <p>Total Scans</p>
          </div>
        </div>
        <div className="stat-card healthy">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{dashboardData.stats.healthyPlants}</h3>
            <p>Healthy Plants</p>
          </div>
        </div>
        <div className="stat-card diseased">
          <div className="stat-icon">🚨</div>
          <div className="stat-content">
            <h3>{dashboardData.stats.diseasedPlants}</h3>
            <p>Diseased Plants</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💬</div>
          <div className="stat-content">
            <h3>{dashboardData.stats.totalChats}</h3>
            <p>Chat Sessions</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="dashboard-tabs">
        <button 
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`tab-btn ${activeTab === 'uploads' ? 'active' : ''}`}
          onClick={() => setActiveTab('uploads')}
        >
          📤 Upload History
        </button>
        <button 
          className={`tab-btn ${activeTab === 'chats' ? 'active' : ''}`}
          onClick={() => setActiveTab('chats')}
        >
          💬 Chat History
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-content">
            <div className="recent-activity">
              <h3>Recent Activity</h3>
              {dashboardData.uploads.length === 0 && dashboardData.chats.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">🌱</div>
                  <h4>No activity yet</h4>
                  <p>Upload your first plant image to get started!</p>
                </div>
              ) : (
                <div className="activity-timeline">
                  {[...dashboardData.uploads, ...dashboardData.chats]
                    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                    .slice(0, 5)
                    .map((item) => {
                      const isUpload = 'fileName' in item
                      return (
                        <div key={item.id} className="activity-item">
                          <div className="activity-icon">
                            {isUpload ? '📸' : '💬'}
                          </div>
                          <div className="activity-details">
                            <h4>
                              {isUpload 
                                ? `Scanned ${(item as UploadHistory).fileName}` 
                                : 'Chat Session'}
                            </h4>
                            <p>{formatDate(item.timestamp)}</p>
                            {isUpload && (
                              <span className={`status-badge ${(item as UploadHistory).predictionClass.toLowerCase()}`}>
                                {(item as UploadHistory).predictionClass}
                              </span>
                            )}
                          </div>
                        </div>
                      )
                    })}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'uploads' && (
          <div className="uploads-content">
            <h3>Image Upload History</h3>
            {dashboardData.uploads.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📤</div>
                <h4>No uploads yet</h4>
                <p>Start by uploading a plant image for analysis</p>
              </div>
            ) : (
              <div className="uploads-grid">
                {dashboardData.uploads.map((upload) => (
                  <div key={upload.id} className="upload-card">
                    <div className="upload-header">
                      <h4>{upload.fileName}</h4>
                      <span className={`prediction-badge ${upload.predictionClass.toLowerCase()}`}>
                        {upload.predictionClass}
                      </span>
                    </div>
                    <div className="upload-details">
                      <p className="upload-date">📅 {formatDate(upload.timestamp)}</p>
                      {upload.severity && (
                        <p className="upload-severity">
                          <strong>Severity:</strong> {upload.severity}
                        </p>
                      )}
                      <div className="confidence-bars">
                        <div className="confidence-item">
                          <span>Healthy</span>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill healthy"
                              style={{ width: `${upload.confidence.healthy * 100}%` }}
                            ></div>
                          </div>
                          <span>{(upload.confidence.healthy * 100).toFixed(1)}%</span>
                        </div>
                        <div className="confidence-item">
                          <span>Diseased</span>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill diseased"
                              style={{ width: `${upload.confidence.diseased * 100}%` }}
                            ></div>
                          </div>
                          <span>{(upload.confidence.diseased * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      {upload.summary && (
                        <div className="upload-summary">
                          <p>{upload.summary}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'chats' && (
          <div className="chats-content">
            <h3>Chat History</h3>
            {dashboardData.chats.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">💬</div>
                <h4>No chat sessions yet</h4>
                <p>Start a conversation with the AgriGuard Assistant</p>
              </div>
            ) : (
              <div className="chats-list">
                {dashboardData.chats.map((chat) => (
                  <div key={chat.id} className="chat-card">
                    <div className="chat-header">
                      <h4>💬 Chat Session</h4>
                      <p className="chat-date">{formatDate(chat.timestamp)}</p>
                    </div>
                    <div className="chat-preview">
                      {chat.messages.slice(0, 3).map((msg, idx) => (
                        <div key={idx} className={`message-preview ${msg.role}`}>
                          <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
                          <p>{msg.content.substring(0, 100)}{msg.content.length > 100 ? '...' : ''}</p>
                        </div>
                      ))}
                      {chat.messages.length > 3 && (
                        <p className="more-messages">
                          +{chat.messages.length - 3} more messages
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
