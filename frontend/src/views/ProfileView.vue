<!-- 由 deepseek v4 pro 生成 -->
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useArchiveStore } from '../stores/archive'
import { showToast } from '../utils/toast'
import logo from '../assets/logo.png'

const router = useRouter()
const user = useUserStore()
const archive = useArchiveStore()

const CONTACT_EMAIL = 'jiay41184@gmail.com'

const industry = ref('')
const savingIndustry = ref(false)

const showPwd = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const savingPwd = ref(false)

const showLogout = ref(false)
const showForgot = ref(false)
const showContact = ref(false)
const showCancel = ref(false)
const cancelPassword = ref('')
const canceling = ref(false)

const quotaPercent = computed(() => {
  const max = user.usage.max || 5
  const remaining = Math.max(0, user.usage.remaining || 0)
  return Math.round((remaining / max) * 100)
})

onMounted(async () => {
  try {
    await user.fetchMe()
    industry.value = user.industry
  } catch {
    
  }
})

async function saveIndustry() {
  const value = industry.value.trim()
  if (!value) {
    industry.value = user.industry || ''
    showToast('所属行业不能为空')
    return
  }
  
  if (value === (user.industry || '')) return
  savingIndustry.value = true
  try {
    await user.updateIndustry(value)
    showToast('已保存')
  } catch (error) {
    showToast(error.message || '保存失败')
  } finally {
    savingIndustry.value = false
  }
}

function openPwd() {
  oldPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  showPwd.value = true
}

async function submitPassword() {
  if (!oldPassword.value) {
    showToast('请输入旧密码')
    return
  }
  if (!newPassword.value) {
    showToast('请输入新密码')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    confirmPassword.value = ''
    showToast('两次输入的新密码不一致')
    return
  }
  savingPwd.value = true
  try {
    await user.changePassword(oldPassword.value, newPassword.value)
    showToast('密码修改成功')
    showPwd.value = false
  } catch (error) {
    showToast(error.message || '修改失败')
  } finally {
    savingPwd.value = false
  }
}

function openForgot() {
  showForgot.value = true
}

function openContact() {
  showContact.value = true
}

function openCancel() {
  cancelPassword.value = ''
  showCancel.value = true
}

async function submitCancel() {
  if (!cancelPassword.value) {
    showToast('请输入密码以确认注销')
    return
  }
  canceling.value = true
  try {
    await user.deleteAccount(cancelPassword.value)
    archive.clear()
    showToast('账号已注销')
    router.replace('/login')
  } catch (error) {
    showToast(error.message || '注销失败')
  } finally {
    canceling.value = false
  }
}

async function logout() {
  showLogout.value = false
  await user.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="profile-page">
    <header class="app-header">
      <button type="button" class="icon-btn" @click="router.back()">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 5l-7 7 7 7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <div class="titles">
        <h1>我的</h1>
      </div>
    </header>

    <main class="profile-body">
      <section class="card info-card">
        <h2 class="card-title">账号信息</h2>

        <div class="row">
          <span class="label">账号名称</span>
          <span class="value">{{ user.username }}</span>
        </div>

        <div class="row column">
          <span class="label">
            所属行业
            <em v-if="savingIndustry" class="industry-saving">保存中…</em>
          </span>
          <div class="industry-edit">
            <input
              v-model="industry"
              type="text"
              placeholder="点击输入行业，例如：餐饮 / 零售 / 医疗（改完自动保存）"
              maxlength="64"
              @blur="saveIndustry"
              @keyup.enter="saveIndustry"
            />
          </div>
        </div>

        <div class="row column">
          <span class="label">剩余生成额度</span>
          <div class="quota">
            <div class="quota-num">
              <b :class="{ empty: user.usage.remaining <= 0 }">{{ user.usage.remaining }}</b>
              <em>/ {{ user.usage.max || 5 }} 次</em>
            </div>
            <div class="quota-bar">
              <div class="quota-fill" :style="{ width: quotaPercent + '%' }"></div>
            </div>
            <p v-if="user.usage.remaining <= 0" class="quota-tip">
              额度已用满，对话与报告生成均已锁定
            </p>
          </div>
        </div>
      </section>

      <section class="card setting-card">
        <h2 class="card-title">系统设置</h2>
        <button type="button" class="setting-row" @click="openPwd">
          <span>修改密码</span>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button type="button" class="setting-row" @click="openForgot">
          <span>忘记密码</span>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button type="button" class="setting-row" @click="router.push('/legal/terms')">
          <span>用户服务协议</span>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button type="button" class="setting-row" @click="router.push('/legal/privacy')">
          <span>隐私政策</span>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button type="button" class="setting-row" @click="openContact">
          <span>联系我们</span>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button type="button" class="setting-row danger" @click="openCancel">
          <span>账号注销</span>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </section>

      <button type="button" class="logout-btn" @click="showLogout = true">退出登录</button>
    </main>

    <transition name="fade">
      <div v-if="showPwd" class="modal-mask" @click.self="showPwd = false">
        <div class="modal card">
          <h3>修改密码</h3>
          <div class="field">
            <input
              v-model="oldPassword"
              type="password"
              placeholder="旧密码"
              autocomplete="current-password"
            />
          </div>
          <div class="field">
            <input
              v-model="newPassword"
              type="password"
              placeholder="新密码"
              autocomplete="new-password"
            />
          </div>
          <div class="field">
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="确认新密码"
              autocomplete="new-password"
              @keyup.enter="submitPassword"
            />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="showPwd = false">取消</button>
            <button type="button" class="btn-primary" :disabled="savingPwd" @click="submitPassword">
              <span v-if="savingPwd" class="spin"></span>
              <span v-else>确认修改</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showLogout" class="modal-mask" @click.self="showLogout = false">
        <div class="modal card">
          <h3>确认退出登录？</h3>
          <p class="modal-desc">退出后需要重新登录才能使用需求分析。</p>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="showLogout = false">取消</button>
            <button type="button" class="btn-primary danger" @click="logout">退出登录</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showForgot" class="modal-mask" @click.self="showForgot = false">
        <div class="modal card">
          <h3>忘记密码</h3>
          <p class="modal-desc">为保障账号安全，请通过管理员重置密码，重置后即可用新密码登录。</p>
          <div class="modal-actions">
            <button type="button" class="btn-primary" @click="showForgot = false">我知道了</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showContact" class="modal-mask" @click.self="showContact = false">
        <div class="modal card contact-modal">
          <img :src="logo" class="contact-logo" alt="极构" />
          <h3>极构 · 需求诊断顾问</h3>
          <a class="contact-mail" :href="'mailto:' + CONTACT_EMAIL">{{ CONTACT_EMAIL }}</a>
          <div class="modal-actions">
            <button type="button" class="btn-primary" @click="showContact = false">知道了</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showCancel" class="modal-mask" @click.self="showCancel = false">
        <div class="modal card">
          <h3>账号注销</h3>
          <p class="modal-desc">
            注销后账号、需求记录与对话记录将被删除且不可恢复，剩余额度一并作废。请先阅读
            <router-link to="/legal/cancellation">《账号注销协议》</router-link>。
          </p>
          <div class="field">
            <input
              v-model="cancelPassword"
              type="password"
              placeholder="输入密码确认注销"
              autocomplete="current-password"
              @keyup.enter="submitCancel"
            />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="showCancel = false">取消</button>
            <button type="button" class="btn-primary danger" :disabled="canceling" @click="submitCancel">
              <span v-if="canceling" class="spin"></span>
              <span v-else>确认注销</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.profile-page {
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

.profile-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card-title {
  margin: 0 0 14px;
  font-size: 13px;
  color: var(--ink-3);
  font-weight: 600;
  letter-spacing: 0.5px;
}

.info-card,
.setting-card {
  padding: 18px 16px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 0;
  border-top: 1px solid var(--line);
}

.row:first-of-type {
  border-top: none;
  padding-top: 0;
}

.row.column {
  flex-direction: column;
  align-items: stretch;
}

.label {
  font-size: 14px;
  color: var(--ink-2);
  flex: none;
}

.value {
  font-size: 15px;
  font-weight: 600;
}

.industry-edit {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.industry-edit input {
  flex: 1;
  height: 42px;
  padding: 0 12px;
  border-radius: 10px;
  background: var(--bg);
  border: 1.5px solid transparent;
  transition: border-color 0.15s, background 0.15s;
}

.industry-edit input:focus {
  border-color: var(--accent);
  background: #fff;
}

.industry-saving {
  font-style: normal;
  font-size: 12px;
  color: var(--accent);
  margin-left: 6px;
  font-weight: 400;
}

.quota {
  margin-top: 4px;
}

.quota-num {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 8px;
}

.quota-num b {
  font-size: 26px;
  color: var(--accent);
  font-weight: 700;
}

.quota-num b.empty {
  color: var(--danger);
}

.quota-num em {
  font-style: normal;
  font-size: 13px;
  color: var(--ink-3);
}

.quota-bar {
  height: 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  overflow: hidden;
}

.quota-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #4f46e5, #0ea5a4);
  transition: width 0.3s;
}

.quota-tip {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--danger);
}

.setting-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 0;
  font-size: 15px;
  color: var(--ink);
}

.setting-row svg {
  color: var(--ink-3);
}

.setting-row.danger {
  color: var(--danger);
}

.setting-row.danger svg {
  color: var(--danger);
}

.modal-desc a {
  color: var(--accent);
  font-weight: 600;
}

.contact-modal {
  text-align: center;
}

.contact-logo {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  object-fit: contain;
  padding: 6px;
  background: #fff;
  border: 1px solid var(--line);
  margin-bottom: 10px;
}

.contact-modal h3 {
  margin-bottom: 4px;
}

.contact-mail {
  display: inline-block;
  margin: 2px 0 16px;
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
  word-break: break-all;
}

.logout-btn {
  width: 100%;
  height: 48px;
  border-radius: 14px;
  background: var(--card);
  border: 1px solid #f3d7d7;
  color: var(--danger);
  font-size: 15px;
  font-weight: 600;
  transition: background 0.15s;
}

.logout-btn:active {
  background: #fdf0f0;
}


.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(26, 31, 54, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.modal {
  width: 100%;
  max-width: 360px;
  padding: 24px 22px;
}

.modal h3 {
  margin: 0 0 14px;
  font-size: 17px;
  font-weight: 700;
}

.modal-desc {
  margin: 0 0 18px;
  font-size: 13.5px;
  color: var(--ink-2);
}

.field {
  margin-bottom: 12px;
}

.field input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border-radius: 12px;
  background: var(--bg);
  border: 1.5px solid transparent;
  transition: border-color 0.15s, background 0.15s;
}

.field input:focus {
  border-color: var(--accent);
  background: #fff;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.btn-ghost {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 14px;
}

.btn-primary {
  flex: 1.4;
  height: 44px;
  border-radius: 12px;
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary.danger {
  background: var(--danger);
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
  .profile-body {
    padding: 12px;
  }
}
</style>
