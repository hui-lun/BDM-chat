<template>
  <teleport to="body">
    <div v-if="show" class="drawer-mask" @click.self="$emit('close')">
      <div class="history-drawer open">
        <div class="drawer-header">
          聊天歷史紀錄
          <span class="close-btn" @click="$emit('close')">×</span>
        </div>
        <ul class="drawer-list">
          <li 
            v-for="(item, idx) in history" 
            :key="idx"
            :class="['drawer-item', { selected: idx === selectedHistoryIdx }]"
            @click="$emit('select', idx)"
          >
            <template v-if="editIdx !== idx">
              <div class="drawer-item-left">
                <span class="drawer-title">{{ item.title }}</span>
              </div>
              <div class="drawer-item-right">
                <span class="drawer-time">{{ item.time }}</span>
                <span class="drawer-menu-btn" @click.stop="$emit('toggle-menu', idx)">⋯</span>

                <div v-if="menuIdx === idx" class="drawer-menu-popup" :style="{top: 'auto'}" @click.stop>
                  <div class="drawer-menu-item" @click.stop="$emit('start-rename', idx, item.title)">重新命名</div>
                  <div class="drawer-menu-item danger" @click.stop="$emit('open-delete-modal', idx)">刪除</div>
                </div>
              </div>
            </template>
            <template v-else>
              <input
                class="drawer-rename-input"
                :value="renameInput"
                @input="$emit('update-rename-input', $event.target.value)"
                ref="renameInputRef"
                @keyup.enter="$emit('finish-rename', idx)"
                @blur="$emit('finish-rename', idx)"
              />
            </template>
          </li>
          <li v-if="!history.length" class="drawer-empty">尚無歷史紀錄</li>
        </ul>
      </div>
    </div>
  </teleport>
  <teleport to="body">
    <div v-if="showDeleteModal && deletePopoverPos" class="delete-popover-mask" @click="$emit('close-delete')">
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
        <div class="delete-popover-subtitle">此操作無法復原，紀錄將永久刪除</div>
        <div class="delete-popover-actions">
          <button class="delete-popover-btn danger" @click="$emit('confirm-delete')">
            <span class="delete-icon">🗑️</span> 確定刪除
          </button>
          <button class="delete-popover-btn" @click="$emit('close-delete')">取消</button>
        </div>
      </div>
    </div>
  </teleport>
  
  <!-- Delete Success Toast -->
  <teleport to="body">
    <div v-if="showDeleteSuccess" class="delete-success-toast">
      <span class="success-icon">✓</span> 聊天紀錄已成功刪除
    </div>
  </teleport>
</template>

<script setup>

const props = defineProps({
  show: Boolean,
  history: Array,
  showDeleteModal: Boolean,
  showDeleteSuccess: Boolean,
  deletePopoverPos: Object,
  deletePopoverStyle: Object,
  menuIdx: Number,              
  editIdx: Number,
  selectedHistoryIdx: Number,
  renameInput: {
    type: String,
    default: ''
  } 
})

defineEmits(['close', 'select', 'toggle-menu', 'start-rename', 'finish-rename', 'update-rename-input', 'open-delete-modal', 'close-delete', 'confirm-delete'])
</script>

<style scoped>
.delete-popover-subtitle {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 12px;
  text-align: center;
}

.delete-icon {
  display: inline-block;
  margin-right: 4px;
}

.delete-success-toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #4caf50;
  color: white;
  padding: 10px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 9999;
  display: flex;
  align-items: center;
  animation: fadeInOut 3s ease-in-out forwards;
}

.success-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background-color: white;
  color: #4caf50;
  border-radius: 50%;
  margin-right: 8px;
  font-weight: bold;
}

@keyframes fadeInOut {
  0% { opacity: 0; transform: translate(-50%, 20px); }
  15% { opacity: 1; transform: translate(-50%, 0); }
  85% { opacity: 1; transform: translate(-50%, 0); }
  100% { opacity: 0; transform: translate(-50%, -20px); }
}

.delete-popover-btn.danger {
  background-color: #e74c3c;
  color: white;
  font-weight: 500;
}

.delete-popover-btn.danger:hover {
  background-color: #c0392b;
}
</style>
