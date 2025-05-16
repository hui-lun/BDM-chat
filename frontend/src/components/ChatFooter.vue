<template>
  <div class="chat-footer">
    <textarea
      v-model="inputValue"
      @keydown.enter.prevent="handleEnter"
      placeholder="請輸入訊息..."
      class="chat-input"
    ></textarea>
  </div>

  <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px;">
    <label style="display:flex;align-items:center;font-size:12px; margin-right: auto;">
      <input 
        type="checkbox" 
        v-model="useAgent" 
        style="width:22px;height:22px;accent-color:#1976d2;margin-right:4px"
      />
      智能助理
    </label>
    
    <button type="submit" :class="['send-button', { 'stop-button': isLoading }]" @click="$emit('send-message', inputValue)">
      {{ isLoading ? "停止" : "送出" }}
    </button>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
const props = defineProps({
  modelValue: String,
  isLoading: Boolean
})
const emit = defineEmits(['update:modelValue', 'send-message'])
const inputValue = ref(props.modelValue || '')


function emitMessage() {
  const message = inputValue.value.trim()
  if (message !== '') {
    emit('send-message', message)  // ✅ 保留這個 emit
    inputValue.value = ''          // 清空輸入框
  }
}

// 處理按鍵行為
function handleEnter(e) {
  if (e.shiftKey) {
    // Shift+Enter 換行
    const textarea = e.target
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const value = inputValue.value
    inputValue.value = value.slice(0, start) + '\n' + value.slice(end)
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 1
    })
  } else {
    // Enter 送出
    emitMessage()
  }
}


watch(() => props.modelValue, (val) => {
  inputValue.value = val || ''
})
watch(inputValue, (val) => {
  emit('update:modelValue', val)
})
</script>

