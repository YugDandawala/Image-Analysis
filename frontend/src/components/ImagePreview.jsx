/**
 * ImagePreview.jsx — Glass-framed image preview with jade domain ribbon.
 * Remove button: ghost at rest, oxblood on hover.
 */
export default function ImagePreview({ imageUrl, filename, category, onRemove }) {
  const domainLabels = {
    medical: 'Medical',
    ui_screenshot: 'Interface',
    document: 'Document',
    general: 'Photograph',
  };

  return (
    <div className="preview-frame">
      <div className="preview-viewport">
        <img src={imageUrl} alt={filename} className="preview-img" />
        {category && (
          <div className="domain-ribbon">
            {domainLabels[category] || category}
          </div>
        )}
      </div>

      <div className="preview-bar">
        <div>
          <div className="file-name" title={filename}>{filename}</div>
          <div className="file-domain">
            {category ? domainLabels[category] : 'Analyzing…'}
          </div>
        </div>
        <button className="btn-remove" onClick={onRemove}>Remove</button>
      </div>
    </div>
  );
}
