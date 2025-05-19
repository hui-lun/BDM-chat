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
        v-model="useAgentLocal" 
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
  isLoading: Boolean,
  useAgent: Boolean
})
const emit = defineEmits(['update:modelValue', 'send-message', 'update:useAgent'])

const inputValue = ref(props.modelValue || '')
const useAgentLocal = ref(props.useAgent ?? false)  // 預設 false，避免 null

// 同步 useAgent 到父層
watch(useAgentLocal, (val) => {
  console.log('[DEBUG] emit update:useAgent', val)
  emit('update:useAgent', val)
})
watch(() => props.modelValue, (val) => {
  inputValue.value = val || ''
})
watch(inputValue, (val) => {
  emit('update:modelValue', val)
})

function emitMessage() {
  const message = inputValue.value.trim()
  if (message !== '') {
    emit('send-message', message)
    inputValue.value = ''
  }
}

function handleEnter(e) {
  if (e.shiftKey) {
    const textarea = e.target
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const value = inputValue.value
    inputValue.value = value.slice(0, start) + '\n' + value.slice(end)
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 1
    })
  } else {
    emitMessage()
  }
}
</script>