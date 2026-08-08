<template>
  <div class="settings-page">
    <h1>Настройки системы</h1>

    <div class="settings-grid">
      <!-- Блок 1: Управление вакансиями -->
      <div class="card">
        <h3>Управление вакансиями (Опросы)</h3>
        <p class="desc">Список активных позиций и их эталонного кода.</p>
        
        <!-- Список добавленных вакансий с прокруткой -->
        <div class="existing-vacancies" v-if="vacancies.length > 0">
          <div class="vacancy-item" v-for="vac in vacancies" :key="vac.id">
            <div class="vac-info" @click="openEditModal(vac)" style="cursor: pointer;" title="Нажмите, чтобы отредактировать">
              <strong>{{ vac.title }}</strong>
              <span class="vac-url">{{ vac.sheet_url }}</span>
            </div>
            <div class="item-actions">
              <button class="btn-edit" @click="openEditModal(vac)" title="Редактировать">✏️</button>
              <button class="btn-delete" @click="deleteVacancy(vac.id)" title="Удалить">🗑️</button>
            </div>
          </div>
        </div>
        <div v-else class="desc">Вакансий пока нет.</div>

        <!-- Кнопка добавления теперь внизу списка -->
        <button class="btn btn-outline mt-15" @click="openCreateModal">➕ Добавить вакансию</button>
      </div>

      <!-- Блок 2: Матрица компетенций -->
      <div class="card">
        <h3>Матрица компетенций</h3>
        <p class="desc">Загрузите актуальный Excel-файл с весами навыков.</p>
        
        <input type="file" @change="onMatrixUpload" accept=".xlsx,.csv" class="file-input" />
        
        <!-- Индикатор текущего файла -->
        <div class="file-status" v-if="currentMatrixFileName">
          📁 Активный файл: <strong>{{ currentMatrixFileName }}</strong>
        </div>
      </div>

      <!-- Блок 3: Границы TSI -->
      <div class="card">
        <h3>Граничные значения TSI</h3>
        <p class="desc">Настройте пороги для автоматического определения грейда.</p>
        
        <div class="tsi-settings">
          <div class="input-group">
            <label>Middle (от)</label>
            <input type="number" step="0.01" v-model="tsiMiddleMin" class="form-input" />
          </div>
          <div class="input-group">
            <label>Senior (от)</label>
            <input type="number" step="0.01" v-model="tsiSeniorMin" class="form-input" />
          </div>
          <button class="btn btn-primary mt-15" @click="saveTsiSettings">💾 Сохранить пороги</button>
        </div>
      </div>
    </div>

    <!-- МОДАЛЬНОЕ ОКНО ДЛЯ СОЗДАНИЯ / РЕДАКТИРОВАНИЯ ВАКАНСИИ -->
    <div class="modal-backdrop" v-if="isModalOpen">
      <div class="modal-content">
        <h3>{{ editingId ? 'Редактировать вакансию' : 'Новая вакансия' }}</h3>
        
        <div class="input-group">
          <label>Название вакансии</label>
          <input type="text" v-model="newVacTitle" placeholder="Например: C# Developer" class="form-input" />
        </div>
        <div class="input-group">
          <label>Ссылка на Google Таблицу ответов</label>
          <input type="text" v-model="newVacUrl" placeholder="https://docs.google.com/..." class="form-input" />
        </div>
        <div class="input-group">
          <label>Эталонный код (Идеал)</label>
          <textarea v-model="newVacIdealCode" placeholder="Вставьте идеальный код с паттернами..." class="form-input code-area"></textarea>
        </div>
        <div class="input-group">
          <label>Сломанный код (Антипаттерн)</label>
          <textarea v-model="newVacBrokenCode" placeholder="Вставьте плохой спагетти-код..." class="form-input code-area"></textarea>
        </div>

        <div class="modal-actions">
          <button class="btn btn-primary" @click="saveOrUpdateVacancy">💾 Сохранить</button>
          <button class="btn btn-secondary" @click="closeModal">❌ Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// Переменные для TSI
const tsiMiddleMin = ref(5.24)
const tsiSeniorMin = ref(11.38)

const vacancies = ref([])
const isModalOpen = ref(false)
const editingId = ref(null)

const newVacTitle = ref('')
const newVacUrl = ref('')
const newVacIdealCode = ref('')
const newVacBrokenCode = ref('')

// Имя текущего файла матрицы компетенций
const currentMatrixFileName = ref('')

// Управление модалкой
const openCreateModal = () => {
  editingId.value = null
  newVacTitle.value = ''
  newVacUrl.value = ''
  newVacIdealCode.value = ''
  newVacBrokenCode.value = ''
  isModalOpen.value = true
}

const openEditModal = (vac) => {
  editingId.value = vac.id
  newVacTitle.value = vac.title
  newVacUrl.value = vac.sheet_url
  newVacIdealCode.value = vac.ideal_code
  newVacBrokenCode.value = vac.broken_code
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}

// Загружаем настройки при открытии страницы
onMounted(async () => {
  try {
    const response = await fetch('http://localhost:8000/api/settings/tsi')
    if (response.ok) {
      const data = await response.json()
      tsiMiddleMin.value = data.tsi_middle_min
      tsiSeniorMin.value = data.tsi_senior_min
    }
    const vacRes = await fetch('http://localhost:8000/api/settings/vacancies')
    if (vacRes.ok) vacancies.value = await vacRes.json()
    
    // Здесь при желании можно сделать GET-запрос на бэкенд, чтобы узнать имя ранее загруженного файла матрицы, если оно сохраняется
  } catch (err) {
    console.error("Не удалось загрузить настройки", err)
  }
})

const saveOrUpdateVacancy = async () => {
  if (!newVacTitle.value.trim() || !newVacUrl.value.trim() || !newVacIdealCode.value.trim() || !newVacBrokenCode.value.trim()) {
    return alert("Заполните все поля, включая эталонный и сломанный код!")
  }

  if (!newVacUrl.value.startsWith('http')) {
    return alert("Ссылка на Google Таблицу должна начинаться с http:// или https://")
  }

  const url = editingId.value 
    ? `http://localhost:8000/api/settings/vacancies/${editingId.value}`
    : 'http://localhost:8000/api/settings/vacancies'
    
  const method = editingId.value ? 'PUT' : 'POST'

  try {
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        title: newVacTitle.value, 
        sheet_url: newVacUrl.value,
        ideal_code: newVacIdealCode.value,
        broken_code: newVacBrokenCode.value
      })
    })

    if (res.ok) {
      const vacRes = await fetch('http://localhost:8000/api/settings/vacancies')
      if (vacRes.ok) vacancies.value = await vacRes.json()
      closeModal()
    } else {
      alert("Ошибка при сохранении вакансии на сервере.")
    }
  } catch (err) {
    alert("Ошибка соединения с сервером.")
    console.error(err)
  }
}

const deleteVacancy = async (id) => {
  if (!confirm("Точно удалить вакансию?")) return
  
  const res = await fetch(`http://localhost:8000/api/settings/vacancies/${id}`, { method: 'DELETE' })
  if (res.ok) {
    vacancies.value = vacancies.value.filter(v => v.id !== id)
  }
}

// Сохраняем новые значения порогов
const saveTsiSettings = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/settings/tsi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tsi_middle_min: parseFloat(tsiMiddleMin.value),
        tsi_senior_min: parseFloat(tsiSeniorMin.value)
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      alert(result.message)
    }
  } catch (err) {
    alert("Ошибка при сохранении настроек")
  }
}

// Загрузка матрицы компетенций
const onMatrixUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // Запоминаем имя файла для отображения на экране
  currentMatrixFileName.value = file.name

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch('http://localhost:8000/api/settings/upload-matrix', {
      method: 'POST',
      body: formData
    })
    if (response.ok) {
      alert(`Файл "${file.name}" успешно загружен!`)
    } else {
      alert("Ошибка загрузки файла матрицы на сервер.")
    }
  } catch (err) {
    alert("Ошибка соединения при загрузке матрицы.")
  }
}
</script>

<style scoped>
.settings-page h1 { 
  color: #6a6561; 
  margin-top: 0;
  margin-bottom: 25px; 
  font-weight: 800;
}

.settings-grid { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 20px; 
}

.card { 
  background: #ffffff; 
  padding: 25px; 
  border-radius: 12px; 
  border: 1px solid #9d9894; 
  box-shadow: 0 4px 15px rgba(106, 101, 97, 0.08); 
}

.card h3 { 
  margin-top: 0; 
  color: #6a6561; 
  font-weight: 700;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.btn-sm {
  padding: 6px 12px;
  font-size: 0.85rem;
}

.desc { 
  color: #9d9894; 
  font-size: 0.9rem; 
  margin-bottom: 20px; 
  line-height: 1.4;
}

/* Формы ввода */
.input-group { margin-bottom: 15px; }
.input-group label { 
  display: block; 
  margin-bottom: 6px; 
  color: #6a6561; 
  font-size: 0.85rem; 
  font-weight: 600;
}

.form-input { 
  width: 100%; 
  padding: 10px 12px; 
  background: #ffffff; 
  border: 1px solid #9d9894; 
  color: #6a6561; 
  border-radius: 8px; 
  box-sizing: border-box; 
  outline: none;
  font-family: inherit;
  transition: all 0.2s;
}

.form-input:focus {
  border-color: #7d8391;
  box-shadow: 0 0 0 2px rgba(125, 131, 145, 0.2);
}

/* Кнопки */
.btn { 
  padding: 10px 15px; 
  border-radius: 8px; 
  cursor: pointer; 
  font-weight: 600; 
  border: none; 
  font-family: inherit;
  transition: all 0.2s;
  background: #A59988;
}

.btn-primary { 
  background: #A59988; 
  color: #ffffff; 
  width: 100%; 
}
.btn-primary:hover { background: #6a6561; }

.mt-15 { margin-top: 15px; }

/* Список вакансий */
.existing-vacancies {
  max-height: 280px;
  overflow-y: auto;
  padding-right: 5px;
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.existing-vacancies::-webkit-scrollbar { width: 6px; }
.existing-vacancies::-webkit-scrollbar-thumb { background: #9d9894; border-radius: 3px; }

.vacancy-item { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  background: #e8e8e8; 
  padding: 12px 15px; 
  border-radius: 8px; 
  border: 1px solid #c4bfbb; 
}

.vac-info { 
  display: flex; 
  flex-direction: column; 
  gap: 4px; 
  overflow: hidden; 
}
.vac-info strong { color: #6a6561; font-size: 0.95rem; }
.vac-url { 
  color: #9d9894; 
  font-size: 0.75rem; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis; 
  max-width: 200px; 
}

.item-actions { display: flex; gap: 8px; }
.btn-edit {
  background: transparent;
  color: #7d8391;
  border: 1px solid #7d8391;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-edit:hover { background: #7d8391; color: #fff; }

.btn-delete { 
  background: transparent; 
  color: #7b3529; 
  border: 1px solid #7b3529; 
  padding: 6px 10px; 
  border-radius: 6px; 
  cursor: pointer; 
  font-weight: 600;
  transition: all 0.2s;
}
.btn-delete:hover { background: #7b3529; color: #ffffff; }

/* Поле загрузки файла и статус */
.file-input {
  display: block;
  width: 100%;
  padding: 8px;
  color: #6a6561;
  border: 1px dashed #9d9894;
  border-radius: 8px;
  background: #e8e8e8;
  cursor: pointer;
}
.file-input::file-selector-button {
  background: #c4bfbb;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  color: #6a6561;
  font-weight: 600;
  cursor: pointer;
  margin-right: 10px;
  transition: background 0.2s;
}
.file-input::file-selector-button:hover {
  background: #9d9894;
  color: #ffffff;
}
.file-status {
  margin-top: 12px;
  font-size: 0.85rem;
  color: #7d8391;
  background: #e8e8e8;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #c4bfbb;
}

.code-area {
  min-height: 120px;
  resize: vertical;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85rem;
}

/* Модальное окно */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(106, 101, 97, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: #ffffff;
  padding: 30px;
  border-radius: 12px;
  width: 550px;
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid #9d9894;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}

.modal-content h3 {
  margin-top: 0;
  color: #6a6561;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-secondary {
  background: #c4bfbb;
  color: #6a6561;
  flex: 1;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}
.btn-secondary:hover {
  background: #9d9894;
  color: #fff;
}
</style>