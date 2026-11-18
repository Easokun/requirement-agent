<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const props = defineProps({
  source: {
    type: String,
    default: ''
  }
})

const sections = computed(() => {
  const src = (props.source || '').trim()
  if (!src) return []

  const chunks = src.split(/^##\s+/m)
  const result = []

  const preamble = chunks[0].replace(/^#\s+/m, '').trim()
  if (preamble) {
    result.push({ title: '', html: renderMarkdown(preamble), intro: true })
  }

  for (let i = 1; i < chunks.length; i += 1) {
    const lines = chunks[i].split('\n')
    const title = lines.shift().trim()
    const body = lines.join('\n').trim()
    result.push({ title, html: renderMarkdown(body), intro: false })
  }

  return result
})
</script>

<template>
  <div class="markdown-doc">
    <section
      v-for="(section, index) in sections"
      :key="index"
      class="doc-section card"
      :class="{ intro: section.intro }"
    >
      <h2 v-if="section.title" class="section-title">
        <span class="section-bar"></span>
        {{ section.title }}
      </h2>
      <div class="section-body" v-html="section.html"></div>
    </section>
  </div>
</template>

<style scoped>
.markdown-doc {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.doc-section {
  padding: 16px;
}

.doc-section.intro {
  border-left: 4px solid var(--accent);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 650;
  margin: 0 0 10px;
}

.section-bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--accent), var(--accent-2));
}

.section-body :deep(h1) {
  font-size: 20px;
  margin: 0 0 8px;
}

.section-body :deep(h2) {
  font-size: 17px;
  margin: 12px 0 6px;
}

.section-body :deep(h3) {
  font-size: 15px;
  margin: 10px 0 4px;
}

.section-body :deep(p) {
  margin: 6px 0;
  font-size: 14px;
}

.section-body :deep(ul),
.section-body :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}

.section-body :deep(li) {
  font-size: 14px;
  margin: 4px 0;
}

.section-body :deep(strong) {
  color: var(--accent);
}

.section-body :deep(blockquote) {
  border-left: 3px solid var(--accent-soft);
  padding-left: 10px;
  color: var(--ink-2);
  font-size: 13px;
  margin: 6px 0;
}

.section-body :deep(code) {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 13px;
}
</style>
