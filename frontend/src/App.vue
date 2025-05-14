<template>
  
  <div v-if="loading" class="loading-screen">
    <div class="spinner"></div>
  </div>

  <div class="chat-app">
    <div v-if="showError" class="error-popup">
      {{ errorMsg }}
    </div>
    
    
    <div v-if="showHistoryMenu" class="drawer-mask" @click="closeHistoryMenu"></div>

    <!-- chat history -->
    <aside class="history-drawer" :class="{ open: showHistoryMenu }">
      <div class="drawer-header">
        <span>歷史紀錄</span>
        <span class="close-btn" @click="closeHistoryMenu">×</span>
      </div>

      <ul class="drawer-list">
        <li 
          v-for="(item, idx) in chatHistory" 
          :key="idx"
          :class="['drawer-item', { selected: idx === selectedHistoryIdx }]"
          @click="selectHistory(idx)"
        >
          <template v-if="editIdx !== idx">
            <div class="drawer-item-left">
              <span class="drawer-title">{{ item.title }}</span>
            </div>
            <div class="drawer-item-right">
              <span class="drawer-time">{{ item.time }}</span>
              <span class="drawer-menu-btn" @click.stop="toggleMenu(idx)">⋯</span>

              <div v-if="menuIdx === idx" class="drawer-menu-popup" @click.stop>
                <div class="drawer-menu-item" @click.stop="startRename(idx, item.title)">重新命名</div>
                <div class="drawer-menu-item danger" @click.stop="openDeleteModal(idx)">刪除</div>
              </div>
            </div>
          </template>

          <template v-else>
            <input
              class="drawer-rename-input"
              v-model="renameTitle"
              ref="renameInput"
              @keyup.enter="finishRename(idx)"
              @blur="finishRename(idx)"
            />
          </template>
        </li>

        <li v-if="!chatHistory.length" class="drawer-empty">尚無歷史紀錄</li>
      </ul>
    </aside>

    <!-- delete double check Popover -->
    <teleport to="body">
      <div v-if="showDeleteModal && deletePopoverPos" class="delete-popover-mask" @click="closeDeleteModal">
        <div class="delete-popover" :style="deletePopoverStyle" @click.stop>
          <div class="delete-popover-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="12" fill="#ffeaea" />
              <path 
                d="M9.5 11v4m5-4v4M5 7h14m-2 0-.545 9.26A2 2 0 0 1 14.46 18h-4.92a2 2 0 0 1-1.995-1.74L5 7Zm3-2h4a1 1 0 0 1 1 1v1H7V6a1 1 0 0 1 1-1Z" 
                stroke="#e74c3c" 
                stroke-width="1.4" 
                stroke-linecap="round" 
                stroke-linejoin="round"
              />
            </svg>
          </div>

          <div class="delete-popover-title">確定要刪除此聊天紀錄嗎？</div>

          <div class="delete-popover-actions">
            <button class="delete-popover-btn danger" @click="doDeleteHistory">確定</button>
            <button class="delete-popover-btn" @click="closeDeleteModal">取消</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- chatbot Header -->
    <div class="chat-header">
      <div class="logo">
        <!-- <img src="/bdmchat-logo.png" alt="logo" /> -->
        <span>BDM.Agent</span>
      </div>

      <div class="header-icons">
        <span class="icon" @click="openHistoryMenu" title="聊天歷史紀錄">🕑</span>
        <!-- <span class="icon" @click="clearMessages" title="清除聊天紀錄">🗑️</span> -->
        <span class="icon" @click="sendEmailContent" title="傳入信件內容">✉️</span>
        <span class="icon" @click="openDraftFormtt" title="生草稿">草稿</span>
        <!-- <span class="icon" @click="createDraftExample" title="產生草稿">📝</span> -->
      </div>
    </div>

    <!-- Chatbot content-->
    <div class="chat-body" ref="chatBody">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['msg-row', msg.sender]">
        <div :class="['msg-bubble', msg.sender]">
          <div v-if="msg.loading" class="loading-dots">
            <span></span><span></span><span></span>
          </div>
          <div v-else>
            <div v-html="msg.text"></div>
            <button v-if="msg.isEmailSummary" class="draft-btn" @click="openDraftForm('AI回覆草稿', msg.text)">產生草稿</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat input area -->
    <form class="chat-footer" @submit.prevent="handleButtonClick">
      <input 
        v-model="query" 
        placeholder="請輸入訊息...." 
        autocomplete="off" 
      />

      <button type="submit" :class="['send-button', { 'stop-button': isLoading }]" >
        {{ isLoading ? "停止" : "送出" }}
      </button>

      <label style="display:flex;align-items:center;margin-left:12px;font-size:12px;gap:4px">
        <input 
          type="checkbox" 
          v-model="useAgent" 
          style="width:22px;height:22px;accent-color:#1976d2;margin-right:4px"
        />
        智能助理
      </label>
    </form>

  </div>
</template>


<script setup>
import { ref, nextTick, watch, onMounted, computed } from 'vue'
import axios from 'axios'

// ====== Basic state ======
const query = ref('') // User input query
const messages = ref([]) // All chat messages
const loading = ref(true) // Loading state for plugin readiness
const isLoading = ref(false) // Loading state for message generation
const useAgent = ref(false) // Switch between agent mode and normal chat
let controller = null // Abort controller for request cancellation
const chatBody = ref(null) // Chat body DOM element for scrolling

// ====== Chat history drawer management ======
const showHistoryMenu = ref(false) // Whether history drawer is shown
const selectedHistoryIdx = ref(null) // Currently selected history index
const chatHistory = ref([ // Hardcoded initial chat history examples
  { title: '2024-04-25 Morning', time: '09:21', messages: [{ sender: 'user', text: '你好' }, { sender: 'ai', text: '哈囉！有什麼可以幫您？' }] },
  { title: '2024-04-24 Afternoon', time: '15:02', messages: [{ sender: 'user', text: '今天天氣？' }, { sender: 'ai', text: '晴時多雲' }] }
])

const menuIdx = ref(null) // Menu index for context actions
const editIdx = ref(null) // Edit index for renaming
const renameTitle = ref('') // Temporary title for renaming
const renameInput = ref(null) // Input DOM for renaming focus
const showDeleteModal = ref(false) // Whether delete modal is shown
const deletePopoverPos = ref(null) // Delete modal positioning
let pendingDeleteIdx = null // Index pending delete

// ====== Chat history drawer actions ======
function openHistoryMenu() { showHistoryMenu.value = true; closeMenu() }
function closeHistoryMenu() { showHistoryMenu.value = false; closeMenu() }
function selectHistory(idx) {
  if (editIdx.value !== null || menuIdx.value !== null) return
  messages.value = [...chatHistory.value[idx].messages]
  selectedHistoryIdx.value = idx
  closeHistoryMenu()
}

function toggleMenu(idx) { menuIdx.value = menuIdx.value === idx ? null : idx; editIdx.value = null }
function closeMenu() { menuIdx.value = null; editIdx.value = null }
function startRename(idx, title) { editIdx.value = idx; menuIdx.value = null; renameTitle.value = title; nextTick(() => renameInput.value?.focus()) }
function finishRename(idx) {
  const val = renameTitle.value.trim()
  if (val) chatHistory.value[idx].title = val
  editIdx.value = null
}

function openDeleteModal(idx) {
  menuIdx.value = null
  nextTick(() => {
    const items = document.querySelectorAll('.drawer-item')
    const el = items[idx]
    if (el) {
      const rect = el.getBoundingClientRect()
      deletePopoverPos.value = { top: rect.top + rect.height/2 + window.scrollY, left: rect.right + 8 + window.scrollX }
    } else {
      deletePopoverPos.value = null
    }
    showDeleteModal.value = true
    pendingDeleteIdx = idx
  })
}

function closeDeleteModal() { showDeleteModal.value = false; deletePopoverPos.value = null; pendingDeleteIdx = null }
function doDeleteHistory() {
  if (pendingDeleteIdx !== null) {
    chatHistory.value.splice(pendingDeleteIdx, 1)
    if (selectedHistoryIdx.value === pendingDeleteIdx) selectedHistoryIdx.value = null
    closeDeleteModal()
  }
}
const deletePopoverStyle = computed(() => {
  if (!deletePopoverPos.value) return {}
  return { position: 'absolute', top: deletePopoverPos.value.top + 'px', left: deletePopoverPos.value.left + 'px', zIndex: 3000 }
})


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


function handleEmailChange(autoSend = false) {
  const item = Office.context.mailbox?.item;
  if (!item) {
    showErrorMessage("Cannot access email item.");
    return;
  }

  const Title = item.subject || '(無主旨)';
  const Custom = item.from?.displayName || '(無寄件者)';
  const BDM = item.to?.map(r => r.displayName).join(', ') || '(無收件者)';
  const dateTime = item.dateTimeCreated || '(無寄送時間)';

  // 取得信件內容
  item.body.getAsync("text", (result) => {
    if (result.status === Office.AsyncResultStatus.Succeeded) {
      const content = result.value.trim();
      if (content) {
        // optional: print info
        const fullContent = `
          寄件者: ${Custom}
          收件者: ${BDM}
          主旨: ${Title}
          寄送時間: ${dateTime}

          ${content}
        `.trim();

        query.value = fullContent;
        if (autoSend) sendQuery();

        console.log("Email Info:");
        console.log("From:", from);
        console.log("To:", to);
        console.log("Subject:", subject);
        console.log("Time:", dateTime);
        console.log("Body:", content);
      } else {
        showErrorMessage("This email body is empty.");
      }
    } else {
      showErrorMessage("Failed to retrieve email body.");
      console.error("getAsync error:", result.error);
    }
  });
}



function sendEmailContent() {
  if (typeof Office === 'undefined' || !Office.context.mailbox?.item) {
    showErrorMessage("Not inside Outlook add-in environment.")
    return
  }
  handleEmailChange(true)
}


// ====== Initial setup when mounted ======
onMounted(() => {
  document.addEventListener('click', closeMenuOnOutside);

  console.log("Checking Office context:", typeof Office !== 'undefined' ? Office.context : 'Office not available');

  if (typeof Office === 'undefined') return;

  Office.onReady(() => {
    console.log("Office.js is ready", Office.context);
    loading.value = false;
  });
});

// onMounted(() => {
//   document.addEventListener('click', closeMenuOnOutside)
//   loading.value = false // 立即關閉 loading，確保畫面可用
// })


function closeMenuOnOutside(e) {
  const drawer = document.querySelector('.history-drawer')
  if (drawer && !drawer.contains(e.target)) closeMenu()
}

// ======================================================================================
function openDraftForm(subject = '', htmlBody = '') {
  if (Office.context.mailbox.displayNewMessageForm) {
    Office.context.mailbox.displayNewMessageForm({
      toRecipients: ["someone@example.com"],
      subject: subject || "Draft via displayNewMessageForm",
      htmlBody: htmlBody || "<p>Hello from Add-in!</p>"
    });
  } else {
    console.error("This Outlook version does not support displayNewMessageForm.");
  }
}

function openDraftFormtt() {
  if (Office.context.mailbox.displayNewMessageForm) {
    Office.context.mailbox.displayNewMessageForm({
      toRecipients: ["someone@example.com"],
      subject: "Draft via displayNewMessageForm",
      htmlBody: "<p>Hello from Add-in!</p>"
    });
  } else {
    console.error("This Outlook version does not support displayNewMessageForm.");
  }
}


// ====== Chat handling ======
const scrollToBottom = () => {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}
watch(messages, scrollToBottom, { deep: true })

const handleButtonClick = async () => {
  if (isLoading.value) stopGenerating()
  else await sendQuery()
}

const sendQuery = async () => {
  if (!query.value.trim()) return

  messages.value.push({ sender: 'user', text: query.value })
  const userMsg = query.value
  query.value = ''
  messages.value.push({ sender: 'ai', loading: true })

  isLoading.value = true

  try {
    controller = new AbortController()
    let res
    if (useAgent.value) {
      res = await axios.post('/agent-chat', { agent_query: userMsg }, { signal: controller.signal })
      const isEmailSummary = res.data.from_email === true
      messages.value[messages.value.length - 1] = { sender: 'ai', text: res.data.summary || JSON.stringify(res.data), isEmailSummary }
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

const stopGenerating = () => {
  if (controller) controller.abort()
  isLoading.value = false
  controller = null
}
</script>

