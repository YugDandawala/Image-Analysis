/**
 * ProcessingStatus.jsx — Connected vertical timeline with animated step nodes.
 * Active: copper breathing dot. Completed: jade fill + thin check SVG.
 * No system names — just clean stage labels from the backend.
 */

/* Check SVG icon for completed steps */
const CheckIcon = () => (
  <svg viewBox="0 0 12 12">
    <polyline points="2.5 6 5 8.5 9.5 3.5" />
  </svg>
);

export default function ProcessingStatus({ stages, currentStage }) {
  return (
    <div className="timeline-card">
      <div className="timeline-heading">Pipeline Progress</div>

      <div className="timeline-track">
        {stages.map((stage, i) => {
          const isActive = stage === currentStage && currentStage !== 'complete';
          const isDone = currentStage === 'complete' || i < stages.indexOf(currentStage);

          let cls = 'timeline-step';
          if (isDone) cls += ' done';
          else if (isActive) cls += ' active';

          return (
            <div key={i} className={cls}>
              <div className="step-node">
                {isDone && <CheckIcon />}
              </div>
              <span className="step-label">{stage}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
