import { ref, computed, nextTick } from 'vue'

export function useDrawer(messages) {
  const showHistoryMenu = ref(false)
  const selectedHistoryIdx = ref(null)
  const chatHistory = ref([])

  const menuIdx = ref(null) // Menu index for context actions
  const editIdx = ref(null) // Edit index for renaming
  const renameTitle = ref('') // Temporary title for renaming
  const renameInput = ref(null) // Input DOM for renaming focus
  const showDeleteModal = ref(false) // Whether delete modal is shown
  const deletePopoverPos = ref(null) // Delete modal positioning
  let pendingDeleteIdx = null // Index pending delete

  function openHistoryMenu() { showHistoryMenu.value = true; closeMenu() }
  function closeHistoryMenu() { showHistoryMenu.value = false; closeMenu() }
  function selectHistory(idx) {
    if (editIdx.value !== null || menuIdx.value !== null) return
    if (messages && messages.value && chatHistory.value && chatHistory.value[idx]) {
      messages.value = [...chatHistory.value[idx].messages]
      selectedHistoryIdx.value = idx
      closeHistoryMenu()
    }
  }

  function toggleMenu(idx) { 
    console.log('Toggling menu for index:', idx); 
    menuIdx.value = menuIdx.value === idx ? null : idx; 
    editIdx.value = null 
}
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

  function closeDeleteModal() {
    showDeleteModal.value = false
    deletePopoverPos.value = null
    pendingDeleteIdx = null
  }

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

  return {
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
    selectHistory,
    toggleMenu,
    closeMenu,
    startRename,
    finishRename,
    openDeleteModal,
    closeDeleteModal,
    doDeleteHistory
  }
}
