# Carteira Financeira

Dashboard financeiro pessoal em Django: carteira de investimentos (ações B3 +
criptomoedas) com cotação quase em tempo real, controle de renda e despesas,
e gráficos de alocação/evolução mensal.

## Stack

- Django 4.2 (server-rendered, sem SPA/Node) + Chart.js via CDN
- SQLite em desenvolvimento, Postgres em produção (via `DATABASE_URL`)
- Cotações: [brapi.dev](https://brapi.dev) (ações B3) e [CoinGecko](https://www.coingecko.com) (cripto), com cache de 60s

## Rodando localmente

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # e preencha SECRET_KEY (veja instrução abaixo)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` e faça login com o superusuário criado.

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

## Deploy

Recomendação: [Render](https://render.com) (free web service + Postgres free
por 90 dias) pra começar. Alternativa sem "sleep": Railway (~US$5/mês).

Passos gerais (Render):
1. Suba este repositório pro GitHub.
2. No Render, crie um **Web Service** apontando pro repo — ele detecta o
   `Procfile` automaticamente (build: `pip install -r requirements.txt`).
3. Crie um banco **Postgres** no Render e copie a `DATABASE_URL` gerada.
4. Nas env vars do Web Service, configure: `SECRET_KEY` (gere uma nova, não
   reuse a de dev), `DEBUG=False`, `ALLOWED_HOSTS=<seu-app>.onrender.com`,
   `DATABASE_URL=<a do passo 3>`, `BRAPI_TOKEN` (opcional).
5. Deploy. O `release: python manage.py migrate` do `Procfile` roda as
   migrations automaticamente a cada deploy.
6. Crie o superusuário em produção via shell do Render:
   `python manage.py createsuperuser`.

**Atenção**: nunca use SQLite em produção nessas plataformas — o disco é
efêmero e o banco seria apagado a cada deploy/restart. Sempre configure
`DATABASE_URL` apontando pra um Postgres de verdade em produção.
