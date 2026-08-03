/**
 * App.jsx — Imagio workspace shell.
 * Ambient background (film grain + copper glow blobs) + bento grid layout.
 */
import { useState, useCallback, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import ImageUpload from './components/ImageUpload';
import ImagePreview from './components/ImagePreview';
import ProcessingStatus from './components/ProcessingStatus';
import ChatInterface from './components/ChatInterface';
import { uploadImage, sendMessage, checkHealth } from './services/api';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [filename, setFilename] = useState('');
  const [category, setCategory] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [stages, setStages] = useState([]);
  const [currentStage, setCurrentStage] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  /* Health check */
  useEffect(() => {
    const check = async () => {
      try {
        const h = await checkHealth();
        setIsConnected(h.status === 'healthy');
      } catch { setIsConnected(false); }
    };
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, []);

  /* Upload */
  const handleUpload = useCallback(async (file) => {
    setIsUploading(true);
    try {
      const r = await uploadImage(file);
      setSessionId(r.session_id);
      setImageUrl(`http://localhost:8000${r.thumbnail_url}`);
      setFilename(r.original_filename);
      setCategory(null);
      setMessages([]);
      setStages([]);
      setStreamingContent('');
    } catch (err) { alert(`Upload failed: ${err.message}`); }
    finally { setIsUploading(false); }
  }, []);

  /* Remove */
  const handleRemove = useCallback(() => {
    setSessionId(null); setImageUrl(null); setFilename('');
    setCategory(null); setMessages([]); setStages([]);
    setStreamingContent(''); setCurrentStage('');
  }, []);

  /* Send message */
  const handleSend = useCallback(async (message) => {
    if (!sessionId) return;
    setMessages(p => [...p, { role: 'user', content: message }]);
    setIsProcessing(true);
    setStreamingContent('');
    setStages([]);

    let acc = '';
    await sendMessage(sessionId, message, {
      onStage: (s) => { setStages(p => [...p, s]); setCurrentStage(s); },
      onToken: (t) => { acc += t; setStreamingContent(acc); },
      onDone: (cat) => {
        if (cat) setCategory(cat);
        if (acc) {
          const final = acc; acc = '';
          setMessages(p => [...p, { role: 'assistant', content: final }]);
          setStreamingContent('');
        }
        setIsProcessing(false);
        setCurrentStage('complete');
      },
      onError: (msg) => {
        setMessages(p => [...p, { role: 'assistant', content: `Error: ${msg}` }]);
        setIsProcessing(false);
        setStreamingContent('');
      },
    });
  }, [sessionId]);

  return (
    <>
      {/* Ambient background — film grain + copper glows */}
      <div className="bg-ambient">
        <div className="bg-glow-a" />
        <div className="bg-glow-b" />
      </div>

      <div className="app-shell">
        <Header isConnected={isConnected} />

        <div className="workspace">
          {/* Control surface */}
          <div className="panel-left">
            {!imageUrl ? (
              <ImageUpload onUpload={handleUpload} disabled={isUploading} />
            ) : (
              <ImagePreview imageUrl={imageUrl} filename={filename}
                category={category} onRemove={handleRemove} />
            )}
            {stages.length > 0 && (
              <ProcessingStatus stages={stages} currentStage={currentStage} />
            )}
          </div>

          {/* Conversation workspace */}
          <div className="panel-right">
            <ChatInterface
              messages={messages} onSendMessage={handleSend}
              isProcessing={isProcessing} streamingContent={streamingContent}
              hasSession={!!sessionId}
            />
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
