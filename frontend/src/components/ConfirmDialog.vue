<script setup>
import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogRoot,
  AlertDialogTitle,
} from 'reka-ui'

const open = defineModel('open', { type: Boolean, default: false })
defineProps({
  title: { type: String, default: 'Tem certeza?' },
  description: { type: String, default: 'Essa ação não pode ser desfeita.' },
  confirmLabel: { type: String, default: 'Excluir' },
})
const emit = defineEmits(['confirm'])
</script>

<template>
  <AlertDialogRoot v-model:open="open">
    <AlertDialogPortal>
      <AlertDialogOverlay class="fixed inset-0 z-40 bg-stone-900/40" />
      <AlertDialogContent
        class="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-6 shadow-xl focus:outline-none"
      >
        <AlertDialogTitle class="text-lg font-bold text-stone-800">{{ title }}</AlertDialogTitle>
        <AlertDialogDescription class="mt-2 text-sm text-stone-500">{{ description }}</AlertDialogDescription>

        <div class="mt-6 flex justify-end gap-2">
          <AlertDialogCancel class="btn-secondary">Cancelar</AlertDialogCancel>
          <AlertDialogAction class="btn-primary bg-red hover:bg-red/90" @click="emit('confirm')">
            {{ confirmLabel }}
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>
