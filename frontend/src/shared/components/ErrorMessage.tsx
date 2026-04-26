interface ErrorMessageProps {
  message: string
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  return <p className="text-sm text-red-600">{message}</p>
}
