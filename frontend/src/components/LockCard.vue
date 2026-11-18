<script setup>
defineProps({
  max: { type: Number, default: 5 }
})
</script>

<template>
  <div class="lockcard card">
    <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="var(--danger)" stroke-width="1.8">
      <rect x="5" y="10" width="14" height="10" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke-linecap="round" />
      <circle cx="12" cy="15" r="1.6" fill="var(--danger)" stroke="none" />
    </svg>
    <h2>需求分析次数已用满（{{ max }} 次）</h2>
    <p>答题与对话均已锁定。如需重置，请联系管理员重置账号额度。</p>
  </div>
</template>

<style scoped>
.lockcard {
  max-width: 480px;
  margin: 60px auto;
  text-align: center;
  border-color: #f3d7d7;
  padding: 38px 30px;
}

.lockcard h2 {
  margin: 10px 0 8px;
  font-size: 17px;
  color: var(--danger);
}

.lockcard p {
  margin: 0;
  color: var(--ink-2);
  font-size: 13.5px;
}

@media (max-width: 640px) {
  .lockcard {
    margin: 40px 16px;
    padding: 30px 22px;
  }
}
</style>
