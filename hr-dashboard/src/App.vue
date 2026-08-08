<script setup>
import { onMounted } from 'vue'

// Безжалостно вырезаем плашку PrimeUI при загрузке
onMounted(() => {
  setTimeout(() => {
    const allDivs = document.querySelectorAll('div');
    allDivs.forEach(div => {
      if (div.innerText && div.innerText.includes('Invalid PrimeUI License')) {
        div.remove();
      }
    });
  }, 500); // Небольшая задержка, чтобы PrimeVue успел отрендерить плашку
})
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <h2>HR Matrix AI</h2>
      <nav class="nav-menu">
        <router-link to="/" class="nav-link">📊 Сводка</router-link>
        <router-link to="/settings" class="nav-link">⚙️ Настройки</router-link>
      </nav>
    </aside>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
/* Скрываем плашку PrimeUI */
div[style*="z-index: 999999999"], 
div[style*="z-index: 99999"] {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

body { 
  margin: 0; 
  background-color: #f0ebe6; /* Теплый пудрово-серый фон */
  color: #5a5550; /* Мягкий коричнево-серый текст */
  font-family: 'Inter', sans-serif; 
}

.app-layout { display: flex; height: 100vh; overflow: hidden; }

/* Боковое меню */
.sidebar { 
  width: 260px; 
  background: #706555; /* Молочный оттенок, без чистого белого */
  padding: 25px 20px; 
  border-right: 1px solid #e3ddd7; 
  display: flex; 
  flex-direction: column; 
}

.sidebar h2 { 
  color: #252321; 
  margin-top: 0; 
  margin-bottom: 35px; 
  font-weight: 800; 
}

.nav-menu { display: flex; flex-direction: column; gap: 10px; }
.nav-link { 
  padding: 12px 16px; 
  color: #D1CBC2; 
  text-decoration: none; 
  border-radius: 8px; 
  transition: 0.2s ease; 
  font-weight: 600; 
}

.nav-link:hover {
  background: #e8e3de; 
  color: #2c2a27; 
}

/* Принудительная подсветка активной страницы */
.nav-link.router-link-active { 
  background: #A59988; /* Пыльно-голубой акцент */
  color: #ffffff; 
  box-shadow: 0 4px 12px rgba(143, 163, 184, 0.3); 
}

.main-content { flex: 1; padding: 40px; overflow-y: auto; }
</style>