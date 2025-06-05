<template>
  
  <div v-if="loading" class="loading-screen">
    <div class="spinner"></div>
  </div>

  <div class="chat-app">
    <div v-if="showError" class="error-popup">
      {{ errorMsg }}
    </div>
    
    
    <!-- Chat history menu -->
    <ChatHistoryMenu
      :show="showHistoryMenu"
      :history="chatHistory"
      :show-delete-modal="showDeleteModal"
      :show-delete-success="showDeleteSuccess"
      :delete-popover-pos="deletePopoverPos"
      :delete-popover-style="deletePopoverStyle"
      :menu-idx="menuIdx"               
      :edit-idx="editIdx"
      :selected-history-idx="selectedHistoryIdx"
      :rename-input="renameTitle"
      @select="selectHistory"
      @close="closeHistoryMenu"
      @close-delete="closeDeleteModal"
      @confirm-delete="doDeleteHistory"
      @toggle-menu="toggleMenu"
      @start-rename="startRename"
      @finish-rename="finishRename"
      @update-rename-input="updateRenameInput"
      @open-delete-modal="openDeleteModal"
    />

    <!-- Q&A History Sidebar -->
    <QASidebar
      :is-visible="showQASidebar"
      :title="currentTitle"
      @close="closeQASidebar"
    />



    <!-- chatbot Header -->
    <ChatHeader
      @open-history-menu="openHistoryMenu"
      @close-history-menu="closeHistoryMenu"
      @clear-messages="clearMessages"
      @send-email-content="sendEmailContent"
      @open-qa-sidebar="openQASidebar"
      :current-title="currentTitle"
    />

    <!-- Chatbot content-->
    <ChatBody
      :messages="messages"
      @open-draft-form="openDraftForm"
    />

    <!-- AI Assistant Toggle -->


    <!-- Chat input area -->
    <ChatFooter
      v-model="query"
      :isLoading="isLoading"
      v-model:useAgent="useAgent"   
      @send-message="handleButtonClick"
    />
  </div>
</template>


<script setup>
import { ref, nextTick, onMounted, computed , watch} from 'vue'
import ChatHeader from './components/ChatHeader.vue'
import ChatBody from './components/ChatBody.vue'
import ChatFooter from './components/ChatFooter.vue'
import ChatHistoryMenu from './components/ChatHistoryMenu.vue'
import QASidebar from './components/QASidebar.vue'
import { useChat } from './composables/useChat'
import { useOutlook } from './composables/useOutlook'
import { useDrawer } from './composables/useDrawer'

localStorage.setItem('should-restore-chat', 'true')

// Current title for Q&A history
const currentTitle = ref('')
const showQASidebar = ref(false)

// Initialize chat history state
const chatHistory = ref([])

// ====== Chat State and API Handling ======
const {
  query,
  messages,
  isLoading,
  useAgent,
  chatBody,
  activeChatId: chatActiveChatId,
  sendMessage,
  stopGenerating,
  scrollToBottom,
  clearMessages,
  saveToHistory
} = useChat(chatHistory)

// ====== Drawer Management (composable) ======
const {
  showHistoryMenu,
  selectedHistoryIdx,
  chatHistory: drawerChatHistory,
  menuIdx,
  editIdx,
  renameTitle,
  renameInput,
  showDeleteModal,
  showDeleteSuccess,
  deletePopoverPos,
  deletePopoverStyle,
  activeChatId: drawerActiveChatId,
  openHistoryMenu,
  closeHistoryMenu,
  selectHistory,
  toggleMenu,
  closeMenu,
  startRename,
  updateRenameInput,
  finishRename,
  openDeleteModal,
  closeDeleteModal,
  doDeleteHistory,
  saveHistoryToLocalStorage
} = useDrawer(messages)

// Sync chatHistory between composables
watch(chatHistory, (newVal) => {
  if (drawerChatHistory && drawerChatHistory.value !== newVal) {
    drawerChatHistory.value = newVal;
  }
}, { deep: true, immediate: true })

// Sync activeChatId between useChat and useDrawer
watch(drawerActiveChatId, (newVal) => {
  if (chatActiveChatId && chatActiveChatId.value !== newVal) {
    chatActiveChatId.value = newVal;
  }
}, { deep: true, immediate: true })

watch(chatActiveChatId, (newVal) => {
  if (drawerActiveChatId && drawerActiveChatId.value !== newVal) {
    drawerActiveChatId.value = newVal;
  }
}, { deep: true, immediate: true })

// Open/close Q&A sidebar
const openQASidebar = (title) => {
  currentTitle.value = title
  showQASidebar.value = true
  closeHistoryMenu()
}

const closeQASidebar = () => {
  showQASidebar.value = false
}

const loading = ref(true) // Plugin readiness loading

// ====== Error Message State ======
const showError = ref(false)
const errorMsg = ref('')

// Show error popup with a message
function showErrorMessage(msg) {
  errorMsg.value = msg
  showError.value = true
  setTimeout(() => {
    showError.value = false
    errorMsg.value = ''
  }, 3000)
}


// ====== Outlook/Draft Related Processing ======
const {
  handleEmailChange,
  sendEmailContent,
  openDraftForm,
} = useOutlook(showErrorMessage, query, sendMessage)

console.log("initial loading:", loading.value)
// ====== Initial setup when mounted ======
onMounted(() => {
  document.addEventListener('click', closeMenuOnOutside)

  const preload = document.getElementById('preload-loading')
  if (preload) preload.remove()

  // 確保 useAgent 永遠為 true
  useAgent.value = true

  watch([messages, useAgent, selectedHistoryIdx], ([newMessages, agent, idx]) => {
    try {
      const payload = {
        messages: newMessages,
        useAgent: agent,
        selectedHistoryIdx: idx,
      }
      localStorage.setItem('cached-chat-session', JSON.stringify(payload))
      // 開發用 log
      console.log('[watch] 快取聊天紀錄已更新')
    } catch (e) {
      console.error('[watch] 儲存聊天紀錄失敗', e)
    }
  }, { deep: true })



  // ========= 🌟 還原流程 =========
  const shouldRestore = localStorage.getItem('should-restore-chat') === 'true'
  console.log('[Mounted] shouldRestore =', shouldRestore)

  if (shouldRestore) {
    const cached = localStorage.getItem('cached-chat-session')
    console.log('[Mounted] 嘗試還原 cached-chat-session =', cached)

    if (cached) {
      try {
        const parsed = JSON.parse(cached)
        if (parsed.messages) {
          messages.value = parsed.messages
          console.log('[Mounted] 還原 messages：', parsed.messages)
        }
        // 強制將 useAgent 設為 true，忽略儲存的值
        useAgent.value = true
        console.log('[Mounted] 強制設定 useAgent 為 true')
        if (parsed.selectedHistoryIdx !== undefined) {
          selectedHistoryIdx.value = parsed.selectedHistoryIdx
          console.log('[Mounted] 還原 selectedHistoryIdx：', parsed.selectedHistoryIdx)
        }
      } catch (e) {
        console.error('[Mounted] 聊天還原失敗', e)
      }
    } else {
      console.warn('[Mounted] 找不到快取聊天紀錄')
    }

    localStorage.removeItem('should-restore-chat')
    console.log('[Mounted] 移除 should-restore-chat flag')
  } else {
    console.log('[Mounted] 無需還原聊天紀錄')
  }


  
  if (typeof Office === 'undefined') {
    loading.value = false; // 本地開發直接顯示內容
    return;
  }
  Office.onReady(() => {
    loading.value = false;
    // 監聽信件切換事件，確保每次切信都抓到最新內容
    if (Office.context.mailbox && Office.context.mailbox.addHandlerAsync) {
      Office.context.mailbox.addHandlerAsync(
        Office.EventType.ItemChanged,
        () => {
          updateLatestMailContent()
        }
      )
    }
  });
})

function closeMenuOnOutside(e) {
  const drawer = document.querySelector('.history-drawer')
  if (drawer && !drawer.contains(e.target)) closeMenu()
}

const handleButtonClick = async () => {
  if (isLoading.value) {
    stopGenerating()
  } else {
    await sendMessage(query.value)
    query.value = ''  // Clear the input after sending
    // If we're not continuing an existing chat, save to history
    if (!chatActiveChatId.value && messages.value.length > 0) {
      saveToHistory()
    }
  }
}

</script>
