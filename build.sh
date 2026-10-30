#!/usr/bin/env bash

set -e

# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"

# Instalar dependencias
make install

# Crear las tablas de la base de datos
psql -v ON_ERROR_STOP=1 -d "$DATABASE_URL" -f database.sql
