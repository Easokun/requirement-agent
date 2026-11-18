<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { api } from '../api'
import { useChatStore } from '../stores/chat'
import { useQuestionnaireStore, multiToText } from '../stores/questionnaire'
import { useArchiveStore } from '../stores/archive'
import { useAnalysisStore } from '../stores/analysis'
import AppHeader from '../components/AppHeader.vue'
import BottomNav from '../components/BottomNav.vue'
import ChatBubble from '../components/ChatBubble.vue'
import DocCard from '../components/DocCard.vue'
import InspirationChips from '../components/InspirationChips.vue'
import LockCard from '../components/LockCard.vue'
import QuestionCard from '../components/QuestionCard.vue'
import { showToast } from '../utils/toast'
import { speechSupported, createSpeech } from '../utils/speech'
import logo from '../assets/logo.png'

const router = useRouter()
const chat = useChatStore()
const quiz = useQuestionnaireStore()
const archive = useArchiveStore()
const analysis = useAnalysisStore()
const { mode } = storeToRefs(analysis) 

const modeChoice = ref(false) 
const confirmMode = ref(null) 
const answer = ref('') 
const note = ref('') 
const noteOpen = ref(false) 
const genLoading = ref(false)

const showExitConfirm = ref(false) 
let pendingPath = null 

const freeInput = ref('')
const freeRef = ref(null)
const chatMainRef = ref(null)


const micSupported = speechSupported()
const listening = ref(false)
let rec = null

function toggleMic() {
  if (!micSupported) return
  if (rec) {
    rec.stop()
    rec = null
    listening.value = false
    return
  }
  rec = createSpeech({
    onText: (t) => {
      freeInput.value = t
      resizeFree()
    },
    onState: (s) => {
      listening.value = s
      if (!s) rec = null
    }
  })
  rec.start()
}

const canNext = computed(() => !quiz.busy && (answer.value || '').trim() !== '')
const canGenerate = computed(
  () =>
    !chat.busy &&
    !genLoading.value &&
    (quiz.answered.length > 0 || (answer.value || '').trim() !== '' || chat.messages.length > 1)
)
const progressWidth = computed(() => {
  const target = 8 
  return Math.min(100, Math.round((quiz.answered.length / target) * 100)) + '%'
})

const chips = [
  '我想做个奶茶店点单小程序，顾客扫码点餐付款，店里能看订单',
  '我只想做一个能管理会员的系统',
  '我也说不清，就有一堆聊天记录'
]

async function startAnalysis() {
  if (chat.busy) return
  await chat.refreshUsage()
  if (chat.locked) {
    showToast('次数已用完，无法开始分析')
    return
  }
  modeChoice.value = true
}

function askMode(m) {
  confirmMode.value = m
}

async function confirmStart() {
  const m = confirmMode.value
  confirmMode.value = null
  try {
    
    chat.applyUsage(await api.consume())
  } catch (e) {
    if (e.status === 403) {
      chat.usage.locked = true
      modeChoice.value = false
    }
    showToast(e.message || '开始分析失败，请重试')
    return
  }
  startMode(m)
}

function startMode(m) {
  modeChoice.value = false
  if (m === 'quiz') {
    quiz.start(chat.sessionId)
    answer.value = ''
    note.value = ''
    noteOpen.value = false
    analysis.start('quiz')
  } else {
    analysis.start('chat')
  }
  analysis.saveDraft()
}

async function goNext() {
  if (!canNext.value) return
  try {
    await quiz.submit(answer.value, note.value)
    answer.value = ''
    note.value = ''
    noteOpen.value = false
    analysis.saveDraft()
  } catch (e) {
    if (e.status === 403) {
      chat.usage.locked = true
      return
    }
    showToast(e.message || '出题失败，请重试')
  }
}

async function continueAsk() {
  try {
    await quiz.continueAsk()
    answer.value = ''
    note.value = ''
    noteOpen.value = false
    analysis.saveDraft()
  } catch (e) {
    showToast(e.message || '出题失败，请重试')
  }
}

function goBack() {
  quiz.back()
  answer.value = (quiz.current && quiz.current._prevAnswer) || ''
  note.value = (quiz.current && quiz.current._prevNote) || ''
  noteOpen.value = !!(quiz.current && quiz.current._prevNote)
  analysis.saveDraft()
}

function collectAnswers() {
  
  const list = quiz.answered.map((a) => ({
    question: a.question,
    answer: multiToText(a.answer, a.type),
    note: a.note || ''
  }))
  const cur = quiz.current
  const val = (answer.value || '').trim()
  if (cur && val)
    list.push({
      question: cur.question,
      answer: multiToText(val, cur.type),
      note: (note.value || '').trim()
    })
  return list
}

async function generate() {
  if (!canGenerate.value) return
  genLoading.value = true
  try {
    const data = await api.generateDoc(chat.sessionId, collectAnswers())
    archive.add(data.document, data.confirm_items, data.assessment)
    chat.applyUsage(data.usage)
    showToast('文档已保存，可在「我的图纸」中查看')
    resetToStart()
  } catch (e) {
    if (e.status === 403) {
      chat.usage.locked = true
    } else {
      showToast(e.message || '文档生成失败')
    }
  } finally {
    genLoading.value = false
  }
}

function resetToStart() {
  analysis.abandon()
  quiz.reset()
  chat.resetSession()
  answer.value = ''
  note.value = ''
  noteOpen.value = false
  freeInput.value = ''
  modeChoice.value = false
}

function abandonAnalysis() {
  analysis.abandon()
  quiz.reset()
  chat.resetSession()
  answer.value = ''
  note.value = ''
  noteOpen.value = false
  freeInput.value = ''
  modeChoice.value = false
}

function openAbandon() {
  pendingPath = null
  showExitConfirm.value = true
}

function continueAnalysis() {
  showExitConfirm.value = false
  pendingPath = null
}

function confirmExit() {
  const target = pendingPath
  showExitConfirm.value = false
  pendingPath = null
  abandonAnalysis()
  if (target) router.push(target)
}

function scrollChatBottom() {
  nextTick(() => {
    const el = chatMainRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function resizeFree() {
  const el = freeRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 100) + 'px'
}

function onFreeKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendFree()
  }
}

async function sendFree() {
  const value = freeInput.value.trim()
  if (!value || chat.busy) return
  chat.busy = true
  chat.messages.push({ role: 'user', content: value, done: true })
  chat.messages.push({
    role: 'assistant',
    content: '',
    status: '',
    statusDone: false,
    thinking: true,
    done: false
  })
  const bubble = chat.messages[chat.messages.length - 1]
  freeInput.value = ''
  resizeFree()
  scrollChatBottom()

  let answerText = ''
  try {
    await api.chatStream(value, chat.sessionId, (event) => {
      if (event.type === 'tool_start') {
        bubble.status = '正在检索知识库…'
        bubble.statusDone = false
      } else if (event.type === 'tool_args') {
        const q = event.args && event.args.query
        if (q) bubble.status = `检索「${q}」`
      } else if (event.type === 'tool_end') {
        bubble.status = '已检索知识库'
        bubble.statusDone = true
      } else if (event.type === 'token') {
        bubble.thinking = false
        answerText += event.content || ''
        bubble.content = answerText
      } else if (event.type === 'done') {
        answerText = event.content || answerText
        bubble.content = answerText
      } else if (event.type === 'error') {
        bubble.thinking = false
        answerText += (answerText ? '\n\n' : '') + '> ' + (event.content || '服务端出错')
        bubble.content = answerText
      }
    })
  } catch (e) {
    if (e.locked) {
      chat.usage.locked = true
      chat.busy = false
      return
    }
    bubble.thinking = false
    answerText +=
      (answerText ? '\n\n' : '') + `> 请求失败：${e.message}（检查后端是否在运行）`
    bubble.content = answerText
  }

  bubble.thinking = false
  bubble.done = true
  if (bubble.status) bubble.statusDone = true
  if (!String(bubble.content || '').trim()) bubble.content = '（没有收到内容，请重试）'
  if (analysis.active) analysis.saveDraft()
  chat.busy = false
  scrollChatBottom()
}


onBeforeRouteLeave((to) => {
  if (!analysis.active) return true
  pendingPath = to.fullPath
  showExitConfirm.value = true
  return false
})

onMounted(async () => {
  analysis.restoreDraft() 
  await chat.init()
})
</script>

<template>
  <div class="chat-page">
    <AppHeader />

    
    <main v-if="chat.locked && mode === ''" class="main">
      <LockCard :max="chat.usage.max" />
    </main>

    
    <main v-else-if="mode === ''" class="main center">
      <div class="start-entry card">
        <div class="start-icon"><img :src="logo" alt="极构" /></div>
        <h2>需求分析</h2>
        <p>
          告诉我您的需求，我会帮您判断还没有什么。
        </p>

        <template v-if="!modeChoice">
          <button type="button" class="start-btn" :disabled="chat.busy" @click="startAnalysis">
            开始需求分析
          </button>
        </template>
        <template v-else>
          <div class="mode-pick">
            <button type="button" class="mode-btn" @click="askMode('quiz')">
              <span class="mode-title">按问卷答题</span>
              <span class="mode-desc">选择题 + 填空题，一题一屏；每道题都能补充你的想法</span>
            </button>
            <button type="button" class="mode-btn" @click="askMode('chat')">
              <span class="mode-title">自由对话</span>
              <span class="mode-desc">像聊天一样直接说，适合已经有比较明确的想法</span>
            </button>
          </div>
        </template>
      </div>
    </main>

    
    <main v-else-if="mode === 'quiz'" class="main">
        <div v-if="!quiz.finished" class="progress-row">
          <div class="progress-bar"><div class="progress-fill" :style="{ width: progressWidth }"></div></div>
          <span class="progress-label">第 {{ quiz.step }} 题 · 已答 {{ quiz.answered.length }} 题</span>
          <button type="button" class="abandon-link" @click="openAbandon">放弃</button>
        </div>

        <div class="qwrap card">
          <template v-if="quiz.finished">
            <div class="finish-card">
              <div class="finish-icon">✅</div>
              <h3>信息收集得差不多了</h3>
              <p class="finish-summary">{{ quiz.summary }}</p>
              <div class="quiz-nav">
                <button type="button" class="nav-btn" :disabled="quiz.busy" @click="continueAsk">
                  再补充几点
                </button>
                <button type="button" class="nav-btn primary" :disabled="genLoading" @click="generate">
                  <span v-if="genLoading" class="spin"></span>
                  <span v-else>生成需求报告</span>
                </button>
              </div>
              <button type="button" class="abandon-link center" @click="openAbandon">放弃本次分析</button>
            </div>
          </template>
          <template v-else>
            <QuestionCard v-model="answer" :question="quiz.current" />

            <button type="button" class="note-toggle" :class="{ on: noteOpen }" @click="noteOpen = !noteOpen">
              <span>💡 补充说明</span>
              <span v-if="(note || '').trim()" class="note-badge">已填写</span>
            </button>
            <div v-if="noteOpen" class="note-box">
              <textarea
                v-model="note"
                rows="3"
                placeholder="如果你突然有些想法，写在这里，我会据此调整后面的提问（比如：预算已经定了、想先做个简单的试试）"
              ></textarea>
            </div>

            <div class="quiz-nav">
              <button type="button" class="nav-btn" :disabled="!quiz.canBack" @click="goBack">
                上一题
              </button>
              <button type="button" class="nav-btn primary" :disabled="!canNext" @click="goNext">
                <span v-if="quiz.busy" class="spin"></span>
                <span v-else>下一题</span>
              </button>
            </div>
          </template>
        </div>

        <button v-if="!quiz.finished" type="button" class="gen-btn" :disabled="!canGenerate" @click="generate">
          <span v-if="genLoading" class="spin"></span>
          <span v-else>生成需求报告</span>
          <span class="left">剩余 <b>{{ chat.usage.remaining }}</b> 次</span>
        </button>
      </main>

      
      <main v-else ref="chatMainRef" class="main chat-main">
        <button type="button" class="abandon-link chat-abandon" @click="openAbandon">放弃本次分析</button>
        <template v-for="(m, i) in chat.messages" :key="i">
          <DocCard v-if="m.role === 'doc'" :document="m.document" :doc-id="m.docId" />
          <ChatBubble
            v-else
            :role="m.role"
            :content="m.content"
            :status="m.status"
            :status-done="m.statusDone"
            :thinking="m.thinking"
            :streaming="m.role === 'assistant' && !m.done && !m.thinking && !!m.content"
          />
        </template>

        <InspirationChips v-if="chat.messages.length === 1" :items="chips" @pick="(t) => { freeInput = t; sendFree() }" />

        <button type="button" class="gen-btn" :disabled="!canGenerate" @click="generate">
          <span v-if="genLoading" class="spin"></span>
          <span v-else>生成需求报告</span>
          <span class="left">剩余 <b>{{ chat.usage.remaining }}</b> 次</span>
        </button>

        <div class="composer">
          <textarea
            ref="freeRef"
            v-model="freeInput"
            rows="1"
            :disabled="chat.busy"
            placeholder="自由提问 / 补充…（Enter 发送，Shift+Enter 换行）"
            @keydown="onFreeKey"
            @input="resizeFree"
          ></textarea>
          <button
            v-if="micSupported"
            type="button"
            class="mic"
            :class="{ on: listening }"
            :disabled="chat.busy"
            @click="toggleMic"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4M8 22h8" />
            </svg>
          </button>
          <button type="button" class="send" :disabled="chat.busy || !freeInput.trim()" @click="sendFree">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 19V5M5 12l7-7 7 7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </main>

    
    <div v-if="confirmMode" class="confirm-mask" @click.self="confirmMode = null">
      <div class="confirm-card card">
        <h3>开始需求分析</h3>
        <p>
          本次将消耗 <b>1 次</b>次数（剩余 {{ chat.usage.remaining }} 次），确定开始吗？
        </p>
        <div class="confirm-actions">
          <button type="button" class="nav-btn" @click="confirmMode = null">取消</button>
          <button type="button" class="nav-btn primary" @click="confirmStart">确定</button>
        </div>
      </div>
    </div>

    
    <div v-if="showExitConfirm" class="confirm-mask">
      <div class="confirm-card card">
        <h3>放弃本次分析？</h3>
        <p>
          本次需求分析尚未生成文档，已消耗 <b>1 次</b>次数（不退还）。放弃后本次进度将被清空。
        </p>
        <div class="confirm-actions">
          <button type="button" class="nav-btn" @click="continueAnalysis">继续分析</button>
          <button type="button" class="nav-btn primary" @click="confirmExit">
            {{ pendingPath ? '放弃并离开' : '放弃本次分析' }}
          </button>
        </div>
      </div>
    </div>

    <BottomNav />
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.main {
  flex: 1;
  overflow-y: auto;
  padding: 18px 16px 20px;
  scroll-behavior: smooth;
}

.main.center {
  display: flex;
  align-items: center;
  justify-content: center;
}


.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #4f46e5, #0ea5a4);
  transition: width 0.3s;
}

.progress-label {
  font-size: 12.5px;
  color: var(--ink-3);
  white-space: nowrap;
}

.abandon-link {
  flex: none;
  font-size: 12.5px;
  padding: 4px 10px;
  border-radius: 999px;
  background: transparent;
  border: 1px solid var(--line);
  color: var(--ink-3);
}

.abandon-link:active {
  background: var(--bg);
}

.abandon-link.center {
  display: block;
  margin: 14px auto 0;
}

.chat-abandon {
  align-self: flex-start;
}


.qwrap {
  padding: 22px 18px;
  margin-bottom: 14px;
}

.quiz-nav {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.nav-btn {
  flex: 1;
  height: 46px;
  border-radius: 13px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.18s;
}

.nav-btn.primary {
  flex: 1.4;
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  font-weight: 600;
}

.nav-btn.primary:hover:not(:disabled) {
  background: #4338ca;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


.gen-btn {
  width: 100%;
  height: 50px;
  border-radius: 14px;
  background: var(--card);
  border: 1px solid var(--accent);
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.18s;
}

.gen-btn:hover:not(:disabled) {
  background: var(--accent);
  color: #fff;
}

.gen-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.gen-btn .left {
  font-size: 12px;
  color: var(--ink-3);
  font-weight: 400;
}

.gen-btn:hover .left {
  color: rgba(255, 255, 255, 0.85);
}

.gen-btn .left b {
  color: var(--accent);
  font-weight: 650;
}

.gen-btn:hover .left b {
  color: #fff;
}


.chat-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.composer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 9px 9px 9px 16px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: var(--shadow);
  margin-top: auto;
  transition: border-color 0.18s;
}

.composer:focus-within {
  border-color: var(--accent);
}

.composer textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font: inherit;
  color: var(--ink);
  max-height: 100px;
  padding: 7px 0;
  line-height: 1.6;
}

.composer textarea::placeholder {
  color: var(--ink-3);
}

.mic {
  flex: none;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  border: 1px solid var(--line);
  cursor: pointer;
  background: var(--bg);
  color: var(--ink-2);
  display: grid;
  place-items: center;
  transition: all 0.18s;
}

.mic.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  animation: micPulse 1.2s ease infinite;
}

.mic:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes micPulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4);
  }
  50% {
    box-shadow: 0 0 0 7px rgba(79, 70, 229, 0);
  }
}

.send {
  flex: none;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  border: none;
  cursor: pointer;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  transition: all 0.18s;
}

.send:hover {
  background: #4338ca;
}

.send:disabled {
  background: #c7cbe0;
  cursor: not-allowed;
}


.start-entry {
  max-width: 440px;
  padding: 30px 24px;
  text-align: center;
}

.start-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 12px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.start-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 6px;
}

.start-entry h2 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
}

.start-entry p {
  margin: 0 0 20px;
  font-size: 13.5px;
  color: var(--ink-2);
  line-height: 1.7;
}

.start-btn {
  width: 100%;
  height: 46px;
  border-radius: 13px;
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  transition: background 0.18s;
}

.start-btn:hover {
  background: #4338ca;
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


.mode-pick {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 16px;
  border-radius: 14px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink);
  text-align: left;
  transition: all 0.16s;
}

.mode-btn:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.mode-title {
  font-size: 16px;
  font-weight: 700;
}

.mode-desc {
  font-size: 12.5px;
  color: var(--ink-2);
  line-height: 1.6;
}


.note-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 13.5px;
  transition: all 0.16s;
}

.note-toggle.on {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
}

.note-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
}

.note-box {
  margin-top: 10px;
}

.note-box textarea {
  width: 100%;
  min-height: 76px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.16s;
}

.note-box textarea:focus {
  border-color: var(--accent);
}


.finish-card {
  text-align: center;
}

.finish-icon {
  width: 56px;
  height: 56px;
  margin: 6px auto 12px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 28px;
  background: var(--accent-soft);
}

.finish-card h3 {
  margin: 0 0 10px;
  font-size: 17px;
  font-weight: 700;
}

.finish-summary {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--ink-2);
  line-height: 1.7;
  text-align: left;
  white-space: pre-wrap;
}


.chat-main .gen-btn {
  margin-top: auto;
}

.chat-main .composer {
  margin-top: 10px;
}


.confirm-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 24px;
}

.confirm-card {
  width: 100%;
  max-width: 360px;
  padding: 24px 20px;
  text-align: center;
}

.confirm-card h3 {
  margin: 0 0 10px;
  font-size: 17px;
  font-weight: 700;
}

.confirm-card p {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--ink-2);
  line-height: 1.6;
}

.confirm-card p b {
  color: var(--accent);
}

.confirm-actions {
  display: flex;
  gap: 10px;
}

.confirm-actions .nav-btn {
  flex: 1;
}

@media (max-width: 640px) {
  .main {
    padding: 14px 12px 16px;
  }

  .tabs {
    padding: 10px 12px 0;
  }

  .qwrap {
    padding: 18px 14px;
  }
}
</style>
