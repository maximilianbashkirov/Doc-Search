import { useState } from 'react'
import { searchDocuments, deleteDocument } from './api.js'

const dateFormatter = new Intl.DateTimeFormat('ru-RU', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function formatDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date)
}

function DocumentCard({ document, onDelete, isDeleting }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <article className="card">
      <header className="card__head">
        <time className="card__date" dateTime={document.created_date}>
          {formatDate(document.created_date)}
        </time>
        <code className="card__id" title={document.id}>
          {document.id}
        </code>
      </header>

      <p className={`card__text${expanded ? ' card__text--expanded' : ''}`}>
        {document.text}
      </p>

      <button
        type="button"
        className="card__toggle"
        onClick={() => setExpanded((value) => !value)}
      >
        {expanded ? 'Свернуть' : 'Показать полностью'}
      </button>

      <footer className="card__foot">
        <ul className="rubrics">
          {document.rubrics.map((rubric) => (
            <li key={rubric} className="rubric">
              {rubric}
            </li>
          ))}
        </ul>
        <button
          type="button"
          className="card__delete"
          onClick={() => onDelete(document.id)}
          disabled={isDeleting}
        >
          {isDeleting ? 'Удаление…' : 'Удалить'}
        </button>
      </footer>
    </article>
  )
}

export default function App() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  async function handleSearch(event) {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) return

    setLoading(true)
    setError('')
    try {
      const found = await searchDocuments(trimmed)
      setDocuments(found)
      setSubmittedQuery(trimmed)
      setSearched(true)
    } catch (err) {
      setError(err.message)
      setDocuments([])
      setSearched(true)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id) {
    setDeletingId(id)
    setError('')
    try {
      await deleteDocument(id)
      setDocuments((current) => current.filter((doc) => doc.id !== id))
    } catch (err) {
      setError(err.message)
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="page">
      <main className="container">
        <header className="hero">
          <h1 className="hero__title">Поиск по документам</h1>
          <p className="hero__subtitle">
            Полнотекстовый поиск по Elasticsearch. Возвращаются первые 20
            документов, отсортированных по дате создания.
          </p>
        </header>

        <form className="search" onSubmit={handleSearch}>
          <input
            className="search__input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Например: Условия"
            aria-label="Поисковый запрос"
          />
          <button className="search__button" type="submit" disabled={loading}>
            {loading ? 'Ищем…' : 'Найти'}
          </button>
        </form>

        {error && <p className="alert alert--error">{error}</p>}

        {!loading && searched && documents.length === 0 && !error && (
          <p className="alert">
            По запросу «{submittedQuery}» ничего не найдено.
          </p>
        )}

        {!loading && documents.length > 0 && (
          <>
            <p className="stats">
              Найдено документов: {documents.length}
            </p>
            <div className="cards">
              {documents.map((document) => (
                <DocumentCard
                  key={document.id}
                  document={document}
                  onDelete={handleDelete}
                  isDeleting={deletingId === document.id}
                />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}