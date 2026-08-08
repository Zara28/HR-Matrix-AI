<template>
  <div class="dashboard-page">
    <div class="header">
      <h1>Сводка по кандидатам</h1>
      
      <div class="actions">
        <!-- Выпадающий список вакансий -->
        <select v-model="selectedVacancyId" class="vacancy-select">
          <option disabled value="">Выберите вакансию...</option>
          <option v-for="vac in vacancies" :key="vac.id" :value="vac.id">
            {{ vac.title }}
          </option>
        </select>
        
        <button class="btn-sync" @click="syncData" :disabled="!selectedVacancyId">
          Синхронизировать
        </button>
      </div>
    </div>

    <DataTable 
        :value="candidates" 
        v-model:filters="filters" 
        :globalFilterFields="['name', 'grade', 'marketGrade', 'selfGrade']"
        :paginator="true" 
        :rows="10" 
        dataKey="id" 
        class="p-datatable-sm dark-table">
        
        <template #header>
          <div class="table-header">
            <span class="search-box">
              <input type="text" v-model="filters['global'].value" placeholder="Поиск кандидата..." class="search-input" />
            </span>
          </div>
        </template>

        <Column field="name" header="Имя" sortable style="width: 25%"></Column>
        <Column field="grade" header="Определенный грейд" sortable style="width: 20%">
          <template #body="slotProps">
            <span class="grade-badge" :class="{
                'grade-junior': slotProps.data.grade.includes('Junior'),
                'grade-middle': slotProps.data.grade.includes('Middle'),
                'grade-senior': slotProps.data.grade.includes('Senior'),
                'grade-unknown': slotProps.data.grade.includes('Unknown') || !slotProps.data.grade
                }">{{ slotProps.data.grade }}</span>
          </template>
        </Column>
        <Column field="grade" header="Заявленный грейд" sortable style="width: 20%">
          <template #body="slotProps">
            <span class="grade-badge" :class="{
                'grade-junior': slotProps.data.selfGrade.includes('Junior'),
                'grade-middle': slotProps.data.selfGrade.includes('Middle'),
                'grade-senior': slotProps.data.selfGrade.includes('Senior'),
                'grade-unknown': slotProps.data.selfGrade.includes('Unknown') || !slotProps.data.selfGrade
                }">{{ slotProps.data.selfGrade }}</span>
          </template>
        </Column>
        <Column field="kScore" header="K-score (Код)" sortable style="width: 20%">
          <template #body="slotProps">
            <b>{{ (slotProps.data.kScore * 100).toFixed(1) }}%</b>
          </template>
        </Column>
        <Column field="theory" header="Теория" sortable style="width: 20%">
          <template #body="slotProps">
            <b>{{ (slotProps.data.theory * 100).toFixed(1) }}%</b>
          </template>
        </Column>
        <Column header="Действия" style="width: 15%">
          <template #body="slotProps">
            <button class="btn-link" @click="goToProfile(slotProps.data.id)">Профиль ➔</button>
          </template>
        </Column>
</DataTable>
  </div>
</template>

<style scoped>
/* --- Основной контейнер и шапка --- */
.header { 
  display: flex; justify-content: space-between; align-items: center; 
  margin-bottom: 30px; 
}
.header h1 { margin: 0; color: #4a4540; font-weight: 700; }

/* --- Элементы управления --- */
.actions { display: flex; gap: 15px; align-items: center; }

.search-input, .vacancy-select { 
  padding: 10px 15px; 
  background: #f8f6f4; 
  color: #5a5550; 
  border: 1px solid #d3cec8; 
  border-radius: 8px; 
  outline: none; 
  font-size: 0.95rem; 
  transition: all 0.2s;
}

.search-input:focus, .vacancy-select:focus {
  border-color: #8fa3b8;
  box-shadow: 0 0 0 2px rgba(143, 163, 184, 0.2);
}

.btn-sync { 
  background: #A59988; /* Пыльно-голубой */
  color: #ffffff; 
  border: none; 
  padding: 10px 20px; 
  border-radius: 8px; 
  cursor: pointer; 
  font-weight: 600;
  transition: background 0.2s;
}
.btn-sync:hover:not(:disabled) { 
  background: #7a8ea3; 
}
.btn-sync:disabled { opacity: 0.5; cursor: not-allowed; }

/* --- Пастельная тема для PrimeVue Table --- */
:deep(.p-datatable) {
  background: #f8f6f4 !important;
  border-radius: 12px !important;
  border: 1px solid #e3ddd7 !important;
  box-shadow: 0 4px 20px rgba(90, 85, 80, 0.04) !important; 
  overflow: hidden;
}

/* Заголовок таблицы */
:deep(.p-datatable-header) {
  background: transparent !important;
  border: none !important;
}

:deep(.p-datatable-thead > tr > th) {
  background: #f0ebe6 !important; 
  color: #8c857f !important; 
  border-bottom: 1px solid #e3ddd7 !important;
  border-top: none !important;
  padding: 16px 15px !important;
  font-weight: 600 !important;
}

/* Строки таблицы */
:deep(.p-datatable-tbody > tr) {
  background: #f8f6f4 !important;
  color: #5a5550 !important;
  transition: background 0.2s;
}

:deep(.p-datatable-tbody > tr:hover) {
  background: #f0ebe6 !important; 
}

/* Ячейки */
:deep(.p-datatable-tbody > tr > td) {
  border-bottom: 1px solid #efeae5 !important;
  padding: 15px !important;
}

/* Пагинация */
:deep(.p-paginator) {
  background: #f8f6f4 !important;
  border-top: 1px solid #e3ddd7 !important;
  padding: 15px !important;
}

:deep(.p-paginator .p-paginator-pages .p-paginator-page),
:deep(.p-paginator .p-paginator-first),
:deep(.p-paginator .p-paginator-prev),
:deep(.p-paginator .p-paginator-next),
:deep(.p-paginator .p-paginator-last) {
  color: #8c857f !important;
  background: transparent !important;
  border: none !important;
  border-radius: 6px !important;
  margin: 0 2px !important;
  transition: all 0.2s;
}

/* Принудительная подсветка активной страницы */
:deep(.p-paginator .p-paginator-page.p-highlight),
:deep(.p-paginator .p-paginator-page[data-p-highlight="true"]),
:deep(.p-paginator .p-paginator-page[aria-current="page"]) {
  background: #A59988 !important;
  color: #ffffff !important;
  font-weight: bold !important;
}

/* Легкий ховер для неактивных страниц */
:deep(.p-paginator .p-paginator-page:hover:not(.p-highlight)) {
  background: #e8e3de !important;
  color: #5a5550 !important;
}

/* Ссылки профиля */
:deep(.p-datatable-tbody > tr > td a) {
  color: #8fa3b8;
  text-decoration: none;
}
:deep(.p-datatable-tbody > tr > td a:hover) {
  text-decoration: underline;
}

/* --- Пастельные бейджи грейдов --- */
:deep(.grade-badge) {
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
  display: inline-block;
  text-align: center;
  white-space: nowrap;
}

:deep(.grade-junior) { 
  background: #e2e8e2; /* Приглушенный шалфей */
  color: #6a7c6a; 
}
:deep(.grade-middle) { 
  background: #f0e6d8; /* Теплый песочный */
  color: #a38563; 
}
:deep(.grade-senior) { 
  background: #e6e2e8; /* Пыльная лаванда */
  color: #8a7a94; 
}
:deep(.grade-unknown) { 
  background: #e8e6e3; /* Мягкий серый */
  color: #8c857f; 
}
</style>

<script setup>
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { ref, onMounted, watch } from 'vue'
import { FilterMatchMode } from '@primevue/core/api'

const router = useRouter()

const filters = ref({
    global: { value: null, matchMode: 'contains' }
})

// Переменные для ссылки и списка кандидатов
const sheetUrl = ref('')
const candidates = ref([])
const vacancies = ref([])
const selectedVacancyId = ref('')

watch(selectedVacancyId, async (newVal) => {
  if (!newVal) return
  try {
    const res = await fetch(`http://localhost:8000/api/candidate/list?vacancy_id=${newVal}`)
    if (res.ok) {
      const data = await res.json()
      candidates.value = data.candidates
    }
  } catch (e) { console.error(e) }
})

onMounted(async () => {
  try {
    const response = await fetch('http://localhost:8000/api/candidate/list')
    const result = await response.json()
    if (response.ok && result.candidates) {
      candidates.value = result.candidates
    }

    const res = await fetch('http://localhost:8000/api/settings/vacancies')
    if (res.ok) {
      vacancies.value = await res.json()
      if (vacancies.value.length > 0) {
        selectedVacancyId.value = vacancies.value[0].id // Выбираем первую по умолчанию
      }
    }
  } catch (err) {
    console.error("Не удалось загрузить данные из бд:", err)
  }
})

// 1. Загрузка матрицы на бэкенд
const onMatrixUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('matrix_file', file)

  try {
    const response = await fetch('http://localhost:8000/api/matrix/upload', {
      method: 'POST',
      body: formData
    })
    const result = await response.json()
    alert(result.message || "Матрица успешно загружена!")
  } catch (err) {
    alert("Ошибка загрузки матрицы: " + err.message)
  }
}

// 2. Синхронизация данных из Google Таблицы
const syncData = async () => {
  if (!selectedVacancyId.value) return alert("Выберите вакансию!")
  const selectedVac = vacancies.value.find(v => v.id === selectedVacancyId.value)
  
  try {
    const response = await fetch('http://localhost:8000/api/candidate/sync-sheet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        sheet_url: selectedVac.sheet_url,
        vacancy_id: selectedVac.id
      })
    })
    
    // Сначала парсим ответ
    const result = await response.json()
    
    if (response.ok) {
      // Если всё 200 OK
      candidates.value = result.candidates
      alert(result.message)
    } else {
      // Если сервер вернул 400 (нет кода) или 500
      alert(`Ошибка синхронизации: ${result.detail || 'Неизвестная ошибка'}`)
    }
  } catch (err) {
    alert("Сервер недоступен или произошла сетевая ошибка.")
    console.error(err)
  }
}

const goToProfile = (id) => {
  router.push(`/candidate/${id}`)
}
</script>

<style scoped>
.dashboard { display: flex; height: 100vh; background: #f8fafc; font-family: sans-serif; }
.sidebar { width: 260px; background: #1e293b; color: white; padding: 20px; }
.content { flex: 1; padding: 30px; }
.control-group { margin-top: 30px; }
.desc { font-size: 0.8rem; color: #94a3b8; margin-bottom: 10px; }
.file-input { color: white; width: 100%; font-size: 0.8rem; }
.text-input, .search-input { width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc; margin-bottom: 10px; box-sizing: border-box; }
.btn { width: 100%; padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn:hover { background: #2563eb; }
.btn-link { background: none; border: none; color: #3b82f6; cursor: pointer; font-weight: bold; }
.table-header { display: flex; justify-content: space-between; }
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
.senior { background: #dcfce7; color: #166534; }
.middle { background: #dbeafe; color: #1e40af; }
.junior { background: #ffedd5; color: #9a3412; }
</style>