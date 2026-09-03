#!/usr/bin/env bash
# Empacota cada skills/<nome>/ em dist/<nome>.zip, pronto para subir em
# Copilot Studio -> Skills -> Adicionar skill -> Carregar arquivo.
#
# O zip contem SKILL.md na raiz + a pasta references/ (se existir).
# Use sempre o .zip em vez do .md solto: so o zip carrega os references/.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v zip >/dev/null 2>&1 || { echo "ERRO: 'zip' nao instalado. Rode: sudo apt-get install zip"; exit 1; }

echo "Validando antes de empacotar..."
./scripts/validate-skills.sh || { echo; echo "Empacotamento abortado: corrija os erros acima."; exit 1; }

rm -rf dist && mkdir -p dist
echo

for dir in skills/*/; do
  nome="$(basename "$dir")"
  ( cd "$dir" && zip -q -r "../../dist/${nome}.zip" SKILL.md $([ -d references ] && echo references) )
  tamanho="$(du -h "dist/${nome}.zip" | cut -f1)"
  n_arquivos="$(unzip -l "dist/${nome}.zip" | tail -1 | awk '{print $2}')"
  printf '  dist/%-26s %5s  (%s arquivos)\n' "${nome}.zip" "$tamanho" "$n_arquivos"
done

echo
echo "Pronto. Suba cada .zip em Copilot Studio -> Skills -> Adicionar skill -> Carregar arquivo."
echo "Ordem sugerida (ver docs/04-passo-a-passo.md):"
echo "  1. inicio-de-conversa   2. portfolio-overview   3. project-deep-dive"
echo "  4. meeting-preparation  5. update-devops        6. notificar-gestor"
echo "  7. consumer-martech (Consumer BPC / B&W MarTech — mundo Excel, independente)"
