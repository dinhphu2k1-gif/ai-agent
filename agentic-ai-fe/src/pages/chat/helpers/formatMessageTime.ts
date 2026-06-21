export const formatMessageTime = (isoOrDisplay?: string): string | undefined => {
  if (!isoOrDisplay) return undefined

  const parsed = Date.parse(isoOrDisplay)
  if (Number.isNaN(parsed)) return isoOrDisplay

  return new Date(parsed).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
