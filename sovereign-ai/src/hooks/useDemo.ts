import { useState, useCallback, useRef } from 'react';
import {
  demoUserMessage,
  demoProcessingSteps,
  demoFindings,
  demoSources,
  type DemoMessage,
  type ProcessingStep,
} from '../data/demoConversation';

export type DemoPhase =
  | 'idle'
  | 'user-message'
  | 'typing'
  | 'processing'
  | 'findings'
  | 'complete';

export function useDemo() {
  const [phase, setPhase] = useState<DemoPhase>('idle');
  const [messages, setMessages] = useState<DemoMessage[]>([]);
  const [currentSteps, setCurrentSteps] = useState<ProcessingStep[]>([]);
  const [showOutput, setShowOutput] = useState(false);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimeouts = () => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  };

  const addTimeout = (fn: () => void, ms: number) => {
    const id = setTimeout(fn, ms);
    timeoutsRef.current.push(id);
    return id;
  };

  const runDemo = useCallback(() => {
    clearTimeouts();
    setMessages([]);
    setCurrentSteps([]);
    setShowOutput(false);

    // Phase 1: User message appears
    setPhase('user-message');
    setMessages([demoUserMessage]);

    // Phase 2: Typing indicator
    addTimeout(() => {
      setPhase('typing');
    }, 1200);

    // Phase 3: Processing steps appear one by one
    addTimeout(() => {
      setPhase('processing');

      const steps = [...demoProcessingSteps];

      steps.forEach((_, index) => {
        // Set processing status
        addTimeout(() => {
          setCurrentSteps(() => {
            const updated = [...demoProcessingSteps.map((s, i) => ({
              ...s,
              status: i < index ? 'complete' as const : i === index ? 'processing' as const : 'pending' as const,
            }))];
            return updated;
          });
        }, index * 700);

        // Set complete status
        addTimeout(() => {
          setCurrentSteps(() => {
            const updated = [...demoProcessingSteps.map((s, i) => ({
              ...s,
              status: i <= index ? 'complete' as const : 'pending' as const,
            }))];
            return updated;
          });
        }, index * 700 + 500);
      });

      // Phase 4: Show findings after all steps
      const totalStepTime = steps.length * 700 + 600;
      addTimeout(() => {
        setPhase('findings');
        setMessages([
          demoUserMessage,
          {
            id: 'demo-ai-1',
            role: 'ai',
            content: '',
            processingSteps: demoProcessingSteps.map((s) => ({ ...s, status: 'complete' as const })),
            findings: demoFindings,
            sources: demoSources,
            attachments: undefined,
            timestamp: '10:24 AM',
          },
        ]);
      }, totalStepTime);

      // Phase 5: Show output panel
      addTimeout(() => {
        setPhase('complete');
        setShowOutput(true);
      }, totalStepTime + 1000);
    }, 2500);
  }, []);

  const reset = useCallback(() => {
    clearTimeouts();
    setPhase('idle');
    setMessages([]);
    setCurrentSteps([]);
    setShowOutput(false);
  }, []);

  return {
    phase,
    messages,
    currentSteps,
    showOutput,
    setShowOutput,
    runDemo,
    reset,
    isDemoActive: phase !== 'idle',
  };
}
