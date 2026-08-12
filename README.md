# Carteira Financeira

Dashboard financeiro pessoal em Django: carteira de investimentos (ações B3 +
criptomoedas) com cotação quase em tempo real, controle de renda e despesas,
e gráficos de alocação/evolução mensal.

## Stack

- Backend: Django 4.2 + Django REST Framework (API pura, sem templates) —
  auth por sessão/cookie, não JWT
- Frontend: Vue 3 + Vite (`frontend/`), SPA separada que consome a API
- SQLite em desenvolvimento, Postgres em produção (via `DATABASE_URL`)
- Cotações: [brapi.dev](https://brapi.dev) (ações B3) e [CoinGecko](https://www.coingecko.com) (cripto), com cache de 60s

## Rodando localmente

Precisa de dois processos rodando ao mesmo tempo: a API Django e o dev
server do Vite (que faz proxy de `/api` pro Django — ver
`frontend/vite.config.js`).

```bash
# terminal 1 — backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # e preencha SECRET_KEY (veja instrução abaixo)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Acesse `http://localhost:5173/` (o front) e faça login com o superusuário
criado. O admin do Django continua em `http://127.0.0.1:8000/admin/`.

Antes de lançar despesas, cadastre categorias em `/admin/financas/categoriadespesa/`
(já vem com algumas padrão: Alimentação, Moradia, Transporte, Saúde, Lazer,
Educação, Outros).

Para ativos do tipo Criptomoeda, o campo "ID do CoinGecko" é obrigatório —
use o slug da moeda na CoinGecko (ex: `bitcoin`, `ethereum`), não o ticker.

## Cotações "em tempo real"

- **CoinGecko**: praticamente em tempo real, sem necessidade de chave.
- **brapi.dev**: pode ter alguns minutos de delay no plano gratuito e, dependendo
  do plano, pode exigir um token. Cadastre-se de graça em https://brapi.dev e
  coloque o token em `BRAPI_TOKEN` no `.env` se notar cotações faltando.

Se a API externa cair, o dashboard usa o último valor em cache (até 24h) em
vez de quebrar — nunca acontece erro 500 por causa disso.

## Deploy (100% grátis)

Desde a migração pro Vue (`frontend/`), o front e o back são deployados
separados:

| Peça | Onde | Grátis? |
|---|---|---|
| Front (`frontend/`, Vite build estático) | [Vercel](https://vercel.com) | sim, sem prazo de validade |
| Back (Django + DRF) | [Render](https://render.com) free web service | sim, mas "dorme" após 15min sem uso (~1min pra acordar) |
| Banco (Postgres) | [Neon](https://neon.tech) free tier | sim, sem prazo de validade (o Postgres free do Render expira em 30 dias) |

Front e back ficam em domínios de verdade diferentes (a Vercel não faz
proxy confiável de rota externa via `vercel.json` — tentamos, não
funcionou), então o front chama o back **direto** por URL absoluta
(`VITE_API_URL`), com `django-cors-headers` liberando a origem da Vercel e
cookie de sessão `SameSite=None; Secure` pra funcionar cross-site. O token
CSRF, que normalmente viria só do cookie, também vem no corpo de
`/api/auth/me/` (campo `csrfToken`) — JS de um domínio não lê cookie
setado por outro, então esse é o jeito do front saber o valor sem
precisar de cookie cross-domain (ver `frontend/src/lib/api.js` e
`core/api_views.py::MeAPIView`).

### 1. Banco (Neon)
Crie um projeto grátis em https://neon.tech e copie a *connection string*
(`postgres://...`) — vai virar a `DATABASE_URL` do passo 2.

### 2. Backend (Render)
1. Suba este repositório pro GitHub (se ainda não subiu).
2. No Render: **New → Blueprint**, aponte pro repo — ele lê o `render.yaml`
   da raiz e cria o Web Service sozinho (build já roda `collectstatic` +
   `migrate` a cada deploy).
3. Depois de criado, preencha as env vars marcadas `sync: false` no
   `render.yaml`: `DATABASE_URL` (do passo 1), `CSRF_TRUSTED_ORIGINS` e
   `CORS_ALLOWED_ORIGINS` (a URL da Vercel do passo 3, ex:
   `https://seu-app.vercel.app` — só dá pra preencher depois de ter essa
   URL), `BRAPI_TOKEN`/`COINGECKO_API_KEY` (opcionais).
4. Anote a URL gerada (ex: `https://carteira-financeira-api.onrender.com`)
   — se o nome do serviço vier diferente de `carteira-financeira-api`,
   ajuste também `ALLOWED_HOSTS` no Render.
5. Crie o superusuário: como o Render free não dá shell, rode localmente
   `DATABASE_URL=<a da Neon> python manage.py createsuperuser` (aponta
   direto pro banco de produção).

### 3. Frontend (Vercel)
1. Na Vercel: **New Project**, importe o mesmo repo.
2. Em "Root Directory", selecione `frontend`. Framework preset: Vite
   (build `npm run build`, output `dist` — detectado automaticamente).
3. Em **Environment Variables**, adiciona `VITE_API_URL` apontando pro
   backend do Render + `/api` (ex:
   `https://carteira-financeira-api.onrender.com/api`).
4. Deploy. Depois de ter a URL final (ex: `https://seu-app.vercel.app`),
   volta no Render e preenche `CSRF_TRUSTED_ORIGINS` **e**
   `CORS_ALLOWED_ORIGINS` com ela (passo 2.3), sem `/` no final.

**Atenção**: nunca use SQLite em produção — o disco do Render é efêmero e o
banco seria apagado a cada deploy/restart. Sempre configure `DATABASE_URL`
apontando pra um Postgres de verdade (Neon).
