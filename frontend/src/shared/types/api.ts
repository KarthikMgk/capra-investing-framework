export interface ApiError {
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export interface ApiCollection<T> {
  items: T[]
  total: number
}
