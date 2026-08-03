/**
 * MessageBubble.jsx — Glass chat bubble with Markdown rendering.
 * User: copper-tinted glass, right-aligned.
 * Assistant: dark surface glass with aperture monogram avatar.
 * No sparkle icons anywhere.
 */
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/* Aperture monogram for assistant */
const ApertureMark = () => (
  <svg viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="3.5" />
    <line x1="12" y1="3" x2="12" y2="8" />
    <line x1="12" y1="16" x2="12" y2="21" />
    <line x1="3" y1="12" x2="8" y2="12" />
    <line x1="16" y1="12" x2="21" y2="12" />
  </svg>
);

/* Simple user silhouette */
const UserIcon = () => (
  <svg viewBox="0 0 24 24">
    <circle cx="12" cy="8" r="4" />
    <path d="M20 21a8 8 0 0 0-16 0" />
  </svg>
);

export default function MessageBubble({ role, content }) {
  const isUser = role === 'user';

  return (
    <div className={`msg-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="msg-avatar">
        {isUser ? <UserIcon /> : <ApertureMark />}
      </div>
      <div className="msg-bubble">
        {isUser ? (
          <div>{content}</div>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
