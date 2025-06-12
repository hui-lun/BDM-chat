<template>
  <div class="chat-body" ref="chatBody">
    <div v-for="(msg, idx) in parsedMessages" :key="idx" :class="['msg-row', msg.sender]">
      <div :class="['msg-bubble', msg.sender]">
        <div v-if="msg.loading" class="loading-dots">
          <span></span><span></span><span></span>
        </div>

        <div v-if="msg.chartData" class="chart-container">
          <img :src="msg.chartData.imageUrl" alt="BDM 狀態圖表" class="chart-image" />
        </div>

        <div v-else>
          <div class="message-text" v-html="msg.parsedHtml"></div>
          <button v-if="msg.isEmail" class="draft-btn" @click="generateDraft(msg)">產生草稿</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onUpdated, ref, computed } from 'vue'
import { marked } from 'marked'

// 配置 marked 來保留換行符
marked.setOptions({
  breaks: true,  // 將單個換行符轉換為 <br>
  gfm: true      // 啟用 GitHub Flavored Markdown
})

const props = defineProps({
  messages: Array
})

const chatBody = ref(null)

const parsedMessages = computed(() =>
  props.messages.map(msg => ({
    ...msg,
    parsedHtml: (() => {
      // 確保 text 是字符串類型
      let textContent = msg.text || ''
      
      // 如果是數組，轉換為字符串
      if (Array.isArray(textContent)) {
        textContent = textContent.join('\n')
      }
      
      // 確保是字符串類型
      if (typeof textContent !== 'string') {
        textContent = String(textContent)
      }
      
      return marked.parse(textContent)
    })()
  }))
)

const emit = defineEmits(['open-draft-form'])

const generateDraft = (msg) => {
  if (!msg.mailInfo) return

  // 確保 text 是字符串類型
  let textContent = msg.text || ''
  
  // 如果是數組，轉換為字符串
  if (Array.isArray(textContent)) {
    textContent = textContent.join('\n')
  }
  
  // 確保是字符串類型
  if (typeof textContent !== 'string') {
    textContent = String(textContent)
  }

  const subject = `Re: ${msg.mailInfo.title || 'No Subject'}`
  const draftTemplate = `Dear ${msg.mailInfo.customer},

Thank you for your inquiry. Based on your request:

${textContent}

If you have any questions, please feel free to contact me. 
Thank you!

Best regards,
${msg.mailInfo.BDM}`

  emit('open-draft-form', draftTemplate)
}

onUpdated(() => {
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
})
</script>

<style scoped>
.message-text {
  white-space: normal;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 0.95rem;
}

.message-text h1,
.message-text h2,
.message-text h3 {
  font-weight: bold;
  margin: 10px 0 5px;
}

.message-text ::v-deep p {
  margin: 3px !important;
}

.message-text ul {
  padding-left: 1.5rem;
  margin: 6px 0;
}

.message-text li {
  margin: 4px 0;
}

.message-text strong {
  font-weight: bold;
}

.message-text em {
  font-style: italic;
}

.message-text code {
  background-color: #f3f3f3;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}

.chart-container {
  margin: 10px 0;
  max-width: 100%;
  overflow: hidden;
}

.loading-dots span {
  display: inline-block;
  width: 4px;
  height: 4px;
  background-color: #666;
  border-radius: 50%;
  margin: 0 2px;
  animation: typing 1s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: 0.2s; }
.loading-dots span:nth-child(2) { animation-delay: 0.3s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
</style>
