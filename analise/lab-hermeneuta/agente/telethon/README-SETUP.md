# Setup Telethon — passo a passo

## 1. Instalar Python (uma vez · ~5 min)

Abra **PowerShell como administrador** e cole:

```powershell
winget install Python.Python.3.12
```

Quando terminar, **feche e abra um terminal novo** (pra PATH atualizar). Verifique:

```powershell
python --version
```

Deve mostrar `Python 3.12.x`. Se mostrar a mensagem da Microsoft Store, instala via [python.org](https://www.python.org/downloads/) marcando "Add Python to PATH".

## 2. Instalar dependências (uma vez · ~30 seg)

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta\agente\telethon
pip install -r requirements.txt
```

## 3. Obter credenciais Telegram (uma vez · ~3 min)

1. Vai em [my.telegram.org/apps](https://my.telegram.org/apps)
2. Loga com seu telefone (o mesmo do app Telegram)
3. Telegram manda código no app → cola aqui
4. **Create new application:**
   - App title: `Monofloor Hermeneuta`
   - Short name: `monofloor`
   - Platform: `Desktop`
   - Description: `Análise interna de grupos de obra`
5. Clica **Create application**
6. Anota os 2 valores:
   - `App api_id` (número de 7 dígitos)
   - `App api_hash` (string longa hexadecimal)

⚠️ **Esses valores são pessoais.** Não compartilha com ninguém. NUNCA commita no git.

## 4. Configurar `.env` local

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta\agente\telethon
copy .env.example .env
notepad .env
```

Preenche os 3 valores:

```
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=abc123def456...
TELEGRAM_PHONE=+5511999999999
```

Salva e fecha.

## 5. Rodar Fase A — listar grupos

```powershell
python listar_grupos.py
```

Primeira execução vai pedir:

1. **"Please enter your phone..."** → já tá no `.env`, mas se pedir, digita o número com `+55` e DDD
2. **"Please enter the code you received:"** → Telegram manda código de 6 dígitos no APP. Digita aqui (sem espaço)
3. **"Please enter your password:"** (só se você tiver 2FA) → digita a senha 2FA

Depois disso roda em ~30s a 2 minutos (depende da quantidade de grupos).

## 6. Conferir saída

Termina criando 2 arquivos:

- `grupos.csv` → abre no Excel/Notepad · ordenado por mensagem mais recente
- `grupos.json` → mesmo conteúdo em JSON

Cada linha tem: `id · nome · tipo · membros · última mensagem (data) · dias inativo · preview da última mensagem (80 chars)`

## 7. Você revisa, marca os de obra

Abre `grupos.csv`. Vai ver 300-400 linhas. Os ativos vão estar no topo (ordenado por data desc). Identifique:

- ✅ Grupos de obra que quer monitorar
- ❌ Zumbis antigos (>180 dias inativos) que NÃO interessam
- ❌ Grupos pessoais / família / outros assuntos

Sugestão: cria coluna nova `monitorar` no Excel e marca `s` ou `n`. Salva como `grupos-marcados.csv`.

## 8. Próximo passo (Fase B — só depois da revisão)

Quando você tiver `grupos-marcados.csv` com as obras selecionadas, eu monto:
- `monitorar.py` — rodar diariamente · pega últimas N mensagens dos grupos marcados · gera `telegram-snapshot.json`
- HERMENEUTA passa a ler esse JSON como fonte primária · KIRA vira backup

---

## Troubleshooting

**"FloodWaitError" ao logar:** Telegram limita login frequente. Espera 5 min e tenta de novo.

**"PhoneCodeInvalid":** o código do app expira em ~2 min. Pede outro reenviando.

**"SessionPasswordNeeded":** sua conta tem 2FA. Coloca senha quando pedir.

**Script trava em "Coletando diálogos":** normal · com 400 grupos pode demorar 1-2 min na primeira vez. Telethon faz cache.

**Script falha com "PYTHON_NOT_FOUND" mesmo após winget:** abre terminal novo. Se persiste, reinicia o Windows.
