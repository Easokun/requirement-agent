<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import logo from '../assets/logo.png'

const router = useRouter()
const chat = useChatStore()

const quotaText = computed(
  () => `需求分析 ${chat.usage.remaining}/${chat.usage.max} 次`
)
const isLow = computed(() => chat.usage.remaining <= 1)
</script>

<template>
  <header class="app-header">
    <div class="logo"><img :src="logo" alt="极构" /></div>
    <div class="titles">
      <h1>极构</h1>
    </div>
    <span class="quota-badge" :class="{ low: isLow }">{{ quotaText }}</span>
    <button class="icon-btn" aria-label="我的图纸" @click="router.push('/history')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M7 3h7l4 4v14H7z" stroke-linejoin="round" />
        <path d="M14 3v4h4" stroke-linejoin="round" />
      </svg>
    </button>
    <button class="icon-btn" aria-label="我的" @click="router.push('/profile')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4 3.6-6 8-6s8 2 8 6" stroke-linecap="round" />
      </svg>
    </button>
  </header>
</template>

<style scoped>
.icon-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  flex: none;
}

.icon-btn:active {
  background: rgba(255, 255, 255, 0.2);
}
</style>
