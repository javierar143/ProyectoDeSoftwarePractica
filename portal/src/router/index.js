import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'inicio',
      component: () => import('../modules/demo/views/HomeView.vue'),
    },
    {
      path: '/contador',
      name: 'contador',
      component: () => import('../modules/demo/views/CounterView.vue'),
    },
  ],
})

export default router