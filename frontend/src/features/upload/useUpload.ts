import { useMutation } from "@tanstack/react-query"
import apiClient from "@/shared/lib/apiClient"

export interface UploadResponse {
  status: "ok"
  batch_id: string
}

function createUploadMutation(endpoint: string) {
  return () =>
    useMutation({
      mutationFn: (file: File) => {
        const formData = new FormData()
        formData.append("file", file)
        return apiClient
          .post<UploadResponse>(endpoint, formData)
          .then((r) => r.data)
      },
    })
}

export const useUploadScreener = createUploadMutation("/api/v1/upload/screener")
export const useUploadRbi = createUploadMutation("/api/v1/upload/rbi")
