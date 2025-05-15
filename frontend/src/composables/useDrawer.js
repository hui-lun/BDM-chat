import { ref, computed, nextTick } from 'vue'

export function useDrawer() {
  const showHistoryMenu = ref(false)
  const selectedHistoryIdx = ref(null)
  const chatHistory = ref([
    { title: '2024-04-25 Morning', time: '09:21', messages: [{ sender: 'user', text: '你好' }, { sender: 'ai', text: '哈囉！有什麼可以幫您？' }] },
    { title: '2024-04-24 Afternoon', time: '15:02', messages: [{ sender: 'user', text: '今天天氣？' }, { sender: 'ai', text: '晴時多雲' }] }
  ])
  const menuIdx = ref(null)
  const editIdx = ref(null)
  const renameTitle = ref('')
  const renameInput = ref(null)
  const showDeleteModal = ref(false)
  const deletePopoverPos = ref(null)
  let pendingDeleteIdx = null

  function openHistoryMenu() { showHistoryMenu.value = true; closeMenu() }
  function closeHistoryMenu() { showHistoryMenu.value = false; closeMenu() }
  function selectHistory(idx) {
    if (editIdx.value !== null || menuIdx.value !== null) return
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
