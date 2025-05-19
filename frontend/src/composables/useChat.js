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
      userMsg = `Subject: ${mailInfo.title}
      From: ${mailInfo.customer}
      To: ${mailInfo.BDM}
      Date: ${mailInfo.dateTime}

      ${mailInfo.body}`
      messages.value.push({ sender: 'user', text: userMsg })
    } else {
      if (!query.value.trim()) return
      userMsg = query.value
      // userMsg = query.value.replace(/<br>/g, '\n')
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

  return {
    query,
    messages,
    isLoading,
    useAgent,
    chatBody,
    sendQuery,
    stopGenerating,
    scrollToBottom
  }
}
