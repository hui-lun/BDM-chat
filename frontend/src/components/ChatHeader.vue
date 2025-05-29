<template>
  <div class="chat-header">
    <div class="logo">
      <span>BDM.Agent</span>
    </div>
    <div class="header-icons">
      <span 
        class="icon" 
        @click="$emit('open-history-menu')" 
        title="歷史紀錄"
      >
        📜
      </span>
      <button 
        v-if="currentTitle" 
        class="qa-button" 
        @click="openQASidebar"
        title="問答歷史"
      >
        <span class="icon">❓</span>
        <span class="button-text">問答歷史</span>
      </button>
      <span 
        class="icon" 
        @click="$emit('clear-messages')" 
        title="清除聊天紀錄"
      >
        🗑️
      </span>
      <span 
        class="icon" 
        @click="$emit('send-email-content')" 
        title="傳入信件內容"
      >
        ✉️
      </span>
      <a 
        class="icon" 
        href="https://192.168.1.193:8443/" 
        target="_blank" 
        title="以新分頁開啟"
      >
        🌐
      </a>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  currentTitle: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['open-qa-sidebar'])

const openQASidebar = () => {
  if (props.currentTitle) {
    emit('open-qa-sidebar', props.currentTitle)
  }
}
</script>

<style scoped>
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  height: 50px;
}

.logo {
  font-weight: bold;
  font-size: 1.2rem;
}

.header-icons {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.icon {
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.7;
  transition: all 0.2s;
  background: none;
  border: none;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.icon:hover {
  opacity: 1;
  background-color: rgba(0, 0, 0, 0.05);
}

.qa-button {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.qa-button:hover {
  background: #dee2e6;
}

.button-text {
  font-size: 0.8rem;
  margin-left: 2px;
}
</style>
