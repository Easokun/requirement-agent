<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownDoc from '../components/MarkdownDoc.vue'
import { legalDocs } from '../data/legal'

const route = useRoute()
const router = useRouter()

const doc = computed(() => legalDocs[route.params.id] || { title: '未找到', content: '' })
</script>

<template>
  <div class="legal-page">
    <header class="app-header">
      <button type="button" class="icon-btn" @click="router.back()">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 5l-7 7 7 7" />
        </svg>
      </button>
      <div class="titles">
        <h1>{{ doc.title }}</h1>
        <p>极构 · 需求诊断顾问</p>
      </div>
    </header>

    <main class="legal-body">
      <MarkdownDoc :source="doc.content" />
    </main>
  </div>
</template>

<style scoped>
.legal-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

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

.legal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

@media (max-width: 640px) {
  .legal-body {
    padding: 12px;
  }
}
</style>
