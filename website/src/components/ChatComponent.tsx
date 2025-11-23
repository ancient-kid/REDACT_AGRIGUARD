import { useState, useEffect, useRef } from 'react'
import { useUser } from '@clerk/clerk-react'
import { agriGuardAPI } from '../services/api'
import type { ChatMessage, PipelineResult } from '../services/api'
import { dashboardStorage } from '../services/dashboardStorage'
import '../App.css'

interface ChatPanelProps {
  analysisContext: PipelineResult;
  onClose: () => void;
}

export function ChatPanel({ analysisContext, onClose }: ChatPanelProps) {
  const { user } = useUser()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [chatId, setChatId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scrollProgress, setScrollProgress] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Initialize chat session
  useEffect(() => {
    initializeChat()
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
    updateScrollProgress()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const updateScrollProgress = () => {
    const container = messagesContainerRef.current
    if (!container) return

    const scrollHeight = container.scrollHeight - container.clientHeight
    if (scrollHeight <= 0) {
      setScrollProgress(100)
      return
    }

    const progress = (container.scrollTop / scrollHeight) * 100
    setScrollProgress(Math.round(progress))
  }

  const handleSliderChange = (value: number) => {
    const container = messagesContainerRef.current
    if (!container) return

    const scrollHeight = container.scrollHeight - container.clientHeight
    container.scrollTop = (value / 100) * scrollHeight
    setScrollProgress(value)
  }

  const initializeChat = async () => {
    setIsInitializing(true)
    setError(null)
    
    try {
      const response = await agriGuardAPI.initializeChat(analysisContext)
      setSessionId(response.session_id)
      const initialMessages = [{
        role: 'assistant' as const,
        content: response.initial_message,
        timestamp: new Date().toISOString()
      }]
      setMessages(initialMessages)

      // Save chat to dashboard if user is signed in
      if (user?.id && user.emailAddresses?.[0]?.emailAddress) {
        await dashboardStorage.ensureUser(
          user.id,
          user.emailAddresses[0].emailAddress,
          user.firstName || undefined,
          user.lastName || undefined
        )
        
        const dbChatId = await dashboardStorage.addChat(user.id, response.session_id)
        setChatId(dbChatId)
        
        // Add initial assistant message
        await dashboardStorage.addChatMessage(dbChatId, 'assistant', response.initial_message)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize chat')
    } finally {
      setIsInitializing(false)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!inputMessage.trim() || !sessionId || isSending) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setIsSending(true)
    setError(null)

    // Add user message immediately
    const userMsg: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMsg])

    try {
      const response = await agriGuardAPI.sendChatMessage(sessionId, userMessage)
      
      // Add assistant response
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      }
      const updatedMessages = [...messages, userMsg, assistantMsg]
      setMessages(updatedMessages)

      // Save messages to database if user is signed in
      if (user?.id && chatId) {
        await dashboardStorage.addChatMessage(chatId, 'user', userMessage)
        await dashboardStorage.addChatMessage(chatId, 'assistant', response.response)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
      // Remove the user message if sending failed
      setMessages(prev => prev.slice(0, -1))
      setInputMessage(userMessage) // Restore the message
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(e)
    }
  }

  return (
    <div className="chat-overlay">
      <div className="chat-panel">
        <div className="chat-header">
          <div className="chat-title">
            <span className="chat-icon">💬</span>
            <div>
              <h3>AgriGuard Assistant</h3>
              <p className="chat-subtitle">Ask questions about your plant health analysis</p>
            </div>
          </div>
          <button className="chat-close-btn" onClick={onClose}>✕</button>
        </div>

        <div
          className="chat-messages"
          ref={messagesContainerRef}
          onScroll={updateScrollProgress}
        >
          {isInitializing && (
            <div className="chat-loading">
              <div className="spinner"></div>
              <p>Initializing chat session...</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? '👨‍🌾' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-text">{msg.content}</div>
                <div className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            </div>
          ))}

          {isSending && (
            <div className="chat-message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="chat-error">
              ⚠️ {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-slider">
          <label htmlFor="chat-slider-input">Conversation Slider</label>
          <input
            id="chat-slider-input"
            type="range"
            min={0}
            max={100}
            value={scrollProgress}
            onChange={(e) => handleSliderChange(Number(e.target.value))}
          />
        </div>

        <form className="chat-input-form" onSubmit={handleSendMessage}>
          <textarea
            className="chat-input"
            placeholder="Ask about treatments, prevention, or plant care..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isSending || isInitializing || !sessionId}
            rows={2}
          />
          <button 
            type="submit" 
            className="chat-send-btn"
            disabled={!inputMessage.trim() || isSending || isInitializing || !sessionId}
          >
            {isSending ? '⏳' : '📤'}
          </button>
        </form>

        <div className="chat-footer">
          <span className="footer-note">
            💡 Tip: Ask about organic treatments, prevention methods, or specific symptoms
          </span>
        </div>
      </div>
    </div>
  )
}