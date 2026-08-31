# Dosificador de Concreto — Despliegue (Render + subdominio Hostinger)

App Flask (Python) que calcula dosificación de concreto, baldes, mortero, estribos,
metrado y exporta a Excel. Se sirve desde `web_app/app.py` y usa el motor
`dosificacion_concreto/`.

- **Dependencias:** Flask, openpyxl, gunicorn (ver `requirements.txt`). PySide6 va
  mockeado en `app.py`, NO se instala en el servidor.
- **Arranque en producción:** `gunicorn --chdir web_app --bind 0.0.0.0:$PORT app:app`
  (definido en `Procfile` y `render.yaml`).
- **Verificado en local:** `GET /`, `GET /api/opciones`, `POST /api/dosificar` → 200.

## Objetivo
`https://dosificador.constructor-ia.com` sirviendo esta app, con el subdominio
gestionado desde el DNS de Hostinger.

## Pasos

1. **Repo GitHub** — subir esta carpeta (`dosificador-web`) como repositorio propio
   (o como subcarpeta del monorepo, con Root Directory en Render).
2. **Render** — cuenta gratis → New → Web Service → conectar el repo.
   Render detecta `render.yaml`/`Procfile`. Plan **Free**. Deploy.
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn --chdir web_app --bind 0.0.0.0:$PORT app:app`
3. **Dominio en Render** — Settings → Custom Domains → `dosificador.constructor-ia.com`.
   Render entrega un destino CNAME.
4. **DNS en Hostinger** — Dominios → constructor-ia.com → DNS → añadir registro
   **CNAME** `dosificador` → (destino que dio Render). Esperar propagación + SSL.
5. **Enlace desde el sitio** — agregar un acceso al Dosificador en la web Next.js
   (Recursos/Herramientas o el campus). Va con el deploy normal a Vercel.

## Notas
- Plan Free de Render "duerme" tras inactividad (arranque en frío ~30 s en la
  primera visita). Suficiente para una herramienta interna; si se quiere siempre
  activa, subir a plan pago o usar un ping periódico.
- La exportación a Excel escribe temporales en memoria/`/tmp` (Render lo permite).
