<template>
  <div
    class="portal-shell"
    :class="{ 'portal-shell--kiosko': esComedor }"
  >
    <header class="portal-topbar">
      <div class="portal-topbar__brand">
        <span class="portal-topbar__title">Portal hospitalario</span>
      </div>

      <nav
        v-if="showNav"
        class="portal-nav"
        aria-label="Navegación principal"
      >
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="portal-nav__link"
          active-class="portal-nav__link--active"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="portal-topbar__user">
        <div class="portal-user-meta">
          <span class="portal-user-meta__name">{{ nombreVisible }}</span>
          <span class="portal-user-meta__detail">
            {{ rolVisible }}
            <template v-if="sectorVisible"> · {{ sectorVisible }}</template>
          </span>
        </div>

        <LogoutButton />
      </div>
    </header>

    <main class="portal-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView } from 'vue-router'

import LogoutButton from '@/modules/auth/components/LogoutButton.vue'
import { useAuthStore } from '@/stores/auth'
import { getNavItemsForRole } from '@/router/nav-items'

const authStore = useAuthStore()

const user = computed(() => authStore.user)
const roleKey = computed(() => authStore.operationalRoleKey)

const esComedor = computed(() => roleKey.value === 'sectorComedor')
const showNav = computed(() => !esComedor.value && navItems.value.length > 0)

const navItems = computed(() => getNavItemsForRole(roleKey.value))

/**
 * Prioriza nombre+apellido del personal; si no hay, usa alias.
 */
const nombreVisible = computed(() => {
  const actual = user.value
  if (!actual) {
    return 'Usuario'
  }

  const nombreCompleto = [actual.nombre, actual.apellido]
    .filter(Boolean)
    .join(' ')
    .trim()

  return nombreCompleto || actual.alias || 'Usuario'
})

const rolVisible = computed(() => user.value?.rol || 'Sin rol')

const sectorVisible = computed(() => {
  const sector = user.value?.sector
  if (!sector || !sector.nombre) {
    return null
  }
  return sector.nombre
})
</script>

<style scoped>
.portal-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  color: #1f2933;
}

.portal-topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: #ffffff;
  border-bottom: 1px solid #d9e2ec;
}

.portal-topbar__brand {
  font-weight: 700;
  letter-spacing: 0.01em;
}

.portal-topbar__title {
  font-size: 1rem;
}

.portal-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  flex: 1;
}

.portal-nav__link {
  text-decoration: none;
  color: #334e68;
  padding: 0.35rem 0.7rem;
  border-radius: 0.35rem;
  font-size: 0.95rem;
}

.portal-nav__link:hover {
  background: #f0f4f8;
}

.portal-nav__link--active {
  background: #d9e2ec;
  color: #102a43;
  font-weight: 600;
}

.portal-topbar__user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: auto;
}

.portal-user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.25;
}

.portal-user-meta__name {
  font-weight: 600;
  font-size: 0.95rem;
}

.portal-user-meta__detail {
  font-size: 0.8rem;
  color: #627d98;
}

.portal-main {
  flex: 1;
  padding: 1.25rem;
}

/* El kiosco de entregas ya maneja su viewport; evitamos padding doble. */
.portal-shell--kiosko .portal-main {
  padding: 0;
}

@media (max-width: 720px) {
  .portal-topbar__user {
    width: 100%;
    justify-content: space-between;
    margin-left: 0;
  }

  .portal-user-meta {
    align-items: flex-start;
  }
}
</style>