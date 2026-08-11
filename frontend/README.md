# Carteira Financeira — front (Vue)

Front novo, em construção fase a fase (ver `/Users/comercial-salareuniao/.claude/plans/dazzling-squishing-hinton.md`
pro plano da fase atual). Substitui gradualmente os templates Django em
`../templates/`, `../core/templates/`, etc. — que continuam funcionando
normalmente enquanto essa migração acontece.

**Stack**: Vite + Vue 3 (`<script setup>`) + Vue Router + Pinia + Tailwind CSS v4
+ [reka-ui](https://reka-ui.com) (componentes headless) + `@lucide/vue` (ícones)
+ `vue-chartjs` (mesmos gráficos Chart.js do dashboard antigo).

**Paleta** (`src/assets/main.css`, bloco `@theme`): `sand` `#c0b19e`,
`peach` `#ffb48f`, `coral` `#f68b7b`, `red` `#f6464a`, `wine` `#911440`.

## Rodando em desenvolvimento

Precisa dos **dois** servidores rodando ao mesmo tempo:

```bash
# Terminal 1 — backend (raiz do projeto)
cd ..
source venv/bin/activate
python manage.py runserver          # :8000

# Terminal 2 — frontend
cd frontend
npm install                          # só na 1ª vez
npm run dev                          # :5173
```

Acesse **http://localhost:5173** (não o :8000 — esse continua servindo o
app antigo em templates). O Vite faz proxy de `/api/*` pro Django, então
cookie de sessão/CSRF funcionam sem CORS. Login: mesmo usuário/senha do
app Django (é a mesma sessão).

## Autenticação

Sessão Django (`SessionAuthentication` do DRF), não JWT — mesmo
`django.contrib.auth` de sempre. `src/lib/api.js` cuida de mandar o cookie
(`credentials: 'include'`) e o header CSRF em toda request que muda estado.

## Build de produção

Ainda não usado — a Fase 1 só cobre desenvolvimento local. Quando todas as
páginas estiverem portadas, `npm run build` gera `dist/`, e o Django passa
a servir esses arquivos estáticos direto (fim do proxy do Vite).
