<template>
  <div class="chat-footer">
    <input
      v-model="inputValue"
      @keyup.enter="$emit('send-message', inputValue)"
      placeholder="請輸入訊息..."
      class="chat-input"
    />
    <button type="submit" :class="['send-button', { 'stop-button': isLoading }]" @click="$emit('send-message', inputValue)">
      {{ isLoading ? "停止" : "送出" }}
    </button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({
  modelValue: String,
  isLoading: Boolean
})
const emit = defineEmits(['update:modelValue', 'send-message'])
const inputValue = ref(props.modelValue || '')

watch(() => props.modelValue, (val) => {
  inputValue.value = val || ''
})
watch(inputValue, (val) => {
  emit('update:modelValue', val)
})
</script>

