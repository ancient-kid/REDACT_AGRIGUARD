import { useUser } from '@clerk/clerk-react'
import { useState, useEffect } from 'react'
import { dashboardStorage } from '../services/dashboardStorage'
import type { DashboardData, UploadHistory } from '../services/dashboardStorage'

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
  const [isLoading, setIsLoading] = useState(true)
  const [expandedChatId, setExpandedChatId] = useState<string | null>(null)

  const loadDashboardData = async () => {
    if (!user?.id) return
    
    setIsLoading(true)
    try {
      // Ensure user exists in database
      if (user.emailAddresses?.[0]?.emailAddress) {
        await dashboardStorage.ensureUser(
          user.id,
          user.emailAddresses[0].emailAddress,
          user.firstName || undefined,
          user.lastName || undefined
        )
      }
      
      const data = await dashboardStorage.getUserData(user.id)
      setDashboardData(data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (isLoaded && user) {
      loadDashboardData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, user])

  if (!isLoaded || !user || isLoading) {
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
                    .sort((a, b) => {
                      const dateA = 'timestamp' in a ? a.timestamp : a.createdAt
                      const dateB = 'timestamp' in b ? b.timestamp : b.createdAt
                      return new Date(dateB).getTime() - new Date(dateA).getTime()
                    })
                    .slice(0, 5)
                    .map((item) => {
                      const isUpload = 'fileName' in item
                      const itemDate = 'timestamp' in item ? item.timestamp : item.createdAt
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
                            <p>{formatDate(itemDate)}</p>
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
                    {upload.imageUrl && (
                      <div className="upload-image-preview">
                        <img 
                          src={`http://localhost:8000${upload.imageUrl}`} 
                          alt={upload.fileName}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none'
                          }}
                        />
                      </div>
                    )}
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
                {dashboardData.chats.map((chat) => {
                  const isExpanded = expandedChatId === chat.id
                  return (
                    <div key={chat.id} className="chat-card">
                      <div className="chat-header">
                        <div className="chat-header-left">
                          <h4>💬 Chat Session</h4>
                          <p className="chat-date">{formatDate(chat.createdAt)}</p>
                          <span className="message-count">{chat.messages.length} messages</span>
                        </div>
                        <button 
                          className="expand-btn"
                          onClick={() => setExpandedChatId(isExpanded ? null : chat.id)}
                        >
                          {isExpanded ? '▲ Collapse' : '▼ Expand'}
                        </button>
                      </div>
                      <div className={`chat-messages ${isExpanded ? 'expanded' : 'collapsed'}`}>
                        {(isExpanded ? chat.messages : chat.messages.slice(0, 2)).map((msg, idx) => (
                          <div key={idx} className={`message-full ${msg.role}`}>
                            <div className="message-header">
                              <strong>{msg.role === 'user' ? '👤 You' : '🤖 Assistant'}</strong>
                              <span className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                            </div>
                            <div className="message-content">
                              <p>{msg.content}</p>
                            </div>
                          </div>
                        ))}
                        {!isExpanded && chat.messages.length > 2 && (
                          <button 
                            className="show-more-btn"
                            onClick={() => setExpandedChatId(chat.id)}
                          >
                            Show all {chat.messages.length} messages
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
