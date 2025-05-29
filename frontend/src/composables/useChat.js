import { ref, nextTick, watch } from 'vue'
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

export function useChat(chatHistory) {
  const query = ref('')
  const messages = ref([])
  const isLoading = ref(false)
  const useAgent = ref(true)
  const currentMailInfo = ref(null)  // Store current mail info
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
      
      // Add to history
      chatHistory.value.unshift(newChat);
      console.log('Saved chat to history:', newChat);
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
      userMsg = `Subject: ${mailInfo.title}
      From: ${mailInfo.customer}
      To: ${mailInfo.BDM}
      Date: ${mailInfo.dateTime}

      ${mailInfo.body.trim()}`
      messages.value.push({ sender: 'user', text: userMsg })
    } else {
      if (!query.value.trim()) return
      userMsg = query.value
      userMsg = query.value.replace(/<br>/g, '\n')
      messages.value.push({ sender: 'user', text: query.value })
      query.value = ''
    }
    messages.value.push({ sender: 'ai', loading: true })
  
    isLoading.value = true
  
    try {
      controller = new AbortController()
      let res
      if (useAgent.value) {
        res = await axios.post('/agent-chat', { agent_query: userMsg }, { signal: controller.signal })
        // add
        const responseData = res.data.summary || res.data.response || ''
        let parsedResponse = {}
        try {
          // 嘗試解析 JSON 字符串
          parsedResponse = typeof responseData === 'string' ? 
                          JSON.parse(responseData) : 
                          responseData
        } catch (e) {
          // 如果不是 JSON，則當作普通文本處理
          parsedResponse = { 
            type: 'text', 
            message: responseData 
          }
        }
        if (parsedResponse.type === 'chart' && parsedResponse.chart_data) {
          messages.value[messages.value.length - 1] = {
            sender: 'ai',
            text: parsedResponse.message,
            chartData: {
              imageUrl: parsedResponse.chart_data,
              contentType: parsedResponse.content_type || 'image/png',
              cleanup: () => {}  // 不需要清理，因為是 base64 數據
            }
          }
          return
        }
        // add
        const isEmail = res.data.from_email === true
        messages.value[messages.value.length - 1] = { 
          sender: 'ai', 
          text: res.data.summary, 
          isEmail,
          mailInfo: isEmail ? currentMailInfo.value : null
        }
      } else {
        res = await axios.post('/chat', { query: userMsg }, { signal: controller.signal })
        messages.value[messages.value.length - 1] = { sender: 'ai', text: res.data.response }
      }
    } catch (e) {
      if (axios.isCancel(e)) {
        messages.value[messages.value.length - 1] = { sender: 'ai', text: '(已停止生成)' }
      } else {
        messages.value[messages.value.length - 1] = { sender: 'ai', text: 'Error: ' + e.message }
      }
    } finally {
      try {
        isLoading.value = false;
        controller = null;
        
        // Save to history after sending a message
        if (messages.value && messages.value.length > 0) {
          console.log('Attempting to save chat to history...');
          const savedChat = saveToHistory();
          console.log('Chat save result:', savedChat ? 'success' : 'failed');
        }
      } catch (error) {
        console.error('Error in sendQuery finally block:', error);
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
  }

  return {
    query,
    messages,
    isLoading,
    useAgent,
    chatBody,
    sendQuery,
    stopGenerating,
    scrollToBottom,
    clearMessages
  }
}
