<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import parallaxSvg from '@/assets/parallax-hero.svg?raw'
import fluxoMark from '@/assets/brand/fluxo-mark-alpha.png'
import fluxoLogoHorizontal from '@/assets/brand/fluxo-logo-horizontal-alpha.png'
import { Wallet, ArrowDownCircle, Target, CreditCard, Landmark, Repeat } from '@lucide/vue'

const svgHost = ref(null)
const scrolled = ref(false)
const heroProgress = ref(0)

const features = [
  { icon: Wallet, title: 'Investimentos', text: 'Acompanhe ativos, preço médio e proventos em uma carteira só, com suporte a multi-moeda.' },
  { icon: ArrowDownCircle, title: 'Despesas & receitas', text: 'Categorize, importe extratos em CSV e veja pra onde o dinheiro está indo todo mês.' },
  { icon: Target, title: 'Metas', text: 'Defina metas financeiras e vincule investimentos a elas pra ver o progresso de verdade.' },
  { icon: CreditCard, title: 'Cartões', text: 'Controle faturas e compras no cartão de crédito sem sair do resto das suas finanças.' },
  { icon: Landmark, title: 'Empréstimos', text: 'Simule amortizações extras e acompanhe a evolução da dívida ao longo do tempo.' },
  { icon: Repeat, title: 'Recorrentes', text: 'Cadastre despesas e receitas recorrentes uma vez só e deixe o resto automático.' },
]

let els = {}
let ticking = false

function clamp01(v) {
  return Math.min(1, Math.max(0, v))
}

function windowed(progress, from, to) {
  return clamp01((progress - from) / (to - from))
}

function lerp(a, b, t) {
  return a + (b - a) * t
}

function applyFrame(progress) {
  const vh = window.innerHeight

  const p1 = windowed(progress, 0, 0.45)
  const hills1 = [
    ['h1-1', 0.55, 0.18], ['h1-2', 0.5, -0.1], ['h1-3', 0.32, 0.22],
    ['h1-4', 0.55, 0.18], ['h1-5', 0.38, 0.18], ['h1-6', 0.42, -0.45],
    ['h1-7', 0.9, 0.28], ['h1-8', 0.62, 0.03], ['h1-9', 0.62, -0.03],
  ]
  for (const [id, fy, fx] of hills1) {
    const el = els[id]
    if (el) el.style.transform = `translate(${fx * p1 * vh}px, ${fy * p1 * vh}px)`
  }
  if (els.cloudsBigL) els.cloudsBigL.style.transform = `translate(${-0.04 * p1 * vh}px, ${0.8 * p1 * vh}px)`
  if (els.cloudsBigR) els.cloudsBigR.style.transform = `translate(${-0.04 * p1 * vh}px, ${0.8 * p1 * vh}px)`
  if (els.hills1Group) els.hills1Group.style.opacity = String(1 - windowed(progress, 0.3, 0.48))

  const pSun = windowed(progress, 0, 0.36)
  if (els.bgGrad) els.bgGrad.setAttribute('cy', String(lerp(-50, 330, pSun)))

  const pBird = windowed(progress, 0.12, 0.55)
  if (els.bird) {
    els.bird.style.opacity = pBird > 0 && pBird < 1 ? '1' : String(1 - windowed(progress, 0.5, 0.6))
    els.bird.style.transform = `translate(${lerp(0, 520, pBird)}px, ${lerp(0, -160, pBird)}px)`
  }

  const pClouds = windowed(progress, 0, 0.7)
  if (els.cloud1) els.cloud1.style.transform = `translateX(${lerp(0, 320, pClouds)}px)`
  if (els.cloud2) els.cloud2.style.transform = `translateX(${lerp(0, 640, pClouds)}px)`
  if (els.cloud3) els.cloud3.style.transform = `translateX(${lerp(0, -640, pClouds)}px)`
  if (els.cloud4) els.cloud4.style.transform = `translate(${lerp(0, -450, pClouds)}px, ${lerp(0, 16, pClouds)}px)`

  const p2 = windowed(progress, 0.15, 0.4)
  const hills2 = [
    ['h2-2', 320], ['h2-3', 420], ['h2-4', 420], ['h2-5', 480], ['h2-6', 540],
  ]
  for (const [id, from] of hills2) {
    const el = els[id]
    if (el) el.style.transform = `translateY(${lerp(from, 0, p2)}px)`
  }

  const pBats = windowed(progress, 0.4, 0.68)
  if (els.bats) {
    els.bats.style.opacity = pBats > 0 ? '1' : '0'
    els.bats.style.transform = `translateY(${lerp(180, 10, pBats)}px) scale(${lerp(0.2, 0.85, pBats)})`
    els.bats.style.transformOrigin = '50% 50%'
  }

  const p3 = windowed(progress, 0.6, 1)
  if (els.scene3) {
    els.scene3.style.visibility = progress > 0.58 ? 'visible' : 'hidden'
    els.scene3.style.opacity = String(windowed(progress, 0.6, 0.8))
  }
  if (els.hills3Group) {
    els.hills3Group.style.transform = `translateY(${lerp(140, -40, p3)}px)`
  }
  if (els.stars) {
    els.stars.style.opacity = String(windowed(progress, 0.62, 0.9) * 0.9)
  }
  if (els.fstar) {
    const pf = windowed(progress, 0.72, 1)
    els.fstar.style.opacity = progress > 0.7 && progress < 0.98 ? '1' : '0'
    els.fstar.style.transform = `translate(${lerp(0, -260, pf)}px, ${lerp(0, -90, pf)}px)`
  }
}

function onScroll() {
  if (ticking) return
  ticking = true
  requestAnimationFrame(() => {
    const section = document.getElementById('parallax-section')
    let progress = 0
    if (section) {
      const rect = section.getBoundingClientRect()
      const total = rect.height - window.innerHeight
      progress = total > 0 ? clamp01(-rect.top / total) : 0
      applyFrame(progress)
    }
    heroProgress.value = progress
    // só troca pro header sólido depois que a cena termina de rolar —
    // enquanto isso o scrim escuro no topo cuida do contraste do texto/logo
    scrolled.value = progress >= 0.98
    ticking = false
  })
}

onMounted(() => {
  const host = svgHost.value
  if (host) {
    const byId = (id) => host.querySelector(`#${id}`)
    els = {
      'h1-1': byId('h1-1'), 'h1-2': byId('h1-2'), 'h1-3': byId('h1-3'), 'h1-4': byId('h1-4'),
      'h1-5': byId('h1-5'), 'h1-6': byId('h1-6'), 'h1-7': byId('h1-7'), 'h1-8': byId('h1-8'), 'h1-9': byId('h1-9'),
      'h2-2': byId('h2-2'), 'h2-3': byId('h2-3'), 'h2-4': byId('h2-4'), 'h2-5': byId('h2-5'), 'h2-6': byId('h2-6'),
      cloudsBigL: byId('cloudsBig-L'), cloudsBigR: byId('cloudsBig-R'),
      bird: byId('bird'), hills1Group: byId('hills1'),
      bgGrad: byId('bg_grad'),
      cloud1: byId('cloud1'), cloud2: byId('cloud2'), cloud3: byId('cloud3'), cloud4: byId('cloud4'),
      bats: byId('bats'),
      scene3: byId('scene3'), hills3Group: byId('hills3'), stars: byId('stars'), fstar: byId('fstar'),
    }
    for (const el of Object.values(els)) {
      if (el && el.style) el.style.willChange = 'transform, opacity'
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <div class="bg-stone-50">
    <header
      class="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-4 py-3 transition-colors duration-300 sm:px-8"
      :class="scrolled ? 'bg-white/90 shadow-sm backdrop-blur' : 'bg-gradient-to-b from-black/45 via-black/15 to-transparent'"
    >
      <img :src="scrolled ? fluxoLogoHorizontal : fluxoMark" alt="Fluxo" class="w-auto transition-all" :class="scrolled ? 'h-8' : 'h-7'" />
      <nav class="flex items-center gap-2 sm:gap-3">
        <RouterLink
          :to="{ name: 'login' }"
          class="rounded-xl px-3 py-2 text-sm font-semibold transition"
          :class="scrolled ? 'text-stone-700 hover:bg-stone-100' : 'text-white hover:bg-white/10'"
        >
          Entrar
        </RouterLink>
        <RouterLink :to="{ name: 'signup' }" class="btn-primary">
          Criar conta
        </RouterLink>
      </nav>
    </header>

    <section id="parallax-section" class="relative" style="height: 340vh;">
      <div class="sticky top-0 h-screen overflow-hidden">
        <div ref="svgHost" class="absolute inset-0 [&_svg]:h-full [&_svg]:w-full" v-html="parallaxSvg" />

        <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center px-4 text-center">

          <div
            class="absolute inset-0"
            style="background: radial-gradient(ellipse 65% 50% at 50% 50%, rgba(10,8,20,0.55) 0%, rgba(10,8,20,0.25) 55%, transparent 78%);"
          />

          <h1 class="relative max-w-2xl text-4xl font-extrabold tracking-tight text-white drop-shadow-md sm:text-5xl">
            Sua vida financeira, do dia à noite
          </h1>
          <p class="relative mt-4 max-w-md text-base text-white/90 drop-shadow sm:text-lg">
            Investimentos, despesas, metas e cartões num só lugar. Role a página pra ver a Fluxo em ação.
          </p>
          <div class="pointer-events-auto relative mt-8 flex flex-wrap items-center justify-center gap-3">
            <RouterLink :to="{ name: 'signup' }" class="btn-primary px-6 py-3 text-base">
              Criar conta grátis
            </RouterLink>
            <RouterLink :to="{ name: 'login' }" class="btn-secondary border-white/40 bg-white/10 px-6 py-3 text-base text-white hover:bg-white/20">
              Já tenho conta
            </RouterLink>
          </div>
        </div>

        <svg
          class="scroll-hint pointer-events-none absolute bottom-8 left-1/2 -translate-x-1/2"
          :style="{ opacity: Math.max(0, 1 - heroProgress / 0.05) }"
          width="16" height="9" viewBox="0 0 16 9" fill="none"
        >
          <path d="M1 1L8 7.5L15 1" stroke="#fff" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
    </section>

    <section class="mx-auto max-w-6xl px-4 py-20 sm:px-8">
      <div class="mx-auto max-w-2xl text-center">
        <h2 class="text-3xl font-bold text-stone-900">Tudo o que sua carteira precisa</h2>
        <p class="mt-3 text-stone-500">Sem planilha solta, sem app pra cada coisa. Um lugar só pra organizar dinheiro.</p>
      </div>

      <div class="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="f in features" :key="f.title" class="card">
          <div class="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-coral/20 text-wine">
            <component :is="f.icon" :size="20" />
          </div>
          <h3 class="font-semibold text-stone-800">{{ f.title }}</h3>
          <p class="mt-1.5 text-sm text-stone-500">{{ f.text }}</p>
        </div>
      </div>
    </section>

    <section class="border-t border-stone-200 bg-white py-16">
      <div class="mx-auto flex max-w-3xl flex-col items-center gap-5 px-4 text-center">
        <h2 class="text-2xl font-bold text-stone-900">Bora organizar as finanças?</h2>
        <p class="text-stone-500">Leva menos de um minuto pra criar sua conta.</p>
        <RouterLink :to="{ name: 'signup' }" class="btn-primary px-6 py-3 text-base">
          Criar conta grátis
        </RouterLink>
      </div>
    </section>

    <footer class="border-t border-stone-200 px-4 py-8 text-center text-sm text-stone-400 sm:px-8">
      © {{ new Date().getFullYear() }} Fluxo. Todos os direitos reservados.
    </footer>
  </div>
</template>

<style>

#info,
#info2 {
  display: none !important;
}

.scroll-hint {
  animation: scroll-hint-bounce 1.8s ease-in-out infinite;
  transition: opacity 0.2s ease;
}

@keyframes scroll-hint-bounce {
  0%, 100% { transform: translate(-50%, 0); }
  50% { transform: translate(-50%, 5px); }
}

@media (prefers-reduced-motion: reduce) {
  .scroll-hint {
    animation: none;
  }
}
</style>
