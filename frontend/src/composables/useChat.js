import { ref, nextTick, watch } from 'vue'
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

export function useChat(chatHistory) {
  const query = ref('')
  const messages = ref([])
  const isLoading = ref(false)
  const useAgent = ref(true)
  const currentMailInfo = ref(null)  // Store current mail info
  const activeChatId = ref(null)  // Track the active chat ID to prevent duplicate history entries
  let controller = null
  const chatBody = ref(null)

  // Automatically scroll to the bottom when messages change
  const scrollToBottom = () => {
    nextTick(() => {
      if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
    })
  }
  watch(messages, scrollToBottom, { deep: true })

  // Save current chat to history
  const saveToHistory = () => {
    try {
      if (!chatHistory || !chatHistory.value) {
        console.warn('Chat history not available');
        return null;
      }
      
      if (!messages.value || messages.value.length === 0) {
        console.warn('No messages to save');
        return null;
      }
      
      // If we have an active chat ID, update that chat instead of creating a new one
      if (activeChatId.value) {
        // Find the index of the active chat in the history
        const activeIdx = chatHistory.value.findIndex(chat => chat.id === activeChatId.value);
        
        if (activeIdx !== -1) {
          // Update the existing chat with the current messages
          chatHistory.value[activeIdx].messages = [...messages.value];
          console.log('Updated existing chat in history:', chatHistory.value[activeIdx]);
          
          // Save the updated history to localStorage if available
          if (typeof localStorage !== 'undefined' && typeof saveHistoryToLocalStorage === 'function') {
            saveHistoryToLocalStorage();
          }
          
          return chatHistory.value[activeIdx];
        }
      }
      
      // If no active chat or active chat not found, create a new one
      const now = new Date();
      const timeString = now.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
      const dateString = now.toISOString().split('T')[0];
      const title = `對話 ${dateString} ${timeString}`;
      
      // Create a new chat history entry
      const newChat = {
        id: uuidv4(),
        title,
        time: timeString,
        messages: [...messages.value],
        createdAt: now.toISOString()
      };
      
      // Set this as the active chat
      activeChatId.value = newChat.id;
      
      // Add to history
      chatHistory.value.unshift(newChat);
      console.log('Saved new chat to history:', newChat);
      
      // Save the updated history to localStorage if available
      if (typeof localStorage !== 'undefined' && typeof saveHistoryToLocalStorage === 'function') {
        saveHistoryToLocalStorage();
      }
      
      return newChat;
    } catch (error) {
      console.error('Error saving chat history:', error);
      return null;
    }
  }

  const sendMessage = async (userMsg) => {
    if (!userMsg.trim()) return

    messages.value.push({ sender: 'user', text: userMsg })
    messages.value.push({ sender: 'ai', text: '' })  // Initialize empty AI message
    isLoading.value = true  // Set loading state

    try {
      controller = new AbortController()
      let res
      if (useAgent.value) {
        console.time("agentChatRequest")
        console.log("start to post agent chat")
        
        // Use fetch for streaming
        const response = await fetch('/agent-chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ agent_query: userMsg }),
          signal: controller.signal
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let aiResponse = ''
        let isEmail = false

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (!line.trim()) continue
            try {
              const data = JSON.parse(line)
              if (data.error) {
                throw new Error(data.error)
              }
              if (data.token) {
                aiResponse += data.token
                isEmail = data.from_email || false
                // Update the last message with the accumulated response
                messages.value[messages.value.length - 1] = { 
                  sender: 'ai', 
                  text: aiResponse,
                  isEmail,
                  mailInfo: isEmail ? currentMailInfo.value : null
                }
              }
            } catch (e) {
              console.error('Error parsing streaming response:', e)
            }
          }
        }
        
        console.timeEnd("agentChatRequest")
      } else {
        console.time("chatRequest")
        console.log("start to post")
        
        // Use fetch for streaming
        const response = await fetch('/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: userMsg }),
          signal: controller.signal
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let aiResponse = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (!line.trim()) continue
            try {
              const data = JSON.parse(line)
              if (data.error) {
                throw new Error(data.error)
              }
              if (data.token) {
                aiResponse += data.token
                // Update the last message with the accumulated response
                messages.value[messages.value.length - 1] = { 
                  sender: 'ai', 
                  text: aiResponse 
                }
              }
            } catch (e) {
              console.error('Error parsing streaming response:', e)
            }
          }
        }
        
        console.timeEnd("chatRequest")
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted')
        messages.value[messages.value.length - 1] = { 
          sender: 'ai', 
          text: '(已停止生成)' 
        }
      } else {
        console.error('Error:', error)
        messages.value[messages.value.length - 1] = { 
          sender: 'ai', 
          text: 'Sorry, there was an error processing your request.' 
        }
      }
    } finally {
      isLoading.value = false  // Reset loading state
      controller = null
    }
  }

  // Stop the AI response generation
  const stopGenerating = () => {
    if (controller) controller.abort()
    isLoading.value = false
    controller = null
  }

  // Clear all chat messages
  const clearMessages = () => {
    messages.value = []
    currentMailInfo.value = null
    // Reset the active chat ID when clearing messages
    activeChatId.value = null
  }

  return {
    query,
    messages,
    isLoading,
    useAgent,
    chatBody,
    activeChatId,
    sendMessage,
    stopGenerating,
    scrollToBottom,
    clearMessages,
    saveToHistory
  }
}
