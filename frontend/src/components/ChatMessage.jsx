
export default function ChatMessage({ message }) {
  const { role, content, sosDetails, contextChunks, isLoading } = message;

  if (isLoading) {
    return (
      <div className="bg-surface-container-lowest border border-on-surface/5 border-l-4 border-l-secondary-container rounded-xl p-lg flex gap-md items-start max-w-3xl mt-md animate-fade-in-up">
        <div className="w-10 h-10 rounded-full bg-secondary-container/20 flex items-center justify-center shrink-0">
          <span className="material-symbols-outlined text-secondary">smart_toy</span>
        </div>
        <div className="flex flex-col gap-sm w-full pt-xs">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary text-sm animate-spin">progress_activity</span>
            <span className="font-label-md text-label-md text-on-surface-variant uppercase">Analyzing...</span>
          </div>
          <div className="space-y-unit mt-sm w-3/4">
            <div className="h-2 bg-surface-variant rounded w-full"></div>
            <div className="h-2 bg-surface-variant rounded w-5/6"></div>
            <div className="h-2 bg-surface-variant rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (role === 'user') {
    return (
      <div className="self-end bg-surface border border-on-surface/5 rounded-xl rounded-tr-none p-md max-w-2xl mt-md animate-fade-in-up">
        <p className="font-body-md text-body-md text-on-surface whitespace-pre-wrap">{content}</p>
      </div>
    );
  }

  return (
    <div className="bg-surface-container-lowest border border-on-surface/5 border-l-4 border-l-secondary-container rounded-xl p-lg flex gap-md items-start max-w-3xl animate-fade-in-up mt-md">
      <div className="w-10 h-10 rounded-full bg-secondary-container/20 flex items-center justify-center shrink-0">
        <span className="material-symbols-outlined text-secondary">{role === 'system' ? 'info' : 'smart_toy'}</span>
      </div>
      <div className="flex flex-col w-full">
        {role === 'system' && (
          <div className="flex flex-col gap-xs mb-md">
            <div className="font-label-md text-[10px] text-secondary uppercase tracking-[0.15em] font-bold">System Initialization</div>
            <p className="font-headline-md text-headline-md text-on-surface leading-tight">
              {content}
            </p>
          </div>
        )}

        {role === 'assistant' && sosDetails && sosDetails.is_sos && (
          <div className="bg-error-container text-on-error-container p-md rounded-lg mb-md font-label-md flex items-start gap-sm border-l-4 border-error">
            <span className="material-symbols-outlined text-error">warning</span>
            <span className="text-body-sm font-bold text-error">
              EMERGENCY ALERT: Potential critical symptoms detected ({sosDetails.matched_rules.join(', ')}). Please consult a physician immediately.
            </span>
          </div>
        )}

        {role === 'assistant' && (
          <div className="font-body-md text-body-md text-on-surface leading-relaxed whitespace-pre-wrap">{content}</div>
        )}

        {role === 'system' && (
          <div className="bg-secondary-container/10 border border-secondary/10 rounded-lg p-md">
            <p className="font-body-sm text-body-sm text-on-surface-variant flex gap-sm items-start">
              <span className="">Please remember I am an AI, not a doctor. Always consult a healthcare professional for medical advice or diagnostic confirmation.</span>
            </p>
          </div>
        )}

        {role === 'assistant' && contextChunks && contextChunks.length > 0 && (
          <details className="mt-md bg-surface-container-high p-sm rounded-lg border border-on-surface/5 text-sm">
            <summary className="cursor-pointer font-bold text-on-surface-variant select-none flex items-center gap-1">
              <span className="material-symbols-outlined text-sm">menu_book</span> View Retrieved Medical Context
            </summary>
            <div className="mt-sm text-on-surface-variant flex flex-col gap-sm text-xs">
              {contextChunks.map((c, i) => (
                <div key={i} className="bg-surface-container p-sm rounded border border-on-surface/5">
                  <strong>Document {i + 1}:</strong> {c.source || c.source_id}
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
