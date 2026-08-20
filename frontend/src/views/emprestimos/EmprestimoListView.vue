<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, LoaderCircle } from '@lucide/vue'

const emprestimos = ref([])
const carregando = ref(true)
// `open` fica separado do item alvo — ver comentário em AtivoDetailView.vue
// sobre a corrida entre o fechamento automático do AlertDialogAction e o
// handler de confirmação.
const confirmExclusao = ref({ open: false, item: null })

async function carregar() {
  carregando.value = true
  emprestimos.value = await api.get('/emprestimos/')
  carregando.value = false
}

function pedirExclusao(e) {
  confirmExclusao.value = { open: true, item: e }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/emprestimos/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-stone-800">Empréstimos</h1>
      <RouterLink to="/emprestimos/novo" class="btn-primary">
        <Plus :size="16" /> Novo empréstimo
      </RouterLink>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[720px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Descrição</th>
            <th class="pb-2 font-medium">Sistema</th>
            <th class="pb-2 text-right font-medium">Valor total</th>
            <th class="pb-2 text-right font-medium">Saldo devedor</th>
            <th class="pb-2 text-right font-medium">Parcelas</th>
            <th class="pb-2 font-medium">Status</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in emprestimos" :key="e.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2 font-medium text-wine">
              <RouterLink :to="`/emprestimos/${e.id}`" class="hover:underline">{{ e.descricao }}</RouterLink>
            </td>
            <td class="py-2 text-stone-500">{{ e.sistema_amortizacao_display }}</td>
            <td class="py-2 text-right text-stone-700">{{ formatarMoeda(e.valor_total) }}</td>
            <td class="py-2 text-right font-medium" :class="e.quitado ? 'text-emerald-600' : 'text-stone-800'">
              {{ formatarMoeda(e.saldo_devedor) }}
            </td>
            <td class="py-2 text-right text-stone-700">{{ e.parcelas_pagas_count }}/{{ e.numero_parcelas }}</td>
            <td class="py-2">
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="e.quitado ? 'bg-emerald-100 text-emerald-700' : 'bg-peach/30 text-wine'">
                {{ e.quitado ? 'Quitado' : 'Em andamento' }}
              </span>
            </td>
            <td class="py-2 text-right">
              <RouterLink :to="`/emprestimos/${e.id}/editar`" class="text-xs font-medium text-stone-500 hover:text-wine">Editar</RouterLink>
              <button type="button" class="ml-3 text-xs font-medium text-red hover:underline" @click="pedirExclusao(e)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!emprestimos.length">
            <td colspan="7" class="py-10 text-center text-stone-400">Nenhum empréstimo cadastrado ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog
      v-model:open="confirmExclusao.open"
      :title="`Excluir ${confirmExclusao.item?.descricao}?`"
      description="As despesas já geradas pelas parcelas pagas não são apagadas."
      @confirm="confirmarExclusao"
    />
  </div>
</template>
