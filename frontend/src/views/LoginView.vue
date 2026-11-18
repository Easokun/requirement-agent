<!-- 由 deepseek v4 pro 生成 -->
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { showToast } from '../utils/toast'
import { isPhone } from '../utils/validators'
import ParticleBackground from '../components/ParticleBackground.vue'
import logo from '../assets/logo.png'

const router = useRouter()
const user = useUserStore()

const username = ref('')
const password = ref('')
const accountChecked = ref(false)
const accountExists = ref(false)

function onUsernameInput() {
  accountChecked.value = false
  accountExists.value = false
  password.value = ''
}

async function checkAccount() {
  const name = username.value.trim()
  if (!name) {
    showToast('请输入手机号')
    return
  }
  if (!isPhone(name)) {
    showToast('账号需为 11 位手机号')
    return
  }
  try {
    accountChecked.value = false
    accountExists.value = await user.checkAccount(name)
    accountChecked.value = true
    if (!accountExists.value) {
      showToast('该账号尚未注册，请先注册')
    }
  } catch (error) {
    showToast(error.message || '网络异常，请稍后重试')
  }
}

async function submit() {
  const name = username.value.trim()
  if (!name) {
    showToast('请输入手机号')
    return
  }
  if (!isPhone(name)) {
    showToast('账号需为 11 位手机号')
    return
  }
  if (!accountChecked.value) {
    await checkAccount()
    return
  }
  if (!accountExists.value) {
    showToast('该账号尚未注册，请先注册')
    return
  }
  if (!password.value) {
    showToast('请输入密码')
    return
  }
  try {
    await user.login(name, password.value)
    showToast('登录成功')
    router.replace('/')
  } catch (error) {
    showToast(error.message || '登录失败')
  }
}
</script>

<template>
  <div class="auth-page">
    <ParticleBackground />
    <div class="auth-brand">
      <div class="brand-logo"><img :src="logo" alt="极构" /></div>
      <h1>极构</h1>
      <p>让一个想法从零到一</p>
    </div>

    <div class="auth-card card">
      <div class="field">
        <label>手机号</label>
        <input
          v-model="username"
          type="tel"
          maxlength="11"
          placeholder="请输入 11 位手机号"
          autocomplete="username"
          @input="onUsernameInput"
          @keyup.enter="submit"
        />
      </div>

      <div v-if="accountExists" class="field">
        <label>密码</label>
        <input
          v-model="password"
          type="password"
          placeholder="请输入密码"
          autocomplete="current-password"
          @keyup.enter="submit"
        />
      </div>

      <p v-if="accountChecked && !accountExists" class="account-tip">
        该账号尚未注册，无法输入密码
      </p>

      <button type="button" class="submit-btn" @click="submit">
        {{ accountExists ? '登录' : '下一步' }}
      </button>

      <p class="switch-line">
        还没有账号？
        <router-link to="/register">点击注册</router-link>
      </p>
    </div>

    <p class="local-tip">请确保您拥有我们的产品</p>
  </div>
</template>

<style scoped>
.auth-page {
  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px calc(32px + env(safe-area-inset-bottom));
  background: linear-gradient(165deg, #16357e 0%, #10245c 40%, #081536 100%);
  overflow-y: auto;
}

.auth-brand {
  position: relative;
  z-index: 1;
  text-align: center;
  margin-bottom: 26px;
}

.brand-logo {
  width: 72px;
  height: 72px;
  margin: 0 auto 10px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.brand-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 6px;
}

.auth-brand h1 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 4px;
  margin: 0;
  color: #fff;
}

.auth-brand p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.72);
  margin: 6px 0 0;
}

.auth-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  padding: 22px 18px;
}

.field {
  margin-bottom: 14px;
}

.field label {
  display: block;
  font-size: 13px;
  color: var(--ink-2);
  margin-bottom: 6px;
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

.account-tip {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--danger);
}

.submit-btn {
  width: 100%;
  height: 48px;
  border-radius: 14px;
  background: var(--accent);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  transition: background 0.15s;
}

.submit-btn:hover {
  background: #4338ca;
}

.switch-line {
  margin: 14px 0 0;
  text-align: center;
  font-size: 13px;
  color: var(--ink-2);
}

.local-tip {
  position: relative;
  z-index: 1;
  margin: 18px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}
</style>
