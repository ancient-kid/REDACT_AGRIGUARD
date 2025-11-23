const API_BASE_URL = 'http://localhost:8000'

// ✅ ADD THESE TYPES (they were missing)
export interface UserUpload {
  id: string
  fileName: string
  imageUrl?: string | null
  predictionClass: string
  severity: string
  confidence: {
    healthy: number
    diseased: number
  }
  summary?: string
  createdAt: string  // Changed from timestamp
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface UserChat {
  id: string
  sessionId: string
  createdAt: string
  messages: ChatMessage[]
}

// Keep existing interfaces
export interface UploadHistory {
  id: string
  fileName: string
  imageUrl?: string | null
  timestamp: Date
  predictionClass: string
  severity: string
  confidence: { healthy: number; diseased: number }
  summary?: string
}

export interface ChatHistory {
  id: string
  sessionId: string
  createdAt: Date
  messages: Array<{ role: 'user' | 'assistant'; content: string; timestamp: string }>
}

export interface DashboardData {
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
  // Ensure user exists in database
  async ensureUser(userId: string, email: string, firstName?: string, lastName?: string): Promise<void> {
    await fetch(`${API_BASE_URL}/api/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        email,
        first_name: firstName,
        last_name: lastName
      })
    })
  },

  // ✅ ADD THIS METHOD (was missing)
  async getUserUploads(userId: string): Promise<UserUpload[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/uploads/${userId}`)
      if (!response.ok) throw new Error('Failed to fetch uploads')
      
      const data = await response.json()
      return data.uploads.map((u: any) => ({
        id: u.id,
        fileName: u.fileName,
        imageUrl: u.imageUrl,
        predictionClass: u.predictionClass,
        severity: u.severity,
        confidence: u.confidence,
        summary: u.summary,
        createdAt: u.timestamp
      }))
    } catch (error) {
      console.error('Error fetching user uploads:', error)
      return []
    }
  },

  // ✅ ADD THIS METHOD (was missing)
  async getUserChats(userId: string): Promise<UserChat[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chats/${userId}`)
      if (!response.ok) throw new Error('Failed to fetch chats')
      
      const data = await response.json()
      return data.chats.map((c: any) => ({
        id: c.id,
        sessionId: c.sessionId,
        createdAt: c.createdAt,
        messages: c.messages || []
      }))
    } catch (error) {
      console.error('Error fetching user chats:', error)
      return []
    }
  },

  // Get user's dashboard data
  async getUserData(userId: string): Promise<DashboardData> {
    try {
      const [uploadsRes, chatsRes, statsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/uploads/${userId}`),
        fetch(`${API_BASE_URL}/api/chats/${userId}`),
        fetch(`${API_BASE_URL}/api/dashboard-stats/${userId}`)
      ])

      const uploadsData = await uploadsRes.json()
      const chatsData = await chatsRes.json()
      const statsData = await statsRes.json()

      return {
        uploads: uploadsData.uploads.map((u: Record<string, unknown>) => ({
          ...u,
          timestamp: new Date(u.timestamp as string)
        })),
        chats: chatsData.chats.map((c: Record<string, unknown>) => ({
          ...c,
          createdAt: new Date(c.createdAt as string)
        })),
        stats: statsData
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
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
    }
  },

  // Add a new upload to history
  async addUpload(userId: string, upload: Omit<UploadHistory, 'id' | 'timestamp'> & { imagePath?: string | null }): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/uploads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          file_name: upload.fileName,
          image_path: upload.imagePath,
          prediction_class: upload.predictionClass,
          severity: upload.severity,
          confidence_healthy: upload.confidence.healthy,
          confidence_diseased: upload.confidence.diseased,
          summary: upload.summary
        })
      })

      const data = await response.json()
      return data.id
    } catch (error) {
      console.error('Error adding upload:', error)
      throw error
    }
  },

  // Add a new chat session to history
  async addChat(userId: string, sessionId: string): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId
        })
      })

      const data = await response.json()
      return data.id
    } catch (error) {
      console.error('Error adding chat:', error)
      throw error
    }
  },

  // Add a message to a chat
  async addChatMessage(chatId: string, role: 'user' | 'assistant', content: string): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/api/chat-messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: chatId,
          role,
          content
        })
      })
    } catch (error) {
      console.error('Error adding chat message:', error)
      throw error
    }
  }
}