# Instale as dependências registradas no arquivo 'requirements.txt'
pip3 install -r requirements.txt

# Inspeciona rapidamente o serviço MCP
fastmcp inspect ferramentas.py

# Executando o inspetor visual (web) de ferramentas
npx @modelcontextprotocol/inspector

# Crie um arquivo .env e informe um valor para GOOGLE_API_KEY (chave de acesso a modelos de IA da google)
https://aistudio.google.com/api-keys

# Executar o sistema
## Primeiro execute: 
python3 ferramentas.py
## Depois: 
python3 chat.py

