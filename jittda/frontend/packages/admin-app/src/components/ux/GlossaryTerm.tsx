import { useState, useRef, useEffect, type ReactNode } from 'react';

export interface GlossaryTermProps {
  term: string;
  explanation: string;
  children: ReactNode;
}

export function GlossaryTerm({ term, explanation, children }: GlossaryTermProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState<'top' | 'bottom'>('top');
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isVisible && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      // If there's not enough space above, show below
      if (rect.top < 100) {
        setPosition('bottom');
      } else {
        setPosition('top');
      }
    }
  }, [isVisible]);

  return (
    <span className="relative inline-block">
      <span
        ref={triggerRef}
        className="border-b border-dotted border-gray-400 text-[--color-text-primary] cursor-help"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        tabIndex={0}
        role="term"
        aria-label={`${term}: ${explanation}`}
      >
        {children}
      </span>

      {isVisible && (
        <div
          ref={tooltipRef}
          role="tooltip"
          className={`
            absolute z-50 w-64 px-3 py-2 rounded-lg shadow-lg
            bg-gray-900 text-white text-xs leading-relaxed
            pointer-events-none
            ${position === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'}
            left-1/2 -translate-x-1/2
          `}
        >
          <p className="font-semibold text-blue-300 mb-1">{term}</p>
          <p>{explanation}</p>
          {/* Arrow */}
          <div
            className={`
              absolute left-1/2 -translate-x-1/2 w-0 h-0
              border-x-[6px] border-x-transparent
              ${
                position === 'top'
                  ? 'top-full border-t-[6px] border-t-gray-900'
                  : 'bottom-full border-b-[6px] border-b-gray-900'
              }
            `}
          />
        </div>
      )}
    </span>
  );
}
