import { ref, computed, nextTick } from 'vue'

export function useDrawer(messages) {
  const showHistoryMenu = ref(false)
  const selectedHistoryIdx = ref(null)
  const chatHistory = ref([])
  const activeChatId = ref(null) // Store the active chat ID to prevent creating new records

  const menuIdx = ref(null) // Menu index for context actions
  const editIdx = ref(null) // Edit index for renaming
  const renameTitle = ref('') // Temporary title for renaming
  const renameInput = ref(null) // Input DOM for renaming focus
  const showDeleteModal = ref(false) // Whether delete modal is shown
  const showDeleteSuccess = ref(false) // Show success toast after deletion
  const deletePopoverPos = ref(null) // Delete modal positioning
  let pendingDeleteIdx = null // Index pending delete
  let deleteSuccessTimer = null // Timer for hiding success toast

  function openHistoryMenu() { showHistoryMenu.value = true; closeMenu() }
  function closeHistoryMenu() { showHistoryMenu.value = false; closeMenu() }
  function selectHistory(idx) {
    if (editIdx.value !== null || menuIdx.value !== null) return
    if (messages && messages.value && chatHistory.value && chatHistory.value[idx]) {
      // Set the messages from the selected history
      messages.value = [...chatHistory.value[idx].messages]
      // Set the active chat ID to the selected history's ID
      activeChatId.value = chatHistory.value[idx].id
      // Update the selected history index
      selectedHistoryIdx.value = idx
      closeHistoryMenu()
    }
  }

  function toggleMenu(idx) { 
    menuIdx.value = menuIdx.value === idx ? null : idx; 
    editIdx.value = null 
}
  function closeMenu() { menuIdx.value = null; editIdx.value = null }
  function startRename(idx, title) { 
    editIdx.value = idx; 
    menuIdx.value = null; 
    renameTitle.value = title; 
    renameInput.value = title; // Set the input value for the component
  }
  
  function updateRenameInput(value) {
    renameTitle.value = value;
    renameInput.value = value;
  }
  
  function finishRename(idx) {
    const val = renameTitle.value.trim()
    if (val && chatHistory.value[idx]) {
      chatHistory.value[idx].title = val
      // Save the updated chat history to localStorage
      saveHistoryToLocalStorage()
    }
    editIdx.value = null
  }

  function openDeleteModal(idx) {
    // Close any open menu
    menuIdx.value = null
    
    // Store the index of the chat to be deleted
    pendingDeleteIdx = idx
    
    nextTick(() => {
      try {
        // Find the element to position the delete confirmation modal
        const items = document.querySelectorAll('.drawer-item')
        const el = items[idx]
        
        if (el) {
          // Position the delete confirmation modal next to the chat item
          const rect = el.getBoundingClientRect()
          deletePopoverPos.value = { 
            top: rect.top + rect.height/2 + window.scrollY, 
            left: rect.right + 8 + window.scrollX 
          }
          // Show the delete confirmation modal
          showDeleteModal.value = true
        } else {
          console.error('Could not find chat item element for deletion')
          deletePopoverPos.value = null
          pendingDeleteIdx = null
        }
      } catch (error) {
        console.error('Error opening delete modal:', error)
        closeDeleteModal()
      }
    })
  }

  function closeDeleteModal() {
    // Hide the delete confirmation modal
    showDeleteModal.value = false
    // Reset the position of the modal
    deletePopoverPos.value = null
    // Clear the pending delete index
    pendingDeleteIdx = null
  }

  function doDeleteHistory() {
    try {
      if (pendingDeleteIdx === null || pendingDeleteIdx < 0 || pendingDeleteIdx >= chatHistory.value.length) {
        console.error('Invalid pending delete index:', pendingDeleteIdx)
        closeDeleteModal()
        return
      }
      
      // Store the ID and title of the chat being deleted for reference
      const deletedChatId = chatHistory.value[pendingDeleteIdx].id
      const deletedChatTitle = chatHistory.value[pendingDeleteIdx].title
      
      // If we're deleting the active chat, clear the activeChatId and messages
      if (activeChatId.value === deletedChatId) {
        activeChatId.value = null
        if (messages && messages.value) {
          messages.value = []
        }
      }
      
      // Update selectedHistoryIdx
      if (selectedHistoryIdx.value === pendingDeleteIdx) {
        selectedHistoryIdx.value = null
      } else if (selectedHistoryIdx.value !== null && selectedHistoryIdx.value > pendingDeleteIdx) {
        // Adjust the selected index if we're deleting an item before it
        selectedHistoryIdx.value--
      }
      
      // Remove the chat from history
      chatHistory.value.splice(pendingDeleteIdx, 1)
      
      // Save the updated chat history to localStorage
      saveHistoryToLocalStorage()
      
      // Close the delete confirmation modal
      closeDeleteModal()
      
      // If we deleted all chats, make sure the UI reflects that
      if (chatHistory.value.length === 0) {
        activeChatId.value = null
        selectedHistoryIdx.value = null
        if (messages && messages.value) {
          messages.value = []
        }
      }
      
      // Show success toast
      showDeleteSuccess.value = true
      
      // Clear any existing timer
      if (deleteSuccessTimer) {
        clearTimeout(deleteSuccessTimer)
      }
      
      // Hide success toast after 3 seconds
      deleteSuccessTimer = setTimeout(() => {
        showDeleteSuccess.value = false
      }, 3000)
      
      console.log(`Chat "${deletedChatTitle}" successfully deleted`)
    } catch (error) {
      console.error('Error deleting chat history:', error)
      closeDeleteModal()
    }
  }
  
  // Helper function to save chat history to localStorage
  function saveHistoryToLocalStorage() {
    try {
      localStorage.setItem('chat-history', JSON.stringify(chatHistory.value))
    } catch (e) {
      console.error('Error saving chat history to localStorage:', e)
    }
  }
  
  // Load chat history from localStorage on initialization
  function loadHistoryFromLocalStorage() {
    try {
      const savedHistory = localStorage.getItem('chat-history')
      if (savedHistory) {
        chatHistory.value = JSON.parse(savedHistory)
      }
    } catch (e) {
      console.error('Error loading chat history from localStorage:', e)
    }
  }
  
  // Initialize by loading history from localStorage
  loadHistoryFromLocalStorage()
  
  const deletePopoverStyle = computed(() => {
    if (!deletePopoverPos.value) return {}
    return { position: 'absolute', top: deletePopoverPos.value.top + 'px', left: deletePopoverPos.value.left + 'px', zIndex: 3000 }
  })

  return {
    showHistoryMenu,
    selectedHistoryIdx,
    chatHistory,
    menuIdx,
    editIdx,
    renameTitle,
    renameInput,
    showDeleteModal,
    showDeleteSuccess,
    deletePopoverPos,
    deletePopoverStyle,
    activeChatId,
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
  }
}
