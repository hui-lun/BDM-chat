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
          // analyze json string
          parsedResponse = typeof responseData === 'string' ? 
                          JSON.parse(responseData) : 
                          responseData
        } catch (e) {
          // if it's not json, take it as a normal text
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
              cleanup: () => {}  
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
        console.time("chatRequest")
        console.log("start to post")
        res = await axios.post('/chat', { query: userMsg }, { signal: controller.signal })
        console.log("get answer")
        console.timeEnd("chatRequest")
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
