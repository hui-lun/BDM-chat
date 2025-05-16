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
      :delete-popover-pos="deletePopoverPos"
      :delete-popover-style="deletePopoverStyle"
      :menu-idx="menuIdx"               
      :edit-idx="editIdx"               
      @select="selectHistory"
      @close="closeHistoryMenu"
      @close-delete="closeDeleteModal"
      @confirm-delete="doDeleteHistory"
      @toggle-menu="toggleMenu"
      @start-rename="startRename"
      @finish-rename="finishRename"
    />



    <!-- chatbot Header -->
    <ChatHeader
      @open-history-menu="openHistoryMenu"
      @close-history-menu="closeHistoryMenu"
      @send-email-content="sendEmailContent"
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
      @send-message="handleButtonClick"
    />
  </div>
</template>


<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import ChatHeader from './components/ChatHeader.vue'
import ChatBody from './components/ChatBody.vue'
import ChatFooter from './components/ChatFooter.vue'
import ChatHistoryMenu from './components/ChatHistoryMenu.vue'
import { useChat } from './composables/useChat'
import { useOutlook } from './composables/useOutlook'
import { useDrawer } from './composables/useDrawer'

// ====== Chat State and API Handling ======
const {
  query,
  messages,
  isLoading,
  useAgent,
  chatBody,
  sendQuery,
  stopGenerating,
  scrollToBottom
} = useChat()

const loading = ref(true) // Plugin readiness loading

// ====== Drawer Management (composable) ======
const {
  showHistoryMenu,
  selectedHistoryIdx,
  chatHistory,
  menuIdx,
  editIdx,
  renameTitle,
  renameInput,
  showDeleteModal,
  deletePopoverPos,
  deletePopoverStyle,
  openHistoryMenu,
  closeHistoryMenu,
  toggleMenu,
  closeMenu,
  startRename,
  finishRename,
  openDeleteModal,
  closeDeleteModal,
  doDeleteHistory
} = useDrawer()


// Corrected selectHistory: Switch chat content when clicking on history
function selectHistory(idx) {
  messages.value = [...chatHistory.value[idx].messages]
  selectedHistoryIdx.value = idx
  closeHistoryMenu()
}

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
} = useOutlook(showErrorMessage, query, sendQuery)

console.log("initial loading:", loading.value)
// ====== Initial setup when mounted ======
onMounted(() => {
  document.addEventListener('click', closeMenuOnOutside)

  const preload = document.getElementById('preload-loading')
  if (preload) preload.remove()

  
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
  if (isLoading.value) stopGenerating()
  else await sendQuery()
}

</script>
