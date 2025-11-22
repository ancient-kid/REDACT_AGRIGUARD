// Utility functions for managing user dashboard data

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

export const dashboardStorage = {
  // Get user's dashboard data
  getUserData(userId: string): DashboardData {
    const userDataKey = `agriguard_user_${userId}`
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
      return data
    }
    
    return {
      uploads: [],
      chats: [],
      stats: {
        totalUploads: 0,
        healthyPlants: 0,
        diseasedPlants: 0,
        totalChats: 0
      }
    }
  },

  // Save user's dashboard data
  saveUserData(userId: string, data: DashboardData): void {
    const userDataKey = `agriguard_user_${userId}`
    localStorage.setItem(userDataKey, JSON.stringify(data))
  },

  // Add a new upload to history
  addUpload(userId: string, upload: Omit<UploadHistory, 'id' | 'timestamp'>): void {
    const data = this.getUserData(userId)
    
    const newUpload: UploadHistory = {
      ...upload,
      id: `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }
    
    data.uploads.unshift(newUpload)
    data.stats.totalUploads++
    
    if (upload.predictionClass.toLowerCase() === 'healthy') {
      data.stats.healthyPlants++
    } else {
      data.stats.diseasedPlants++
    }
    
    this.saveUserData(userId, data)
  },

  // Add a new chat session to history
  addChat(userId: string, chat: Omit<ChatHistory, 'id' | 'timestamp'>): void {
    const data = this.getUserData(userId)
    
    const newChat: ChatHistory = {
      ...chat,
      id: `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }
    
    data.chats.unshift(newChat)
    data.stats.totalChats++
    
    this.saveUserData(userId, data)
  },

  // Update an existing chat session
  updateChat(userId: string, chatId: string, messages: Array<{ role: 'user' | 'assistant'; content: string }>): void {
    const data = this.getUserData(userId)
    const chatIndex = data.chats.findIndex(chat => chat.id === chatId)
    
    if (chatIndex !== -1) {
      data.chats[chatIndex].messages = messages
      data.chats[chatIndex].timestamp = new Date()
      this.saveUserData(userId, data)
    }
  },

  // Get latest chat session
  getLatestChat(userId: string): ChatHistory | null {
    const data = this.getUserData(userId)
    return data.chats.length > 0 ? data.chats[0] : null
  },

  // Clear all user data
  clearUserData(userId: string): void {
    const userDataKey = `agriguard_user_${userId}`
    localStorage.removeItem(userDataKey)
  }
}
