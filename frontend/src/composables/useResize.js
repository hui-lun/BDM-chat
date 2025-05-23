import { ref, onUnmounted } from 'vue'

export function useResize(elementRef, options = {}) {
  const { minHeight = 60 } = options
  const startY = ref(0)
  const startHeight = ref(0)
  const isResizing = ref(false)
  let rafId = null
  let lastY = 0

  function updateHeight() {
    if (!isResizing.value) return
    
    const newHeight = startHeight.value - (lastY - startY.value)
    if (newHeight > minHeight) {
      elementRef.value.style.height = `${newHeight}px`
    }
    
    rafId = requestAnimationFrame(updateHeight)
  }

  function handleResize(e) {
    if (!isResizing.value) return
    lastY = e.clientY
  }

  function startResize(e) {
    e.preventDefault()
    e.stopPropagation()
    
    isResizing.value = true
    startY.value = e.clientY
    lastY = e.clientY
    startHeight.value = parseInt(document.defaultView.getComputedStyle(elementRef.value).height, 10)
    
    // 使用 passive: true 提高滾動性能
    document.addEventListener('mousemove', handleResize, { passive: true })
    document.addEventListener('mouseup', stopResize, { passive: true })
    
    // 開始動畫幀更新
    rafId = requestAnimationFrame(updateHeight)
  }

  function stopResize() {
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    
    isResizing.value = false
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
  }

  onUnmounted(() => {
    if (rafId) {
      cancelAnimationFrame(rafId)
    }
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
  })

  return {
    startResize,
    isResizing
  }
}
