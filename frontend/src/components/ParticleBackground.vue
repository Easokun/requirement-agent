<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const canvasRef = ref(null)

let ctx = null
let raf = 0
let w = 0
let h = 0
let dpr = 1
let particles = []


const COLORS = [
  '147, 197, 253',
  '191, 219, 254',
  '224, 242, 254',
  '125, 211, 252'
]

function build() {
  const area = Math.max(w * h, 1)
  const small = Math.min(90, Math.floor(area / 8000))
  const big = Math.min(16, Math.floor(area / 35000))
  particles = []
  for (let i = 0; i < small; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 0.5 + Math.random() * 1.5,
      vx: (Math.random() - 0.5) * 0.32,
      vy: (Math.random() - 0.5) * 0.32,
      a: 0.18 + Math.random() * 0.5,
      tw: Math.random() * Math.PI * 2,
      ts: 0.008 + Math.random() * 0.028,
      c: COLORS[(Math.random() * COLORS.length) | 0]
    })
  }
  for (let i = 0; i < big; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 1.7 + Math.random() * 2.3,
      vx: (Math.random() - 0.5) * 0.16,
      vy: (Math.random() - 0.5) * 0.16,
      a: 0.5 + Math.random() * 0.45,
      tw: Math.random() * Math.PI * 2,
      ts: 0.01 + Math.random() * 0.03,
      c: '219, 234, 254'
    })
  }
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  w = rect.width
  h = rect.height
  canvas.width = Math.floor(w * dpr)
  canvas.height = Math.floor(h * dpr)
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  build()
}

function tick() {
  ctx.clearRect(0, 0, w, h)
  for (const p of particles) {
    p.x += p.vx
    p.y += p.vy
    if (p.x < -14) p.x = w + 14
    else if (p.x > w + 14) p.x = -14
    if (p.y < -14) p.y = h + 14
    else if (p.y > h + 14) p.y = -14
    p.tw += p.ts
    const alpha = p.a * (0.55 + 0.45 * Math.sin(p.tw))
    
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r * 2.7, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${p.c}, ${(alpha * 0.22).toFixed(3)})`
    ctx.fill()
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${p.c}, ${Math.min(1, alpha).toFixed(3)})`
    ctx.fill()
  }
  raf = requestAnimationFrame(tick)
}

onMounted(() => {
  ctx = canvasRef.value.getContext('2d')
  resize()
  window.addEventListener('resize', resize)
  raf = requestAnimationFrame(tick)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', resize)
})
</script>

<template>
  <div class="particle-bg" aria-hidden="true">
    <canvas ref="canvasRef"></canvas>
    <div class="grain"></div>
  </div>
</template>

<style scoped>
.particle-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.particle-bg canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.grain {
  position: absolute;
  inset: 0;
  opacity: 0.07;
  mix-blend-mode: soft-light;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
</style>
