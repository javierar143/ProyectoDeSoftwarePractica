# Portal — Grupo 50

Frontend Vue 3 (Vite) para los roles operativos del sistema de comidas hospitalarias:

- **Jefe de Servicio**
- **Servicio de Alimentación**
- **Sector Comedor**

El portal **no** administra sectores ni usuarios. Consume la API del admin Flask (`/api/...`) con JWT.

La gestión de sectores, usuarios y configuración sigue en la app **admin** (Flask).

---

## Requisitos

- Node.js `^22.18` o `>=24.12` (ver `package.json` → `engines`)
- npm
- Admin Flask corriendo en local (por defecto `http://localhost:5000`)
- PostgreSQL del proyecto levantado (`g50-postgres`)

---

## Setup rápido

```bash
cd portal
npm install