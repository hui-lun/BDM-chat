<template>
  <div class="chat-header">
    <div class="logo">
      <!-- <img src="/bdmchat-logo.png" alt="logo" /> -->
      <span>BDM.Agent</span>
    </div>
    <div class="header-icons">
      <!-- <span class="icon" @click="$emit('open-history-menu')" title="聊天歷史紀錄">🕑</span> -->
      <span class="icon" @click="$emit('clear-messages')" title="清除聊天紀錄">🗑️</span>
      <span class="icon" @click="$emit('send-email-content')" title="傳入信件內容">✉️</span>
      <a class="icon" href="https://192.168.1.193:8443/" target="_blank" title="以新分頁開啟">🌐</a> 
      <!-- <a class="icon" href="https://841f-59-124-2-11.ngrok-free.app/" target="_blank" title="以新分頁開啟">🌐</a> -->
    </div>
  </div>
</template>



