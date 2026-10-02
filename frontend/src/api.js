const API_BASE = import.meta.env.VITE_API_BASE || ''

async function readError(response, fallback) {
  try {
    const data = await response.json()
    if (data && typeof data.detail === 'string') return data.detail
  } catch {
  }
  return `${fallback} (HTTP ${response.status})`
}

export async function searchDocuments(query) {
  const response = await fetch(
    `${API_BASE}/search?query=${encodeURIComponent(query)}`
  )
  if (!response.ok) {
    throw new Error(await readError(response, 'Ошибка поиска'))
  }
  return response.json()
}

export async function deleteDocument(id) {
  const response = await fetch(`${API_BASE}/document/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
  if (response.status === 404) {
    throw new Error('Документ уже удалён')
  }
  if (!response.ok) {
    throw new Error(await readError(response, 'Ошибка удаления'))
  }
  return true
}