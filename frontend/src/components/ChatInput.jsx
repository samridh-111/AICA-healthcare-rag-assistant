import { useState, useRef } from 'react';

export default function ChatInput({ onSend }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleInput = (e) => {
    setInput(e.target.value);
    e.target.style.height = '';
    e.target.style.height = e.target.scrollHeight + 'px';
  };

  const handleSend = () => {
    if (input.trim()) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = '';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="shrink-0 bg-surface-bright pb-xl pt-md px-margin-desktop w-full border-t border-on-surface/5">
      <div className="max-w-4xl mx-auto relative group">
        <div className="absolute inset-0 bg-primary-container/5 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none scale-105"></div>
        <div className="relative flex items-end gap-sm bg-surface-container-lowest border border-on-surface/10 rounded-xl p-sm shadow-[0_4px_16px_rgba(14,4,4,0.02)] focus-within:border-primary focus-within:shadow-[0_0_0_2px_rgba(204,73,68,0.1)] transition-all duration-200">
          <textarea
            ref={textareaRef}
            className="w-full bg-transparent border-none focus:ring-0 resize-none font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant/50 py-sm min-h-[44px] max-h-[200px]"
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask a health-related question... (e.g., 'What are the symptoms of asthma?')"
            rows="1"
          />
          <button
            onClick={handleSend}
            className="bg-primary text-on-primary h-10 w-10 rounded-lg flex items-center justify-center shrink-0 hover:bg-on-primary-fixed-variant transition-colors shadow-sm self-end mb-xs mr-xs"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px', fontWeight: 600 }}>arrow_upward</span>
          </button>
        </div>
        <div className="text-center mt-sm">
          <p className="font-label-md text-label-md text-on-surface-variant/60 uppercase">Healthcare AI Assistant can make mistakes. Verify important information.</p>
        </div>
      </div>
    </div>
  );
}
