<script setup>
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'
import { X } from '@lucide/vue'

const open = defineModel('open', { type: Boolean, default: false })
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-40 bg-stone-900/40 data-[state=open]:animate-in data-[state=open]:fade-in data-[state=closed]:animate-out data-[state=closed]:fade-out" />
      <DialogContent
        class="fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-6 shadow-xl focus:outline-none"
      >
        <div class="mb-4 flex items-start justify-between">
          <div>
            <DialogTitle class="text-lg font-bold text-stone-800">{{ title }}</DialogTitle>
            <DialogDescription v-if="description" class="mt-1 text-sm text-stone-500">
              {{ description }}
            </DialogDescription>
          </div>
          <DialogClose class="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-600">
            <X :size="18" />
          </DialogClose>
        </div>

        <slot />
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
