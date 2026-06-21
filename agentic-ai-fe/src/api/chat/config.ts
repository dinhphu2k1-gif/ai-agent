export const getChatApiBaseUrl = (): string => {
  const chatRoot =
    import.meta.env.VITE_CHAT_API_URL?.trim() ||
    import.meta.env.VITE_APP_API_URL?.trim() ||
    ''

  return `${chatRoot.replace(/\/$/, '')}/api/v1/chat`
}
