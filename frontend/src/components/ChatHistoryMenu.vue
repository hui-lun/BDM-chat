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

                <div v-if="menuIdx === idx" class="drawer-menu-popup" @click.stop>
                  <div class="drawer-menu-item" @click.stop="$emit('start-rename', idx, item.title)">重新命名</div>
                  <div class="drawer-menu-item danger" @click.stop="$emit('open-delete-modal', idx)">刪除</div>
                </div>
              </div>
            </template>
            <template v-else>
              <input
                class="drawer-rename-input"
                v-model="renameTitle"
                ref="renameInput"
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
        <div class="delete-popover-actions">
          <button class="delete-popover-btn danger" @click="$emit('confirm-delete')">確定</button>
          <button class="delete-popover-btn" @click="$emit('close-delete')">取消</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>

const props = defineProps({
  show: Boolean,
  history: Array,
  showDeleteModal: Boolean,
  deletePopoverPos: Object,
  deletePopoverStyle: Object,
  menuIdx: Number,              
  editIdx: Number,     
  renameInput: {
    type: Object,
    default: null
  } 
})
</script>
