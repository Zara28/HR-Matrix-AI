import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import CandidatePage from '../views/CandidatePage.vue'
import Settings from '@/views/Settings.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/settings', name: 'settings', component: Settings },
    { path: '/candidate/:id', name: 'candidate', component: CandidatePage }
  ]
})

export default router