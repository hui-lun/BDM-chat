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
  const saveToHistory = async () => {
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
      
      // Generate title based on the first user message
      let title = "New Chat";
      const firstUserMessage = messages.value.find(msg => msg.sender === 'user');
      
      if (firstUserMessage && firstUserMessage.text) {
        try {
          const response = await fetch('/generate-title', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ first_message: firstUserMessage.text })
          });
          
          if (response.ok) {
            const result = await response.json();
            title = result.title || "New Chat";
            console.log('Generated title:', title);
          } else {
            console.warn('Failed to generate title, using fallback');
          }
        } catch (error) {
          console.error('Error generating title:', error);
        }
      }
      
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

  // Unified text processing function
  const processTextResponse = (accumulatedText, isEmail) => {
    messages.value[messages.value.length - 1] = {
      sender: 'ai',
      text: accumulatedText,
      isEmail,
      mailInfo: isEmail ? currentMailInfo.value : null,
      loading: false
    }
  }

  // Unified chart processing function
  const processChartResponse = (accumulatedText, isEmail) => {
    try {
      console.log('[frontend] Attempting to parse chart data:', accumulatedText.substring(0, 100) + '...')
      const parsedResponse = JSON.parse(accumulatedText)
      console.log('[frontend] Parsed response:', parsedResponse)
      
      if (parsedResponse.type === 'chart' && parsedResponse.chart_data) {
        console.log('[frontend] Chart data complete, updating message')
        
        // 解析 base64 编码的 JSON 数据
        const base64Data = parsedResponse.chart_data.replace('data:application/json;base64,', '')
        const decodedData = JSON.parse(atob(base64Data))
        
        messages.value[messages.value.length - 1] = {
          sender: 'ai',
          text: decodedData.message || '圖表已生成',
          chartData: {
            imageUrl: decodedData.chart_image,
            contentType: 'image/png',
            cleanup: () => {}
          },
          isEmail,
          mailInfo: isEmail ? currentMailInfo.value : null,
          loading: false
        }
        
        console.log('[frontend] Message updated with chartData:', messages.value[messages.value.length - 1])
        return true // 表示成功處理了 chart
      }
      
      console.log('[frontend] Not a valid chart response:', parsedResponse)
    } catch (parseError) {
      console.log('[frontend] Failed to parse chart data:', parseError)
    }
    return false
  }


  
  // Support mailInfo object structure
  const sendQuery = async (mailInfo = null) => {
    let userMsg
    console.log('[DEBUG] useAgent:', useAgent.value)
    if (mailInfo) {
      // Format email info as a string
      currentMailInfo.value = mailInfo  // Save mailInfo
      // mailInfo.body = mailInfo.body.replaceAll('\r\n\r\n', '\r\n')

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
        let jsonBuffer = ''  // Buffer for accumulating incomplete JSON

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (!line.trim()) continue
            
            // Add current line to JSON buffer
            jsonBuffer += line
            console.log(jsonBuffer)
            try {
              const data = JSON.parse(jsonBuffer)
              console.log('[frontend] Received data:', data)
              
              // Clear buffer after successful parsing
              jsonBuffer = ''
          
              if (data.from_email !== undefined) {
                console.log('[frontend] Received from_email flag:', data.from_email)
                isEmail = data.from_email
              } else if (data.summary !== undefined) {
                console.log('[frontend] Received summary chunk:', data.summary)
                accumulatedText += data.summary

                // Check if it's a chart response
                if (accumulatedText.includes('"type": "chart"')) {
                  console.log('[frontend] Detected chart response')
                  
                  if (processChartResponse(accumulatedText, isEmail)) {
                    console.log("chart processed successfully")
                    break
                  }
                }

                // Normal processing for non-chart responses
                if (isFirstToken) {
                  isFirstToken = false
                  console.log('[frontend] First token, updating message')
                  processTextResponse(accumulatedText, isEmail)
                } else {
                  // Just update the text
                  console.log('[frontend] Updating message text')
                  messages.value[messages.value.length - 1].text = accumulatedText
                  await nextTick()
                }
              }
            } catch (e) {
              // JSON parsing failed, possibly due to incomplete data, continue accumulating
              console.log("keep adding json info")
              continue
            }
          }
          
          // If chart has been processed, break out of outer loop
          if (messages.value[messages.value.length - 1].chartData) {
            break
          }
        }

        // Final check: if chart not processed, handle as text
        if (!messages.value[messages.value.length - 1].chartData) {
          console.log("i will go there")
          processTextResponse(accumulatedText, isEmail)
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
                  processTextResponse(accumulatedText, false) // No email info in non-agent mode
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
        processTextResponse(accumulatedText, false) // No email info in non-agent mode
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
          const savedChat = await saveToHistory()
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