/**
 * ImageUpload.jsx — Glass dropzone + preset tiles.
 * All icons: custom SVG, 1.5px stroke, rounded joins, no emoji.
 */
import { useState, useRef } from 'react';

/* ── SVG Icons (unified 1.5px stroke family) ───────────────────── */
const UploadIcon = () => (
  <svg viewBox="0 0 24 24">
    <path d="M12 16V4" />
    <path d="M8 8l4-4 4 4" />
    <path d="M20 16v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-2" />
  </svg>
);

const HeartPulseIcon = () => (
  <svg viewBox="0 0 24 24">
    <path d="M3 12h4l3-9 4 18 3-9h4" />
  </svg>
);

const LayoutIcon = () => (
  <svg viewBox="0 0 24 24">
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <line x1="3" y1="9" x2="21" y2="9" />
    <line x1="9" y1="21" x2="9" y2="9" />
  </svg>
);

const FileTextIcon = () => (
  <svg viewBox="0 0 24 24">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="8" y1="13" x2="16" y2="13" />
    <line x1="8" y1="17" x2="13" y2="17" />
  </svg>
);

const FolderIcon = () => (
  <svg viewBox="0 0 24 24">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  </svg>
);

export default function ImageUpload({ onUpload, disabled }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = () => setIsDragOver(false);
  const handleDrop = (e) => {
    e.preventDefault(); setIsDragOver(false);
    if (e.dataTransfer.files?.[0]) onUpload(e.dataTransfer.files[0]);
  };
  const handleFileSelect = (e) => {
    if (e.target.files?.[0]) onUpload(e.target.files[0]);
  };

  const createSample = (type, title, filename) => {
    const c = document.createElement('canvas');
    c.width = 800; c.height = 500;
    const ctx = c.getContext('2d');
    const g = ctx.createLinearGradient(0,0,800,500);
    g.addColorStop(0,'#0B0A09'); g.addColorStop(1,'#1E1A16');
    ctx.fillStyle = g; ctx.fillRect(0,0,800,500);
    ctx.fillStyle = '#F3ECE3'; ctx.font = 'bold 24px sans-serif';
    ctx.fillText(title, 48, 60);
    ctx.fillStyle = '#A79C8E'; ctx.font = '14px sans-serif';
    if (type === 'medical') {
      ctx.fillText('Patient ID: MED-884920 · Modality: Chest X-Ray', 48, 100);
      ctx.strokeStyle = '#4F8F73'; ctx.lineWidth = 2;
      ctx.strokeRect(200,140,400,280);
      ctx.fillText('[Scan region]', 340, 290);
    } else if (type === 'ui') {
      ctx.fillText('Dashboard Workspace v2.4 · Status: Active', 48, 100);
      ctx.fillStyle = '#C17A4D'; ctx.fillRect(48,130,140,38);
      ctx.fillStyle = '#0B0A09'; ctx.font = '13px sans-serif';
      ctx.fillText('Primary Action', 72, 154);
      ctx.fillStyle = '#1E1A16'; ctx.fillRect(208,130,540,38);
    } else {
      ctx.fillText('INVOICE #INV-2026-00492 · Due: $1,450.00', 48, 100);
      ctx.fillStyle = '#6E655A'; ctx.fillRect(48,130,700,1);
    }
    c.toBlob(blob => onUpload(new File([blob], filename, { type: 'image/png' })));
  };

  return (
    <div>
      <div
        className={`dropzone ${isDragOver ? 'drag-active' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input ref={fileInputRef} type="file" accept="image/*"
          onChange={handleFileSelect} style={{ display: 'none' }} disabled={disabled} />

        <div className="dropzone-glyph"><UploadIcon /></div>
        <div className="dropzone-title">Drop your image here</div>
        <div className="dropzone-subtitle">or click to browse files</div>

        <div className="format-row">
          {['JPG','PNG','WEBP','TIFF','BMP'].map(f => (
            <span key={f} className="format-tag">{f}</span>
          ))}
        </div>
      </div>

      <div className="presets-section" style={{ marginTop: 12 }}>
        <span className="presets-label">Quick Test</span>
        <div className="presets-grid">
          <button className="preset-tile" disabled={disabled}
            onClick={() => createSample('medical','Medical Scan Sample','sample_xray.png')}>
            <HeartPulseIcon /><span>Medical scan</span>
          </button>
          <button className="preset-tile" disabled={disabled}
            onClick={() => createSample('ui','UI Dashboard','sample_ui.png')}>
            <LayoutIcon /><span>UI screenshot</span>
          </button>
          <button className="preset-tile" disabled={disabled}
            onClick={() => createSample('doc','Invoice Sample','sample_invoice.png')}>
            <FileTextIcon /><span>Document</span>
          </button>
          <button className="preset-tile" disabled={disabled}
            onClick={() => fileInputRef.current?.click()}>
            <FolderIcon /><span>Browse file</span>
          </button>
        </div>
      </div>
    </div>
  );
}
