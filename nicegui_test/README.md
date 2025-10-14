# Cria o projeto completo

uv init nome_do_projeto

# Para inicializar o projeto com uma versão específica do python (caso não seja especificada a versão, será usada a versão global definida com o `uv python pin --global`)

uv init nome_do_projeto --python=3.12.3

# Ou inicializa dentro de um projeto existente que não tenha o arquivo `pyproject.toml`:

uv init

# Para um projeto que já tenha o arquivo `pyproject.toml` e não tenha ainda o arquivo `uv.lock` é importante executar o comando abaixo, caso contrário nenhuma dependência será adicionada ao `.env`

uv pip compile

# Caso queira instalar também as dependências opcionais de dev e docs executar (porém acho melhor usar o `uv tool install` para instalar globalmente ao invés de instalar no `.env` do projeto):

uv pip compile --extra dev --extra docs

# Para syncronizar projetos que já possuam o arquivo `pyproject.toml`. Instala Python, cria venv e instala dependências:

uv sync

# Instala pacotes

uv add pyside6==6.6.0 yt-dlp requests

# Remove pacotes

uv remove requests

# Instala ferramentas como ruff ou pyright globalmente

uv tool install ruff pytest pyrightcls

# Para desistalar uma tool

uv tool uninstall ruff

# Caso queira apenas executar a tool sem instalá-la

uvx ruff

# NiceGUI

https://nicegui.io/documentation/aggrid
