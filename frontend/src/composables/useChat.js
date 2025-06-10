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

  // Support mailInfo object structure
  const sendQuery = async (mailInfo = null) => {
    let userMsg
    console.log('[DEBUG] useAgent:', useAgent.value)
    if (mailInfo) {
      // Format email info as a string
      currentMailInfo.value = mailInfo  // Save mailInfo
      mailInfo.body = mailInfo.body.replaceAll('\r\n\r\n', '\r\n')

      userMsg = [
        `Subject: ${mailInfo.title}`,
        `From: ${mailInfo.customer}`,
        `To: ${mailInfo.BDM}`,
        `Date: ${mailInfo.dateTime}`,
        '',
        `${mailInfo.body.trim()}`
      ].join('\n');

      messages.value.push({ sender: 'user', text: userMsg })
      console.log(mailInfo)
    } else {
      if (!query.value.trim()) return
      userMsg = query.value
      userMsg = query.value.replace(/<br>/g, '\n')
      messages.value.push({ sender: 'user', text: query.value })
      query.value = ''
    }
    // Initial loading state
    messages.value.push({ sender: 'ai', loading: true })
  
    isLoading.value = true
  
    try {
      controller = new AbortController()
      let res
      if (useAgent.value) {
        controller = new AbortController()

        const response = await fetch('/agent-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_query: userMsg }),
          signal: controller.signal
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let accumulatedText = ''
        let isFirstToken = true
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
              console.log('[frontend] Received data:', data)
          
              if (data.from_email !== undefined) {
                console.log('[frontend] Received from_email flag:', data.from_email)
                isEmail = data.from_email
              } else if (data.summary !== undefined) {
                console.log('[frontend] Received summary chunk:', data.summary)
                accumulatedText += data.summary
                console.log('[frontend] Accumulated text so far:', accumulatedText)

                // 判斷是否為 chart
                let parsedResponse
                try {
                  parsedResponse = JSON.parse(accumulatedText)
                } catch {
                  parsedResponse = { type: 'text', message: accumulatedText }
                }

                if (
                  parsedResponse.type === 'chart' &&
                  parsedResponse.chart_data
                ) {
                  console.log("i'm chart")
                  messages.value[messages.value.length - 1] = {
                    sender: 'ai',
                    text: parsedResponse.message,
                    chartData: {
                      imageUrl: parsedResponse.chart_data,
                      contentType: parsedResponse.content_type || 'image/png',
                      cleanup: () => {}
                    }
                  }
                  // return
                }

                if (isFirstToken) {
                  isFirstToken = false
                  console.log('[frontend] First token, updating message')
                  messages.value[messages.value.length - 1] = {
                    sender: 'ai',
                    text: accumulatedText,
                    isEmail,
                    mailInfo: isEmail ? currentMailInfo.value : null,
                    loading: false
                  }
                } else {
                  // Just update the text
                  console.log('[frontend] Updating message text')
                  messages.value[messages.value.length - 1].text = accumulatedText
                  await nextTick()
                }
              }
            } catch (e) {
              console.error('Error parsing streaming response:', line, e)
            }
          }
        }

        // 最終補上最後一次更新（保險）
        messages.value[messages.value.length - 1] = {
          sender: 'ai',
          text: accumulatedText,
          isEmail,
          mailInfo: isEmail ? currentMailInfo.value : null,
          loading: false
        }
      }
      
      else {
        // Handle streaming chat response
        console.time("chatRequest")
        console.log("start to post")
        
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
        let accumulatedText = ''
        let isFirstToken = true

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
                accumulatedText += data.token
                // On first token, remove loading state
                if (isFirstToken) {
                  isFirstToken = false
                  messages.value[messages.value.length - 1] = {
                    sender: 'ai',
                    text: accumulatedText,
                    loading: false
                  }
                } else {
                  // Just update the text
                  messages.value[messages.value.length - 1].text = accumulatedText
                }
              }
            } catch (e) {
              console.error('Error parsing streaming response:', e)
            }
          }
        }

        console.log("get answer")
        console.timeEnd("chatRequest")
        
        // Final update
        messages.value[messages.value.length - 1] = {
          sender: 'ai',
          text: accumulatedText,
          loading: false
        }
      }
    } catch (e) {
      // Handle all stop generation cases in one place
      if (e.name === 'AbortError' || axios.isCancel(e)) {
        messages.value[messages.value.length - 1] = { 
          sender: 'ai', 
          text: '(已停止生成)', 
          loading: false 
        }
      } else {
        messages.value[messages.value.length - 1] = { 
          sender: 'ai', 
          text: 'Error: ' + e.message, 
          loading: false 
        }
      }
    } finally {
      try {
        isLoading.value = false
        controller = null
        
        // Save to history after sending a message
        if (messages.value && messages.value.length > 0) {
          console.log('Attempting to save chat to history...')
          const savedChat = saveToHistory()
          console.log('Chat save result:', savedChat ? 'success' : 'failed')
        }
      } catch (error) {
        console.error('Error in sendQuery finally block:', error)
      }
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
    sendQuery,
    stopGenerating,
    scrollToBottom,
    clearMessages,
    saveToHistory
  }
}
