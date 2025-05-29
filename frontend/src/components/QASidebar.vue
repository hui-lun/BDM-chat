<template>
  <div class="qa-sidebar" :class="{ 'is-visible': isVisible }">
    <div class="sidebar-header">
      <h3>Q&A 歷史紀錄</h3>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
    <div class="search-box">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="搜尋問題或答案..."
        class="search-input"
      />
    </div>
    <div class="qa-list" v-if="filteredQA.length > 0">
      <div v-for="(qa, index) in filteredQA" :key="index" class="qa-item">
        <div class="question" @click="toggleQA(index)">
          <span class="question-text">{{ qa.question }}</span>
          <span class="toggle-icon">{{ expandedQA === index ? '−' : '+' }}</span>
        </div>
        <div class="answer" v-show="expandedQA === index">
          {{ qa.answer }}
        </div>
      </div>
    </div>
    <div v-else class="no-results">
      {{ isLoading ? '載入中...' : '沒有找到相關的問答紀錄' }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineProps, defineEmits } from 'vue'
import axios from 'axios'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const qaList = ref([])
const searchQuery = ref('')
const expandedQA = ref(null)
const isLoading = ref(false)

const filteredQA = computed(() => {
  if (!searchQuery.value.trim()) return qaList.value
  
  const query = searchQuery.value.toLowerCase()
  return qaList.value.filter(qa => 
    qa.question.toLowerCase().includes(query) || 
    qa.answer.toLowerCase().includes(query)
  )
})

const toggleQA = (index) => {
  expandedQA.value = expandedQA.value === index ? null : index
}

const fetchQAHistory = async () => {
  if (!props.title) return
  
  isLoading.value = true
  try {
    const response = await axios.get(`/api/qa-history/${encodeURIComponent(props.title)}`)
    qaList.value = response.data.qa_list || []
  } catch (error) {
    console.error('Error fetching QA history:', error)
    qaList.value = []
  } finally {
    isLoading.value = false
  }
}

// Fetch QA history when component is mounted or title changes
onMounted(fetchQAHistory)
</script>

<style scoped>
.qa-sidebar {
  position: fixed;
  top: 0;
  right: -400px;
  width: 400px;
  height: 100vh;
  background-color: #f8f9fa;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  transition: right 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.qa-sidebar.is-visible {
  right: 0;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e9ecef;
  background-color: #fff;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0 8px;
  line-height: 1;
}

.close-btn:hover {
  color: #343a40;
}

.search-box {
  padding: 12px 16px;
  border-bottom: 1px solid #e9ecef;
  background-color: #fff;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.qa-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.qa-item {
  margin-bottom: 8px;
  border-radius: 4px;
  overflow: hidden;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.question {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  transition: background-color 0.2s;
}

.question:hover {
  background-color: #f8f9fa;
}

.toggle-icon {
  font-size: 1.2rem;
  color: #6c757d;
  font-weight: bold;
}

.answer {
  padding: 0 16px 12px;
  color: #495057;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.no-results {
  padding: 24px 16px;
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

/* Scrollbar styling */
.qa-list::-webkit-scrollbar {
  width: 6px;
}

.qa-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.qa-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.qa-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
