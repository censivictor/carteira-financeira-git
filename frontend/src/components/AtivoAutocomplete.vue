<script setup>
import { ref, watch } from 'vue'
import { api } from '@/lib/api'

const props = defineProps({
  modelValue: { type: String, default: '' },
  tipo: { type: String, required: true }, // 'ACAO' | 'FII' | 'CRIPTO'
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'select'])

const texto = ref(props.modelValue)
const sugestoes = ref([])
const mostrarLista = ref(false)
let debounceId = null
let controller = null

watch(() => props.modelValue, (v) => { texto.value = v })

async function buscar(q) {
  if (q.trim().length < 2) {
    sugestoes.value = []
    mostrarLista.value = false
    return
  }
  if (controller) controller.abort()
  controller = new AbortController()
  try {
    const resp = await fetch(`/api/investimentos/buscar/?tipo=${props.tipo}&q=${encodeURIComponent(q)}`, {
      credentials: 'include',
      signal: controller.signal,
    })
    const data = await resp.json()
    sugestoes.value = data.results || []
    mostrarLista.value = sugestoes.value.length > 0
  } catch (e) {
    if (e.name !== 'AbortError') sugestoes.value = []
  }
}

function aoDigitar(ev) {
  const valor = ev.target.value
  texto.value = valor
  emit('update:modelValue', valor)
  clearTimeout(debounceId)
  debounceId = setTimeout(() => buscar(valor), 300)
}

function selecionar(item) {
  texto.value = item.value
  emit('update:modelValue', item.value)
  emit('select', item)
  mostrarLista.value = false
}

function aoSairDoFoco() {
  // pequeno delay pra permitir o click na sugestão registrar antes de esconder a lista
  setTimeout(() => { mostrarLista.value = false }, 150)
}
</script>

<template>
  <div class="relative">
    <input
      type="text"
      class="input"
      :value="texto"
      :placeholder="placeholder"
      autocomplete="off"
      @input="aoDigitar"
      @blur="aoSairDoFoco"
      @focus="mostrarLista = sugestoes.length > 0"
    />
    <ul
      v-if="mostrarLista"
      class="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-xl border border-stone-200 bg-white py-1 shadow-lg"
    >
      <li v-for="item in sugestoes" :key="item.value">
        <button
          type="button"
          class="block w-full px-3.5 py-2 text-left text-sm text-stone-700 hover:bg-peach/20"
          @mousedown.prevent="selecionar(item)"
        >
          {{ item.label }}
        </button>
      </li>
    </ul>
  </div>
</template>
