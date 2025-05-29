import { ref, nextTick, watch } from 'vue'
import axios from 'axios'

export function useChat() {
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

  // Support mailInfo object structure
  const sendQuery = async (mailInfo = null) => {
    let userMsg
    console.log('[DEBUG] useAgent:', useAgent.value)
    if (mailInfo) {
      // Format email info as a string
      currentMailInfo.value = mailInfo  // Save mailInfo
      mailInfo.body = mailInfo.body.replaceAll('\r\n\r\n', '\r\n')
      // userMsg = `Subject: ${mailInfo.title}
      // From: ${mailInfo.customer}
      // To: ${mailInfo.BDM}
      // Date: ${mailInfo.dateTime}

      // ${mailInfo.body.trim()}`
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
      isLoading.value = false
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
