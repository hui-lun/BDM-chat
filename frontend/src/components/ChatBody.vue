<template>
  <div class="chat-body" ref="chatBody">
    <div v-for="(msg, idx) in messages" :key="idx" :class="['msg-row', msg.sender]">
      <div :class="['msg-bubble', msg.sender]">
        <div v-if="msg.loading" class="loading-dots">
          <span></span><span></span><span></span>
        </div>
        <div v-else>
          <div class="message-text" v-html="msg.text"></div>
          <button v-if="msg.isEmail" class="draft-btn" @click="generateDraft(msg)">產生草稿</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onUpdated, ref } from 'vue'
const props = defineProps({
  messages: Array
})
const chatBody = ref(null)

const emit = defineEmits(['open-draft-form'])

const generateDraft = (msg) => {
  if (!msg.mailInfo) return
  
  const subject = `Re: ${msg.mailInfo.title || 'No Subject'}`
  const draftTemplate = `Dear ${msg.mailInfo.customer}, 

    Thank you for your inquiry. Based on your request:
    <br>

    ${msg.text}

    <br>
    If you have any questions, please feel free to contact me. 
    Thank you!
    
    <br>
    ${msg.mailInfo.BDM}`

  emit('open-draft-form', draftTemplate)
  //emit('open-draft-form', subject, draftTemplate, msg.mailInfo.customerEmail)
}

onUpdated(() => {
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
})
</script>

<style scoped>
.message-text {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
