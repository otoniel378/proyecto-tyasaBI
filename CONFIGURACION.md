# TYASA BI — Guía de Configuración para Nuevos Colaboradores

## Requisitos previos

- Python 3.10 o superior
- Git instalado
- Acceso al repositorio en GitHub

---

## 1. Clonar el repositorio e instalar dependencias

```bash
git clone <URL-del-repositorio>
cd proyecto-tyasaBI
pip install -r requirements.txt
```

---

## 2. Obtener las credenciales de Google Cloud

Pide a **otoniel378** que te agregue a GCP con los permisos necesarios.  
Una vez que te confirme el acceso, sigue estos pasos:

1. Abre [GCP Console → IAM y administración → Cuentas de servicio](https://console.cloud.google.com/iam-admin/serviceaccounts?project=project-d0cf2519-d089-47d3-930)
2. Haz clic en la cuenta de servicio del proyecto (termina en `...iam.gserviceaccount.com`)
3. Ve a la pestaña **Claves** → **Agregar clave** → **Crear clave nueva** → formato **JSON**
4. Descarga el archivo JSON — guárdalo en un lugar seguro

> ⚠️ **Nunca compartas este archivo ni lo subas a git.**

---

## 3. Crear el archivo secrets.toml

1. Copia la plantilla:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
2. Abre `.streamlit/secrets.toml` con cualquier editor de texto
3. Rellena la sección `[gcp_service_account]` con el contenido del JSON descargado:

   | Campo en secrets.toml       | Campo en el JSON descargado       |
   |-----------------------------|-----------------------------------|
   | `private_key_id`            | `private_key_id`                  |
   | `private_key`               | `private_key` (incluye `\n`)      |
   | `client_email`              | `client_email`                    |
   | `client_id`                 | `client_id`                       |
   | `client_x509_cert_url`      | `client_x509_cert_url`            |

   Los demás campos (`type`, `project_id`, `auth_uri`, `token_uri`, `auth_provider_x509_cert_url`) ya están rellenados en la plantilla — no los cambies.

4. Asegúrate de que la `GEMINI_API_KEY` esté configurada. Pídela a otoniel378 si no la tienes.

---

## 4. Verificar la configuración

Ejecuta el script de verificación para confirmar que todo está correcto:

```bash
python scripts/check_setup.py
```

Deberías ver:
```
✓ secrets.toml encontrado
✓ GEMINI_API_KEY presente
✓ gcp_service_account presente
✓ Conexión a BigQuery exitosa — proyecto: project-d0cf2519-d089-47d3-930
✓ Todo listo. Puedes correr: streamlit run app.py
```

---

## 5. Correr la aplicación

```bash
streamlit run app.py
```

La app abrirá automáticamente en tu navegador en `http://localhost:8501`.

---

## Resolución de problemas

### Error: `DefaultCredentialsError` o `google.auth.exceptions`
→ El `secrets.toml` no está configurado correctamente.  
→ Verifica que la sección `[gcp_service_account]` esté completa y que los valores no tengan comillas extras o espacios.

### Error: `403 Permission Denied` en BigQuery
→ Tu cuenta de servicio no tiene acceso al dataset.  
→ Contacta a otoniel378 para que te agregue el rol **BigQuery Data Viewer** en el proyecto GCP.

### Error: `FileNotFoundError: .streamlit/secrets.toml`
→ Olvidaste copiar la plantilla. Ejecuta:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

### Error de Gemini: `Configura GEMINI_API_KEY`
→ Falta la API key de Google AI Studio en `secrets.toml`.  
→ Pídela a otoniel378 o crea la tuya en [aistudio.google.com](https://aistudio.google.com/app/apikey).

---

## Estructura del proyecto (referencia rápida)

```
proyecto-tyasaBI/
├── app.py                    ← Punto de entrada
├── config.py                 ← Colores, parámetros globales
├── requirements.txt          ← Dependencias Python
├── CONFIGURACION.md          ← Esta guía
├── .streamlit/
│   ├── secrets.toml          ← TUS credenciales (no está en git)
│   └── secrets.toml.example  ← Plantilla (sí está en git)
├── core/
│   └── db_connector.py       ← Cliente BigQuery
├── pages/                    ← Páginas de la app
└── mercado_noticias/         ← Módulo de noticias e IA
```
