# LinguaBot 2.0 🤖🌍

Bot de **aprendizagem de idiomas no Telegram**, para **adultos e crianças**,
feito para funcionar com **custo zero** (bibliotecas e serviços gratuitos e de
código aberto). O bot **não é** um site: ele vive dentro do Telegram.

> ⚠️ Projeto educativo/informativo. Não é uma certificação oficial de
> proficiência (A1–C1 são usados apenas como referência aproximada).

---

## ✨ O que o bot faz

- **Configuração guiada** (`/start`): idioma da **interface** → idioma a
  **aprender** → nível → voz (feminina/masculina) → perfil (adulto/infantil) →
  modalidade → objetivo. O idioma da interface é **separado** do idioma estudado.
- **Retoma de onde parou**: ao voltar com `/start`, o bot oferece *continuar*,
  *recomeçar* (sem apagar o histórico) ou *ver progresso*.
- **Módulos**:
  - 💬 **Conversação livre** (texto e voz) com correção.
  - 🗣️ **Pronúncia**: ouça a referência, envie um áudio e receba feedback.
  - 📖 **Gramática**: lições com explicação, exemplos e exercícios.
  - 🖼️ **Imagens**: aprendizagem visual com áudio.
  - 🧒 **Modo infantil**: atividades curtas, seguro e com reforço positivo.
  - 📝 **Exercícios/Avaliações** com pontuação e histórico.
- **Persistência em SQLite** (com migrações versionadas).
- **Privacidade**: ver (`/meusdados`) e apagar (`/apagar`) todos os dados.
  Áudios de voz são processados e **descartados**.

### Comandos

| Comando | Função |
|---|---|
| `/start` | Iniciar, retomar ou recomeçar |
| `/menu` | Menu principal |
| `/ajuda` | Ajuda |
| `/progresso` | Painel de progresso |
| `/config` | Alterar idioma, nível, voz, etc. |
| `/privacidade` | Como tratamos seus dados |
| `/meusdados` | Ver os dados guardados |
| `/apagar` | Apagar todos os dados |

---

## 🏗️ Arquitetura

```
linguabot/
├── config.py            # configuração via variáveis de ambiente
├── models.py            # enums e estruturas de domínio
├── container.py         # contêiner de serviços + fábrica de dependências
├── content/             # idiomas, vocabulário e gramática (conteúdo)
├── storage/             # SQLite + migrações + repositórios
├── services/            # áudio, imagens, LLM, STT, TTS, tutor
├── bot/                 # aplicação, teclados, textos e handlers
└── health.py            # servidor HTTP de saúde (opcional)
```

Os motores de IA são **plugáveis** e **opcionais**:

| Recurso | Opções | Padrão (custo zero) |
|---|---|---|
| LLM (conversação) | `none` (regras), `gemini`, `ollama` | `none` |
| Fala → texto (STT) | `vosk` (local), `gemini`, `none` | `vosk` |
| Texto → voz (TTS) | `edge` (sem chave), `gtts`, `piper` | `edge` |

Se um motor falhar ou não estiver instalado, o bot **cai para uma alternativa
gratuita** e avisa o usuário — nunca finge ter reconhecido ou gerado algo.

---

## 🚀 Como rodar

### 1. Requisitos

- Python 3.10+ (testado em 3.14 no Windows).
- Um token de bot do Telegram (gratuito, via [@BotFather](https://t.me/BotFather)).

### 2. Instalação

```bash
git clone <url-do-repositorio>
cd Linguabot-bot
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuração

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Edite o `.env` e preencha **apenas** o `BOT_TOKEN`. Todo o resto é opcional.

### 4. Diagnóstico (recomendado)

```bash
python -m linguabot --diagnose
```

Mostra o que está instalado, a configuração atual e avisos.

### 5. (Opcional) Modelos de voz para STT local

```bash
python scripts/download_vosk_models.py en es    # baixa modelos Vosk gratuitos
```

### 6. Executar

```bash
python -m linguabot          # ou: python bot.py
```

---

## ⚙️ Variáveis de ambiente

Todas são lidas de `.env` (nunca faça commit do `.env`). Veja `.env.example`.

| Variável | Padrão | Descrição |
|---|---|---|
| `BOT_TOKEN` | — | **Obrigatório.** Token do @BotFather. |
| `DATABASE_PATH` | `./data/linguabot.db` | Arquivo SQLite. |
| `DEFAULT_UI_LANG` | `pt` | Idioma da interface (`pt`, `en`, `es`). |
| `LLM_PROVIDER` | `none` | `none`, `gemini` ou `ollama`. |
| `GEMINI_API_KEY` | — | Necessário para `gemini`. |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | — | Para `ollama` (LLM local). |
| `STT_PROVIDER` | `vosk` | `vosk`, `gemini` ou `none`. |
| `VOSK_MODELS_DIR` | `./models/vosk` | Onde ficam os modelos Vosk. |
| `TTS_PROVIDER` | `edge` | `edge`, `gtts` ou `piper`. |
| `RATE_LIMIT_PER_MINUTE` | `30` | Antiflood por usuário. |
| `KIDS_MODE_ENABLED` | `true` | Liga/desliga o modo infantil. |
| `HEALTH_ENABLED` / `PORT` | `false` / `10000` | Servidor HTTP de saúde. |

---

## 🧪 Testes

```bash
python -m pytest
```

A suíte cobre configuração, banco/migrações, repositórios, conteúdo,
pronúncia, tutor, áudio (com ffmpeg embutido), TTS/STT, imagens e os fluxos do
bot (onboarding, gramática, avaliação, conversação, modo infantil,
privacidade e antiflood) usando objetos falsos — **sem** acessar o Telegram.

---

## ☁️ Publicação (opções gratuitas)

- **Long polling** em qualquer máquina ligada 24h (PC, Raspberry Pi, etc.).
- **Web Service gratuito** (ex.: Render): o bot usa long polling; o servidor de
  saúde é ativado com `HEALTH_ENABLED=true`. Atenção: planos gratuitos podem
  **hibernar**; para operação contínua, prefira um processo *worker* ou uma
  máquina sempre ligada.

> O `HEALTH_ENABLED` apenas expõe `/health`; ele **não substitui** o bot.

---

## 🔐 Privacidade e crianças

- Guardamos só o necessário: idioma, nível, preferências, progresso e histórico
  de avaliações.
- Áudios de voz são **temporários** e descartados após o uso.
- O modo infantil **não pede dados pessoais**, exige consentimento de um
  responsável e usa **imagens curadas ou geradas localmente** (nunca busca
  externa aleatória).
- Conformidade com LGPD/ECA **não foi certificada**; o bot adota boas práticas
  de minimização de dados e controle do usuário, mas isso não constitui
  garantia legal.

---

## ⚠️ Limitações conhecidas (honestas)

- A **avaliação de pronúncia** compara o **texto reconhecido** com o esperado;
  **não** mede fonemas nem entonação.
- A **correção offline** (sem LLM) é limitada a regras simples e explícitas.
- O TTS **gTTS** não permite escolher o gênero da voz (use `edge` para isso).
- Cobertura de **gramática**: inglês e espanhol; vocabulário básico para
  francês, alemão e italiano.
- Imagens do Wikimedia Commons podem variar em qualidade; para crianças,
  prefira assets curados em `assets/images/`.

---

## 📦 Migração da versão anterior

A versão 1.x era um único arquivo (`bot.py`) com Flask, banco **em memória**
(perdia tudo ao reiniciar), `from gTTS import gTTS` (import quebrado em
Linux) e suporte apenas a inglês. Esta versão reescreve o projeto de forma
modular, com **persistência real**, **fallbacks gratuitos** e testes.

## 📄 Licença

Distribuído para uso educacional. Verifique as licenças das dependências e das
mídias do Wikimedia Commons antes de reutilizar publicamente.
