<script setup>
import fluxoMarkWhite from '@/assets/brand/fluxo-mark-white.png'

defineProps({
  tagline: { type: String, default: 'Sua vida financeira, do dia à noite.' },
  subtagline: {
    type: String,
    default: 'Investimentos, despesas, metas e cartões — tudo num só lugar.',
  },
})
</script>

<template>
  <div class="grid min-h-screen md:grid-cols-2">
    <div class="relative hidden overflow-hidden bg-gradient-to-br from-wine via-wine to-[#5a0f2c] md:flex md:flex-col md:justify-between md:p-12 lg:p-16">
      <div aria-hidden="true" class="pointer-events-none absolute inset-0 overflow-hidden">
        <div class="absolute -left-20 -top-24 h-72 w-72 rounded-full bg-coral/30 blur-3xl" />
        <div class="absolute -bottom-32 -right-16 h-96 w-96 rounded-full bg-peach/20 blur-3xl" />
        <div class="absolute right-1/4 top-1/3 h-40 w-40 rounded-full bg-sand/10 blur-2xl" />
      </div>

      <img :src="fluxoMarkWhite" alt="Fluxo" class="relative h-9 w-auto self-start" />

      <div class="relative">
        <p class="max-w-sm text-3xl font-bold leading-tight text-white lg:text-4xl">{{ tagline }}</p>
        <p class="mt-4 max-w-xs text-sm text-white/70">{{ subtagline }}</p>
      </div>
    </div>

    <div class="flex items-center justify-center bg-stone-50 px-4 py-12 sm:px-8">
      <div class="w-full max-w-sm">
        <slot />
      </div>
    </div>
  </div>
</template>
