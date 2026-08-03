/**
 * ChatInterface.jsx — Conversation workspace.
 * Empty state uses Fraunces display headline.
 * Suggestion tiles, glass input dock, aperture loading indicator.
 * No duplicate processing messages — input placeholder is plain disabled text.
 */
import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';

/* SVG icons — 1.5px stroke family */
const ChatGlyph = () => (
  <svg viewBox="0 0 24 24">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const ArrowIcon = () => (
  <svg viewBox="0 0 24 24">
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </svg>
);

/* Aperture monogram for assistant loading */
const ApertureMark = () => (
  <svg viewBox="0 0 24 24" style={{ width: 16, height: 16, stroke: 'var(--accent-primary)', strokeWidth: 1.5, fill: 'none' }}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="3.5" />
    <line x1="12" y1="3" x2="12" y2="8" />
    <line x1="12" y1="16" x2="12" y2="21" />
  </svg>
);

export default function ChatInterface({
  messages,
  onSendMessage,
  isProcessing,
  streamingContent,
  hasSession,
}) {
  const [input, setInput] = useState('');
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  useEffect(() => {
    if (hasSession && !isProcessing) inputRef.current?.focus();
  }, [hasSession, isProcessing]);

  const submit = (e) => {
    e?.preventDefault();
    const t = input.trim();
    if (!t || isProcessing || !hasSession) return;
    onSendMessage(t);
    setInput('');
  };

  const suggest = (text) => {
    if (isProcessing || !hasSession) return;
    onSendMessage(text);
  };

  return (
    <div className="chat-scroll-wrapper" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="chat-scroll">
        {/* Empty state with Fraunces display headline */}
        {messages.length === 0 && !streamingContent && (
          <div className="empty-state">
            <div className="empty-glyph"><ChatGlyph /></div>

            <h2 className="empty-headline">
              {hasSession ? 'Ready to Analyze' : 'Upload an Image to Begin'}
            </h2>
            <p className="empty-body">
              {hasSession
                ? 'Choose a prompt below or type your own question.'
                : 'Drop an image on the left panel, then ask questions about it here.'}
            </p>

            {hasSession && (
              <div className="suggestions">
                <div className="suggestion-tile"
                  onClick={() => suggest('Analyze this image and summarize key findings')}>
                  <div className="suggestion-title">Full analysis</div>
                  <div className="suggestion-desc">Summarize content and key details</div>
                </div>
                <div className="suggestion-tile"
                  onClick={() => suggest('Extract all text, headings, and tables from this image')}>
                  <div className="suggestion-title">Text extraction</div>
                  <div className="suggestion-desc">Pull text, tables and structure</div>
                </div>
                <div className="suggestion-tile"
                  onClick={() => suggest('Identify all interactive elements and layout structure')}>
                  <div className="suggestion-title">Element detection</div>
                  <div className="suggestion-desc">Find buttons, inputs and layout</div>
                </div>
                <div className="suggestion-tile"
                  onClick={() => suggest('Describe any notable findings or observations')}>
                  <div className="suggestion-title">Observations</div>
                  <div className="suggestion-desc">Clinical or visual findings</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Message history */}
        {messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} content={msg.content} />
        ))}

        {/* Live streaming */}
        {streamingContent && (
          <MessageBubble role="assistant" content={streamingContent} />
        )}

        {/* Aperture breathing indicator — only when processing and no stream yet */}
        {isProcessing && !streamingContent && messages.length > 0 && (
          <div className="msg-row assistant">
            <div className="msg-avatar"><ApertureMark /></div>
            <div className="msg-bubble">
              <div className="aperture-indicator">
                <div className="aperture-ring" />
                <span>Analyzing</span>
              </div>
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* Input dock */}
      <div className="input-dock">
        <form className="input-row" onSubmit={submit}>
          <input
            ref={inputRef}
            type="text"
            className="input-field"
            placeholder={
              !hasSession
                ? 'Upload an image to start'
                : isProcessing
                ? 'Waiting for analysis…'
                : 'Ask about the image…'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(e); } }}
            disabled={!hasSession || isProcessing}
          />
          <button type="submit" className="btn-send"
            disabled={!input.trim() || isProcessing || !hasSession}>
            <svg viewBox="0 0 24 24">
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
