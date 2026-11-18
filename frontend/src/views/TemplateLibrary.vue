<script setup>
import { computed, onMounted, ref } from 'vue'
import { useChatStore } from '../stores/chat'
import AppHeader from '../components/AppHeader.vue'
import BottomNav from '../components/BottomNav.vue'
import MarkdownDoc from '../components/MarkdownDoc.vue'
import AssessmentCard from '../components/AssessmentCard.vue'
import { templates } from '../data/templates'
import { cases } from '../data/cases'
import { saveTextFile } from '../utils/export'
import { showToast } from '../utils/toast'

const chat = useChatStore()

const tab = ref('templates') 
const keyword = ref('')
const active = ref(null) 

onMounted(() => {
  chat.init()
})

const source = computed(() => (tab.value === 'cases' ? cases : templates))

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  const list = source.value
  if (!kw) return list
  return list.filter(
    (t) =>
      t.name.toLowerCase().includes(kw) ||
      t.category.toLowerCase().includes(kw) ||
      (t.tags || []).some((tag) => tag.toLowerCase().includes(kw))
  )
})

function open(t) {
  active.value = t
}

function close() {
  active.value = null
}

function exportMd(t) {
  const suffix = tab.value === 'cases' ? '案例成品' : '需求文档模板'
  const mode = saveTextFile(`${t.name}·${suffix}.md`, t.content)
  showToast(mode === 'native' ? '已保存到「下载」目录' : 'MD 文件已导出')
}
</script>

<template>
  <div class="tpl-page">
    <AppHeader />

    <main class="tpl-body">
      <div class="tpl-head">
        <h2>{{ tab === 'cases' ? '案例成品库' : '标准模板库' }}</h2>
        <p>
          {{
            tab === 'cases'
              ? '看看别人填完之后长什么样的成品报告，建立预期'
              : '不同业务场景的需求文档模板，可预览并导出 MD 文档'
          }}
        </p>
      </div>

      <div class="tab-switch">
        <button type="button" class="sw" :class="{ on: tab === 'templates' }" @click="tab = 'templates'">标准模板</button>
        <button type="button" class="sw" :class="{ on: tab === 'cases' }" @click="tab = 'cases'">案例成品</button>
      </div>

      <div class="search-box">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.3-4.3" />
        </svg>
        <input
          v-model="keyword"
          type="text"
          :placeholder="tab === 'cases' ? '搜索案例，例如：奶茶、会员…' : '搜索模板名称，例如：电商、物联网…'"
        />
        <button v-if="keyword" type="button" class="clear" @click="keyword = ''">×</button>
      </div>

      <div v-if="filtered.length" class="tpl-list">
        <div v-for="t in filtered" :key="t.id" class="tpl-card card" @click="open(t)">
          <div class="tpl-top">
            <span class="tpl-name">{{ t.name }}</span>
            <span class="tpl-cat">{{ t.category }}</span>
            <span v-if="t.assessment" class="score-chip">成熟度 {{ t.assessment.score }}</span>
          </div>
          <p class="tpl-summary">{{ t.summary }}</p>
          <div class="tpl-bottom">
            <div class="tpl-tags">
              <span v-for="tag in t.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
            <button type="button" class="export-btn" @click.stop="exportMd(t)">导出 MD</button>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <p>没有找到「{{ keyword }}」相关的{{ tab === 'cases' ? '案例' : '模板' }}</p>
      </div>
    </main>

    <BottomNav />

    
    <transition name="fade">
      <div v-if="active" class="detail-mask">
        <div class="detail">
          <header class="detail-bar">
            <button type="button" class="icon-btn" @click="close">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 5l-7 7 7 7" />
              </svg>
            </button>
            <div class="detail-title">{{ active.name }}</div>
            <button type="button" class="detail-export" @click="exportMd(active)">导出 MD</button>
          </header>
          <div class="detail-body">
            <div v-if="active.assessment" class="case-assessment card">
              <AssessmentCard :assessment="active.assessment" />
            </div>
            <MarkdownDoc :source="active.content" />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.tpl-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.tpl-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px 16px 24px;
}

.tpl-head h2 {
  margin: 0 0 4px;
  font-size: 19px;
  font-weight: 700;
}

.tpl-head p {
  margin: 0 0 14px;
  font-size: 13px;
  color: var(--ink-2);
}


.tab-switch {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  padding: 4px;
  border-radius: 12px;
  background: var(--card);
  border: 1px solid var(--line);
}

.sw {
  flex: 1;
  height: 38px;
  border-radius: 9px;
  color: var(--ink-2);
  font-size: 14px;
  font-weight: 600;
  transition: all 0.16s;
}

.sw.on {
  background: var(--accent);
  color: #fff;
}

.score-chip {
  flex: none;
  font-size: 11px;
  padding: 2px 9px;
  border-radius: 999px;
  background: #d1fae5;
  color: #059669;
  font-weight: 650;
}


.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  height: 46px;
  border-radius: 13px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink-3);
  transition: border-color 0.15s;
  margin-bottom: 14px;
}

.search-box:focus-within {
  border-color: var(--accent);
  color: var(--accent);
}

.search-box input {
  flex: 1;
  height: 100%;
  font-size: 14px;
  color: var(--ink);
}

.search-box input::placeholder {
  color: var(--ink-3);
}

.search-box .clear {
  font-size: 20px;
  line-height: 1;
  color: var(--ink-3);
  padding: 4px;
}


.tpl-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tpl-card {
  padding: 14px 16px;
  cursor: pointer;
  transition: transform 0.15s;
}

.tpl-card:active {
  transform: scale(0.99);
}

.tpl-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tpl-name {
  font-size: 16px;
  font-weight: 700;
}

.tpl-cat {
  font-size: 11px;
  padding: 2px 9px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  flex: none;
}

.tpl-summary {
  margin: 8px 0 10px;
  font-size: 13px;
  color: var(--ink-2);
  line-height: 1.6;
}

.tpl-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.tpl-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--bg);
  color: var(--ink-3);
  border: 1px solid var(--line);
}

.export-btn {
  flex: none;
  font-size: 12.5px;
  padding: 6px 13px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--ink-3);
  font-size: 14px;
}


.detail-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: var(--bg);
  display: flex;
  flex-direction: column;
}

.detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 1080px;
  width: 100%;
  margin: 0 auto;
}

.detail-bar {
  flex: none;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  padding-top: max(14px, env(safe-area-inset-top));
  background: #fff;
  border-bottom: 1px solid var(--line);
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--ink);
  flex: none;
}

.icon-btn:active {
  background: var(--bg);
}

.detail-title {
  flex: 1;
  font-size: 16px;
  font-weight: 700;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-export {
  flex: none;
  font-size: 13px;
  padding: 7px 14px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px 16px 28px;
}

.case-assessment {
  padding: 16px;
  margin-bottom: 16px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .tpl-body {
    padding: 14px 12px 20px;
  }

  .detail-body {
    padding: 12px 12px 24px;
  }
}
</style>
