<template>
  <div class="profile-page">
    <button class="back-btn" @click="router.push('/')">🔙 Вернуться к списку</button>

    <div v-if="candidate" class="dashboard-grid">
      
      <!-- ВЕРХНЯЯ КАРТОЧКА (Сводка) -->
      <div class="card header-card">
        <div class="header-info">
          <h2>👤 {{ candidate.name }}</h2>
          <p class="rationale"><b>Обоснование ИИ:</b> {{ candidate.rationale }}</p>
        </div>
        <div class="badges">
          <div class="stat-box">
            <span class="label">Итоговый грейд</span>
            <span class="value main-grade">{{ candidate.grade }}</span>
          </div>
          <div class="stat-box">
            <span class="label">Рыночный потенциал (TSI)</span>
            <span class="value">{{ candidate.tsi.toFixed(2) }}</span>
          </div>
          <div class="stat-box">
            <span class="label">Самооценка</span>
            <span class="value">{{ candidate.selfGrade }}</span>
          </div>
        </div>
      </div>

      <!-- ГРАФИКИ -->
      <div class="charts-row">
        <!-- Радар (Теория) -->
        <div class="card chart-card">
          <h3>Профиль компетенций (Теория)</h3>
          <Chart type="radar" :data="radarData" :options="radarOptions" class="chart-container" />
        </div>

        <!-- Бар-чарт (K-score) -->
        <div class="card chart-card">
          <h3>От Хаоса к Архитектуре (GraphCodeBERT)</h3>
          <Chart type="bar" :data="barData" :options="barOptions" class="chart-container" />
        </div>
      </div>

    </div>
    
    <div v-else class="loading">
      <h2>Загрузка профиля...</h2>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Chart from 'primevue/chart'

const route = useRoute()
const router = useRouter()
const candidate = ref(null)

// Данные для графиков
const radarData = ref(null)
const barData = ref(null)

// Настройки внешнего вида графиков
const radarOptions = {
  plugins: { legend: { display: false } },
  scales: { r: { min: 0, max: 100 } }
}

const barOptions = {
  indexAxis: 'y', // Горизонтальный бар
  plugins: { legend: { display: false } },
  scales: { 
    x: { min: 0, max: 1.2, title: { display: true, text: 'Прогресс к эталону (1.0 = Идеал)' } } 
  },
  maintainAspectRatio: false
}

onMounted(async () => {
  const id = route.params.id
  try {
    const response = await fetch(`http://localhost:8000/api/candidate/${id}`)
    if (response.ok) {
      candidate.value = await response.json()
      setupCharts(candidate.value)
    } else {
      alert("Кандидат не найден")
      router.push('/')
    }
  } catch (e) {
    console.error("Ошибка загрузки профиля", e)
  }
})

const setupCharts = (data) => {
  // Бар-чарт (K-score) в новых пастельных цветах
  barData.value = {
    labels: ['Текущий уровень кода'],
    datasets: [{
      label: 'K-score',
      // Используем цвета из новой палитры: пыльно-синий (хорошо), персиковый (средне), терракотовый (плохо)
      backgroundColor: data.kScore >= 0.7 ? '#7d8391' : (data.kScore >= 0.4 ? '#f29875' : '#7b3529'),
      data: [data.kScore]
    }]
  }

  let lRespPercentage = 30;
  if (data.marketGrade === 'Senior') lRespPercentage = 100;
  else if (data.marketGrade === 'Middle') lRespPercentage = 60;
  
  // Радар в пыльно-синих тонах (из палитры №5)
  radarData.value = {
    labels: [
      'Код (K-score)', 
      'Теория (TF-IDF)', 
      'Архитектура', 
      'Опыт (до 5 лет)', 
      'Ответственность'
    ],
    datasets: [{
      label: 'Инженерный профиль',
      backgroundColor: 'rgba(125, 131, 145, 0.2)', // #7d8391 с прозрачностью
      borderColor: '#7d8391',
      pointBackgroundColor: '#7d8391',
      data: [
        data.kScore * 100,
        data.theory * 100,
        data.archScore * 100,
        Math.min(100, (data.expYears / 5.0) * 100),
        lRespPercentage
      ]
    }]
  }
}
</script>

<style scoped>
.profile-page { padding: 30px; background: #e1e1e1; min-height: 100vh; font-family: 'Inter', sans-serif; }
.back-btn { background: none; border: none; color: #6a6561; cursor: pointer; font-size: 1rem; margin-bottom: 20px; font-weight: 600; }
.back-btn:hover { color: #7d8391; }

.dashboard-grid { display: flex; flex-direction: column; gap: 20px; }
.card { background: #ffffff; border-radius: 12px; padding: 25px; border: 1px solid #9d9894; box-shadow: 0 4px 15px rgba(106, 101, 97, 0.08); }

/* Верхняя карточка */
.header-card { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;}
.header-info h2 { margin: 0 0 10px 0; color: #6a6561; font-size: 1.8rem; font-weight: 800; }
.rationale { margin: 0; color: #9d9894; font-size: 1.1rem; max-width: 600px; line-height: 1.5; }

.badges { display: flex; gap: 20px; }
.stat-box { display: flex; flex-direction: column; background: #e8e8e8; padding: 15px 20px; border-radius: 8px; min-width: 150px; border: 1px solid #c4bfbb; }
.stat-box .label { font-size: 0.85rem; color: #9d9894; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
.stat-box .value { font-size: 1.3rem; font-weight: 800; color: #6a6561; }
.stat-box .main-grade { color: #7b3529; } /* Терракотовый акцент для итогового грейда */

/* Графики */
.charts-row { display: flex; gap: 20px; }
.chart-card { flex: 1; min-width: 0; }
.chart-card h3 { margin-top: 0; color: #6a6561; font-weight: 700; text-align: center; }
.chart-container { height: 400px; display: flex; justify-content: center; align-items: center; }

.loading { text-align: center; margin-top: 100px; color: #9d9894; font-weight: bold; }
</style>