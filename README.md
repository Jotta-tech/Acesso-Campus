# Acesso Campus

Sistema web para registrar e acompanhar barreiras de acessibilidade dentro de uma universidade, como uma rampa bloqueada ou um elevador indisponível. Qualquer pessoa pode abrir um relato e consultar os que já existem; usuários autorizados definem a prioridade e atualizam a situação de cada um.

Foi desenvolvido em equipe, durante um hackathon acadêmico, e é um protótipo para execução local: usa SQLite e não tem configuração de implantação.

## Funcionalidades

- **Registro de ocorrências sem login.** O relato leva título, descrição, categoria e localização (bloco, andar ou local específico). Ele entra como `pendente` e com prioridade `media`; quem registra não escolhe esses dois campos.
- **Lista com busca e filtros.** Pesquisa por título e descrição, filtros por status, prioridade e categoria, 10 ocorrências por página e uma tela de detalhes para cada relato.
- **Painel.** Total de ocorrências e distribuição por status e prioridade.
- **Área de administração.** Login e logout; usuários com permissão de gestão alteram o status e a prioridade na tela de detalhes.
- **API REST** usada pelo front-end, com limite de criações por IP anônimo (padrão: 60 por hora).

As categorias são: rampa bloqueada ou inadequada, elevador ou plataforma indisponível, corredor obstruído, banheiro acessível, sinalização ausente ou inadequada, acessibilidade digital e outras dificuldades de acesso.

## Tecnologias

| Camada | Tecnologias |
| --- | --- |
| Front-end | React 19, Vite 8, JavaScript (JSX) e CSS |
| Back-end | Python, Django 5.2, Django REST Framework, django-filter e python-dotenv |
| Banco de dados | SQLite |

## Pré-requisitos

- Git
- Python 3.11 ou superior, com `pip` (mínimo exigido pelo django-filter 26.2)
- Node.js 20.19+, 22.13+ ou 24+, com `npm` (mínimo exigido pelo Vite 8 e pelo ESLint 10)

## Instalação e execução

O back-end (Django) e o front-end (React) rodam em processos separados, então você vai precisar de dois terminais.

### 1. Baixar o projeto

```bash
git clone https://github.com/Jotta-tech/Acesso-Campus.git
cd Acesso-Campus
```

### 2. Back-end

Na raiz do projeto, crie e ative um ambiente virtual.

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o arquivo `.env` a partir do exemplo:

```bash
# Linux/macOS
cp .env.example .env
```

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

Abra o `.env` e troque `SECRET_KEY` por uma chave aleatória. Para gerar uma:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Mantenha `DEBUG=True` apenas em ambiente local e não envie o `.env` ao GitHub (ele já está no `.gitignore`).

Crie o banco e inicie o servidor:

```bash
python manage.py migrate
python manage.py runserver
```

O servidor sobe em `http://127.0.0.1:8000/`. A rota raiz não tem página (responde 404); a API fica em `/api/` e o Django Admin em `/admin/`.

### 3. Front-end

Em outro terminal, a partir da raiz do projeto:

```bash
cd front-end
npm install
npm run dev
```

Abra o endereço que o Vite mostrar no terminal (por padrão, `http://localhost:5173/`). Em desenvolvimento, o Vite encaminha as chamadas de `/api` para o Django em `http://127.0.0.1:8000` (veja `front-end/vite.config.js`), por isso os dois servidores precisam ficar ligados.

### 4. Criar um usuário administrador (opcional)

Na raiz, com o ambiente virtual ativado:

```bash
python manage.py createsuperuser
```

Depois, entre em **Administração** na interface ou acesse `http://127.0.0.1:8000/admin/`.

Ao final do `migrate`, o projeto cria o grupo **Gestores**, com permissão para editar e excluir ocorrências. Usuários que não são superusuários precisam estar nesse grupo (ou ter a permissão `change_ocorrencia`) para gerenciar ocorrências.

## Configuração

As variáveis ficam no arquivo `.env` da raiz e são lidas por `config/settings.py`.

| Variável | Função | Valor em `.env.example` |
| --- | --- | --- |
| `SECRET_KEY` | Chave secreta do Django. Obrigatória quando `DEBUG` não é `True`. | valor de exemplo; troque |
| `DEBUG` | Modo de depuração. Se a variável não existir, o padrão é `False`. | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por vírgula. | `127.0.0.1,localhost` |
| `THROTTLE_CRIACAO_ANONIMA` | Limite de ocorrências criadas por IP anônimo, no formato `número/período` (`second`, `minute`, `hour` ou `day`). | `60/hour` |

As origens confiáveis para CSRF (`CSRF_TRUSTED_ORIGINS`, em `config/settings.py`) são `http://localhost:5173` e `http://127.0.0.1:5173`. Se o Vite usar outra porta, inclua-a nessa lista.

## Como usar a interface

1. Em **Visão geral**, clique em **Registrar ocorrência**, preencha o formulário e envie.
2. Em **Ocorrências recentes**, pesquise, filtre e abra **Ver detalhes** para ler o relato completo.
3. Para gerenciar, abra **Administração** no menu lateral e entre com um usuário autorizado. Na tela de detalhes, **Gerenciar ocorrência** permite trocar status e prioridade; confirme em **Salvar alterações**.

## API

A API fica sob `/api/`. Leitura e criação de ocorrências são públicas; as demais operações exigem um usuário com permissão, autenticado por sessão do Django ou por Basic Auth.

### Ocorrências e painel

| Método | Rota | Finalidade | Acesso |
| --- | --- | --- | --- |
| `GET` | `/api/dashboard/` | Total e contagens por status, categoria e prioridade | Público |
| `GET` | `/api/ocorrencias/` | Lista paginada (10 por página) | Público |
| `POST` | `/api/ocorrencias/` | Registra uma ocorrência | Público, com limite por IP |
| `GET` | `/api/ocorrencias/{id}/` | Consulta uma ocorrência | Público |
| `PUT`, `PATCH` | `/api/ocorrencias/{id}/` | Edita uma ocorrência | Gestor |
| `PATCH` | `/api/ocorrencias/{id}/status/` | Altera somente o status | Gestor |
| `DELETE` | `/api/ocorrencias/{id}/` | Exclui uma ocorrência | Gestor com permissão de exclusão |

**Listagem.** Parâmetros aceitos: `search` (título e descrição), `categoria`, `status`, `prioridade`, `localizacao` (contém o texto, sem diferenciar maiúsculas) e `page`. Valores inválidos nos filtros retornam 400.

**Criação.** Só são aceitos `titulo` (5 a 120 caracteres), `descricao` (10 a 2000), `categoria` e `localizacao` (3 a 150). Se `status` ou `prioridade` forem enviados nessa rota, são ignorados.

| Campo | Valores |
| --- | --- |
| `categoria` | `rampa`, `elevador`, `corredor`, `banheiro`, `sinalizacao`, `digital`, `outros` |
| `prioridade` | `baixa`, `media` (padrão), `alta` |
| `status` | `pendente` (padrão), `em_andamento`, `resolvida` |

### Área de administração (usada pelo front-end)

Estas rotas trabalham com sessão e proteção CSRF: o front-end obtém o cookie em `/api/acesso-admin/csrf/` e envia o valor no cabeçalho `X-CSRFToken`.

| Método | Rota | Finalidade |
| --- | --- | --- |
| `GET` | `/api/acesso-admin/csrf/` | Define o cookie CSRF |
| `GET` | `/api/acesso-admin/session/` | Informa se há sessão ativa e se o usuário pode gerenciar |
| `POST` | `/api/acesso-admin/login/` | Inicia a sessão (`username` e `password`); responde 403 se as credenciais forem inválidas ou o usuário não puder gerenciar |
| `POST` | `/api/acesso-admin/logout/` | Encerra a sessão |
| `PATCH` | `/api/acesso-admin/ocorrencias/{id}/` | Altera `status` e/ou `prioridade` |

### Exemplos

Os comandos abaixo usam `curl` em bash, com o back-end rodando em `127.0.0.1:8000`.

Registrar uma ocorrência (sem login):

```bash
curl -X POST http://127.0.0.1:8000/api/ocorrencias/ \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Rampa bloqueada na entrada", "descricao": "A rampa do bloco A está bloqueada por bicicletas.", "categoria": "rampa", "localizacao": "Bloco A, entrada principal"}'
```

Listar rampas pendentes:

```bash
curl "http://127.0.0.1:8000/api/ocorrencias/?categoria=rampa&status=pendente"
```

Alterar o status com um usuário que tenha permissão de gestão (troque `1` pelo id da ocorrência). Basic Auth só deve ser usado em ambiente local ou com HTTPS:

```bash
curl -u SEU_USUARIO:SUA_SENHA -X PATCH http://127.0.0.1:8000/api/ocorrencias/1/status/ \
  -H "Content-Type: application/json" \
  -d '{"status": "em_andamento"}'
```

## Testes

```bash
python manage.py test
```

Execute na raiz, com o ambiente virtual ativado e o `.env` criado. Os testes cobrem a API: criação, leitura, filtros, alteração de status, permissões, painel e limite de criação anônima. O front-end não tem testes automatizados.

## Estrutura do projeto

```text
Acesso-Campus/
├── config/             # Configurações, rotas principais e login da área de administração
├── front-end/          # Aplicação React + Vite
│   ├── src/
│   │   ├── App.jsx     # Tela principal: painel, formulário, lista, detalhes e administração
│   │   ├── api.js      # Chamadas à API
│   │   └── components/ # Componentes de interface
│   └── vite.config.js  # Proxy de /api para o Django
├── ocorrencias/        # App Django: modelo, serializers, filtros, permissões, views e testes
├── .env.example        # Modelo de variáveis de ambiente
├── manage.py
└── requirements.txt    # Dependências Python
```

## Limitações conhecidas

- A API calcula a contagem por categoria (`por_categoria`), mas o painel da interface ainda não a exibe.
- Pela interface é possível registrar ocorrências e alterar status e prioridade. Editar os demais campos e excluir ocorrências só é possível pela API ou pelo Django Admin.
- O projeto usa SQLite e foi preparado para execução local. Publicá-lo exige definir hospedagem, banco de dados e configurações de segurança (`DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS` e origens CSRF).

## Equipe

4° SEMESTRE CIÊNCIA DA COMPUTAÇÃO
Sabrina Maués da Silva - 04181448 - codewith-sabrina (github)
João Pedro dos Santos Maciel - 04179247 - Jotta-tech (github)
