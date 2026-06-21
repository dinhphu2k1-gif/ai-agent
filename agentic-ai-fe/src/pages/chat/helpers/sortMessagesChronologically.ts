import type { Message } from '@/api/chat'

/** BE list endpoint returns newest-first; chat UI expects oldest-first. */
export const sortMessagesChronologically = (messages: Message[]): Message[] =>
  messages
    .map((msg, index) => ({ msg, index }))
    .sort((a, b) => {
      const ta = a.msg.timestamp ? Date.parse(a.msg.timestamp) : Number.NaN
      const tb = b.msg.timestamp ? Date.parse(b.msg.timestamp) : Number.NaN
      const aHasTime = !Number.isNaN(ta)
      const bHasTime = !Number.isNaN(tb)

      if (aHasTime && bHasTime && ta !== tb) return ta - tb
      if (aHasTime && !bHasTime) return -1
      if (!aHasTime && bHasTime) return 1
      return a.index - b.index
    })
    .map(({ msg }) => msg)
