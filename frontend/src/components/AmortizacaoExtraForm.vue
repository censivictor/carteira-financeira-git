<script setup>
import { ref } from 'vue'
import { api } from '@/lib/api'
import { formatarMoeda } from '@/lib/format'
import { LoaderCircle } from '@lucide/vue'

const props = defineProps({ emprestimo: { type: Object, required: true } })
const emit = defineEmits(['done'])

const valorExtra = ref('')
const modo = ref('PRAZO')
const erros = ref({})
const salvando = ref(false)

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    await api.post(`/emprestimos/${props.emprestimo.id}/amortizar/`, {
      valor_extra: valorExtra.value,
      modo: modo.value,
    })
    emit('done')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="salvar">
    <p class="text-sm text-stone-500">
      Saldo devedor atual: <strong class="text-stone-700">{{ formatarMoeda(emprestimo.saldo_devedor) }}</strong>
    </p>

    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor a abater (R$)</label>
      <input v-model="valorExtra" type="number" step="any" min="0.01" class="input" required />
      <p v-if="erros.valor_extra" class="mt-1 text-xs text-red">{{ erros.valor_extra[0] }}</p>
    </div>

    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">O que fazer com a diferença?</label>
      <div class="space-y-2">
        <label class="flex items-start gap-2 rounded-lg border border-stone-200 p-3 text-sm has-[:checked]:border-wine has-[:checked]:bg-peach/10">
          <input v-model="modo" type="radio" value="PRAZO" class="mt-0.5 h-4 w-4 text-wine focus:ring-wine/40" />
          <span>
            <strong class="text-stone-700">Reduzir prazo</strong>
            <span class="block text-xs text-stone-400">Mantém o valor da parcela e quita mais rápido — economiza mais juros.</span>
          </span>
        </label>
        <label class="flex items-start gap-2 rounded-lg border border-stone-200 p-3 text-sm has-[:checked]:border-wine has-[:checked]:bg-peach/10">
          <input v-model="modo" type="radio" value="PARCELA" class="mt-0.5 h-4 w-4 text-wine focus:ring-wine/40" />
          <span>
            <strong class="text-stone-700">Reduzir parcela</strong>
            <span class="block text-xs text-stone-400">Mantém a mesma quantidade de parcelas, cada uma fica menor.</span>
          </span>
        </label>
      </div>
      <p v-if="erros.modo" class="mt-1 text-xs text-red">{{ erros.modo[0] }}</p>
    </div>

    <p v-if="erros.detail" class="text-xs text-red">{{ erros.detail }}</p>

    <button type="submit" class="btn-primary w-full" :disabled="salvando">
      <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
      Abater
    </button>
  </form>
</template>
