# Bitácora — /.github

## 2026-07-04 · Automatización externa
- **Qué:** `workflows/actualizar-tablero.yml` — corre el batch EOD en GitHub Actions (cron 22:00 UTC hábiles + manual + push), commitea `ui/data.json`/`ui/data.js` y publica `ui/` en GitHub Pages.
- **Por qué:** Franco quería actualización automática fuera de Claude y de su PC. GitHub lo corre en la nube sin costo ni API keys.
- **Decisiones:** 22:00 UTC cubre el cierre US todo el año (evita el borde de DST). Deploy vía Pages con `deploy-pages@v4` (requiere Source: GitHub Actions en Settings).
- **Falta:** activación manual una vez (push + habilitar Pages + permisos de escritura).
