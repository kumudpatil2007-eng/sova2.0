import React, { useState, useRef, useEffect } from 'react';
import Logo from '../components/common/Logo';
import ChatInput, { type AttachedFileState, formatBytes } from '../components/chat/ChatInput';
import ChatMessage, { type MessageItem } from '../components/chat/ChatMessage';
import OutputPanel from '../components/output/OutputPanel';
import { useAuth } from '../context/AuthContext';
import {
  uploadDocument,
  sendChatMessageStream,
  generateEngineeringNote,
  loadSampleDocument,
  getSystemStatus,
  type SystemStatusResponse
} from '../services/api';
import {
  AlertTriangle,
  FileCheck,
  ShieldCheck,
  Cpu,
  RefreshCw,
  Check,
  Loader2
} from 'lucide-react';

interface WorkspaceProps {
  onRunDemo?: () => void;
}

interface PipelineStep {
  name: string;
  status: 'pending' | 'running' | 'done';
}

const Workspace: React.FC<WorkspaceProps> = () => {
  const { currentUser } = useAuth();
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [attachedFile, setAttachedFile] = useState<AttachedFileState | null>(null);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([]);

  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [isCheckingSystem, setIsCheckingSystem] = useState(false);

  const [showOutput, setShowOutput] = useState(false);
  const [generatedNote, setGeneratedNote] = useState<string | null>(null);
  const [isGeneratingNote, setIsGeneratingNote] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Poll system status on mount
  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    setIsCheckingSystem(true);
    try {
      const res = await getSystemStatus();
      setSystemStatus(res);
    } catch {
      setSystemStatus({
        ollama: false,
        model: 'qwen2.5vl:3b',
        model_available: false,
        available_models: [],
        external_calls: 0,
        inference: 'local',
        network: 'Offline',
        message: 'Backend API unreachable. Ensure FastAPI is running on port 8000.'
      });
    } finally {
      setIsCheckingSystem(false);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pipelineSteps]);

  // Handle file selected through native OS file dialog (Section 27)
  const handleFileSelect = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const newAttached: AttachedFileState = {
      file,
      name: file.name,
      sizeFormatted: formatBytes(file.size),
      extension: ext,
      uploadStatus: 'uploading'
    };

    setAttachedFile(newAttached);
    setIsProcessing(true);
    setPipelineSteps([
      { name: 'Reading document', status: 'running' },
      { name: 'Extracting relevant content', status: 'pending' },
      { name: 'Preparing local context', status: 'pending' },
    ]);

    try {
      const res = await uploadDocument(file);
      setActiveFileId(res.file_id);
      setAttachedFile({
        ...newAttached,
        uploadStatus: 'ready',
        fileId: res.file_id
      });
      setPipelineSteps([
        { name: 'Reading document', status: 'done' },
        { name: 'Extracting relevant content', status: 'done' },
        { name: 'Preparing local context', status: 'done' },
      ]);
    } catch (err: any) {
      setAttachedFile({
        ...newAttached,
        uploadStatus: 'error',
        error: err.message || 'Upload failed'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Preload real sample document
  const handleLoadSample = async () => {
    setIsProcessing(true);
    setPipelineSteps([
      { name: 'Reading document', status: 'running' },
      { name: 'Extracting relevant content', status: 'pending' },
      { name: 'Preparing local context', status: 'pending' },
    ]);

    try {
      const res = await loadSampleDocument();
      setActiveFileId(res.file_id);
      setAttachedFile({
        file: new File([], res.filename),
        name: res.filename,
        sizeFormatted: formatBytes(res.size),
        extension: '.pdf',
        uploadStatus: 'ready',
        fileId: res.file_id
      });

      // Add system confirmation message in chat
      setMessages((prev) => [
        ...prev,
        {
          id: `sample-${Date.now()}`,
          role: 'assistant',
          content: `**Document Ingested: ${res.filename}** (${res.total_pages} pages)\n\nNative inspection data extracted locally. Intelligent routing active. You can now ask questions about wall thickness, corrosion rate calculations, equipment specifications, or engineering recommendations.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model: systemStatus?.model || 'qwen2.5vl:3b'
        }
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'error',
          content: `Could not load sample document: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsProcessing(false);
      setPipelineSteps([]);
    }
  };

  // Handle sending a message with real-time token streaming (Section 13, 23)
  const handleSendMessage = async (text: string) => {
    if (!text && !attachedFile) return;

    let targetFileId = activeFileId;

    // 1. If file attached but not uploaded yet, upload now
    if (attachedFile && attachedFile.uploadStatus !== 'ready' && attachedFile.file) {
      setIsProcessing(true);
      setPipelineSteps([
        { name: 'Reading document', status: 'running' },
        { name: 'Extracting relevant content', status: 'pending' },
        { name: 'Preparing local context', status: 'pending' },
      ]);
      try {
        const uploadRes = await uploadDocument(attachedFile.file);
        targetFileId = uploadRes.file_id;
        setActiveFileId(targetFileId);
        setAttachedFile({ ...attachedFile, uploadStatus: 'ready', fileId: targetFileId });
      } catch (err: any) {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: 'error',
            content: `Failed to upload document: ${err.message}`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
        setIsProcessing(false);
        setPipelineSteps([]);
        return;
      }
    }

    const userMessage: MessageItem = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text || `Please analyze this attached document: ${attachedFile?.name}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachedFile: attachedFile ? {
        name: attachedFile.name,
        sizeFormatted: attachedFile.sizeFormatted,
        extension: attachedFile.extension
      } : undefined
    };

    const aiMessageId = `ai-${Date.now()}`;
    const initialAiMessage: MessageItem = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      model: systemStatus?.model || 'qwen2.5vl:3b'
    };

    setMessages((prev) => [...prev, userMessage, initialAiMessage]);
    setIsProcessing(true);

    // Initial real pipeline stages (Section 23)
    setPipelineSteps([
      { name: 'Reading document', status: 'running' },
      { name: 'Extracting relevant content', status: 'pending' },
      { name: 'Preparing local context', status: 'pending' },
      { name: 'Local inference', status: 'pending' },
    ]);

    const history = messages.slice(-4).map((m) => ({
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.content
    }));

    try {
      let accumulatedContent = '';
      await sendChatMessageStream(
        userMessage.content,
        targetFileId,
        history,
        {
          onStage: (_stage, step) => {
            setPipelineSteps((prev) =>
              prev.map((s, idx) => {
                if (idx < step - 1) return { ...s, status: 'done' };
                if (idx === step - 1) return { ...s, status: 'running' };
                return { ...s, status: 'pending' };
              })
            );
          },
          onToken: (token) => {
            accumulatedContent += token;
            // First token received: mark preparation steps done, local inference running
            setPipelineSteps([
              { name: 'Reading document', status: 'done' },
              { name: 'Extracting relevant content', status: 'done' },
              { name: 'Preparing local context', status: 'done' },
              { name: 'Local inference', status: 'running' },
            ]);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiMessageId ? { ...m, content: accumulatedContent } : m
              )
            );
          },
          onDone: (data) => {
            setPipelineSteps((prev) => prev.map((s) => ({ ...s, status: 'done' })));
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiMessageId
                  ? {
                      ...m,
                      model: data.model,
                      sources: data.sources,
                      verification: data.verification,
                      generated_document: data.generated_document,
                    }
                  : m
              )
            );
          },
          onError: (err) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiMessageId
                  ? {
                      ...m,
                      role: 'error',
                      content: err || 'Local AI engine error.',
                    }
                  : m
              )
            );
          }
        }
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId
            ? {
                ...m,
                role: 'error',
                content: err.message || 'Inference engine error occurred.',
              }
            : m
        )
      );
    } finally {
      setIsProcessing(false);
      setPipelineSteps([]);
    }
  };

  // Generate engineering note
  const handleGenerateNote = async () => {
    if (!activeFileId) {
      alert('Please upload or attach an engineering document first.');
      return;
    }

    setIsGeneratingNote(true);

    try {
      const res = await generateEngineeringNote(activeFileId);
      setGeneratedNote(res.note_markdown);
      setShowOutput(true);
    } catch (err: any) {
      alert(`Failed to generate engineering note: ${err.message}`);
    } finally {
      setIsGeneratingNote(false);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Main chat column */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          minWidth: 0,
        }}
      >
        {/* Ollama Status Warning Banner if Offline */}
        {systemStatus && !systemStatus.ollama && (
          <div
            style={{
              padding: '10px 24px',
              background: 'rgba(239, 68, 68, 0.08)',
              borderBottom: '1px solid rgba(239, 68, 68, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: 12.5,
              color: '#DC2626',
              flexShrink: 0,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertTriangle size={15} />
              <span>
                <strong>Local AI engine offline</strong>: Start Ollama (<code>ollama serve</code>) and ensure <code>qwen2.5vl:3b</code> is installed.
              </span>
            </div>
            <button
              onClick={checkStatus}
              disabled={isCheckingSystem}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: 'var(--color-surface)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 6,
                padding: '4px 10px',
                fontSize: 11.5,
                color: '#DC2626',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={12} className={isCheckingSystem ? 'animate-spin' : ''} />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Empty State / Welcome Screen */}
        {isEmpty ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px 24px',
              maxWidth: 820,
              margin: '0 auto',
              width: '100%',
            }}
          >
            {/* Branding Header */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                gap: 12,
                marginBottom: 32,
                animation: 'fade-in 0.4s ease-out',
              }}
            >
              <Logo size={52} />
              <h1
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: 'var(--color-text-primary)',
                  letterSpacing: '-0.03em',
                  margin: 0,
                  lineHeight: 1.1,
                }}
              >
                Hello, <span className="text-gradient">{currentUser?.name || 'Engineer'}</span>
              </h1>
              <p
                style={{
                  fontSize: 15,
                  color: 'var(--color-text-secondary)',
                  margin: 0,
                  fontWeight: 500,
                }}
              >
                {currentUser?.role ? `${currentUser.role} • ${currentUser.department}` : 'Your private engineering intelligence workspace.'}
              </p>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  padding: '6px 14px',
                  borderRadius: 20,
                  fontSize: 12,
                  color: 'var(--color-text-tertiary)',
                  marginTop: 6,
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#059669', fontWeight: 600 }}>
                  <ShieldCheck size={14} /> Air-Gapped Mode
                </span>
                <span>•</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontWeight: 600, color: 'var(--color-accent)' }}>
                  {currentUser?.clearanceCode || 'L3'} Clearance
                </span>
                <span>•</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <Cpu size={14} /> {systemStatus?.model || 'qwen2.5vl:3b'}
                </span>
                <span>•</span>
                <span>0 External Calls</span>
              </div>
            </div>

            {/* Chat Input in Center */}
            <div
              style={{
                width: '100%',
                maxWidth: 720,
                marginBottom: 24,
                animation: 'slide-up 0.4s ease-out 0.1s both',
              }}
            >
              <ChatInput
                onSend={handleSendMessage}
                attachedFile={attachedFile}
                onFileSelect={handleFileSelect}
                onRemoveFile={() => {
                  setAttachedFile(null);
                  setActiveFileId(null);
                }}
                disabled={isProcessing}
                placeholder="Ask about your engineering document or attach a file..."
              />
            </div>

            {/* Real Pipeline Status if Processing */}
            {isProcessing && pipelineSteps.length > 0 && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                  maxWidth: 420,
                  width: '100%',
                  margin: '0 auto 20px',
                  padding: '12px 18px',
                  borderRadius: 10,
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  fontSize: 12.5,
                }}
              >
                {pipelineSteps.map((step) => (
                  <div
                    key={step.name}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      color:
                        step.status === 'done'
                          ? '#059669'
                          : step.status === 'running'
                          ? 'var(--color-accent)'
                          : 'var(--color-text-tertiary)',
                    }}
                  >
                    <span>{step.name}</span>
                    <span>
                      {step.status === 'done' && <Check size={14} color="#10B981" />}
                      {step.status === 'running' && <Loader2 size={13} className="animate-spin" />}
                      {step.status === 'pending' && <span style={{ opacity: 0.4 }}>○</span>}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Quick Actions (Load Sample Inspection Report) */}
            <div
              style={{
                display: 'flex',
                gap: 12,
                flexWrap: 'wrap',
                justifyContent: 'center',
                maxWidth: 680,
                animation: 'slide-up 0.4s ease-out 0.2s both',
              }}
            >
              <button
                onClick={handleLoadSample}
                disabled={isProcessing}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '9px 16px',
                  borderRadius: 10,
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-primary)',
                  fontSize: 12.5,
                  fontWeight: 600,
                  cursor: isProcessing ? 'default' : 'pointer',
                  boxShadow: 'var(--shadow-xs)',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-accent)';
                  e.currentTarget.style.background = 'rgba(37, 99, 235, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                  e.currentTarget.style.background = 'var(--color-surface)';
                }}
              >
                <FileCheck size={16} color="var(--color-accent)" />
                <span>Load Sample Inspection Report (E-204 PDF)</span>
              </button>
            </div>
          </div>
        ) : (
          /* Active Chat Conversation */
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Message Stream */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '24px 32px',
              }}
            >
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onGenerateNote={activeFileId ? handleGenerateNote : undefined}
                  isGeneratingNote={isGeneratingNote}
                />
              ))}

              {/* Real Pipeline Stage Indicators (Section 23) */}
              {isProcessing && pipelineSteps.length > 0 && (
                <div
                  style={{
                    maxWidth: 780,
                    width: '100%',
                    margin: '12px auto',
                    padding: '12px 18px',
                    borderRadius: 10,
                    background: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    fontSize: 12.5,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                  }}
                >
                  {pipelineSteps.map((step) => (
                    <div
                      key={step.name}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        color:
                          step.status === 'done'
                            ? '#059669'
                            : step.status === 'running'
                            ? 'var(--color-accent)'
                            : 'var(--color-text-tertiary)',
                        fontWeight: step.status === 'running' ? 600 : 400,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                        {step.status === 'done' ? (
                          <Check size={13} color="#10B981" />
                        ) : step.status === 'running' ? (
                          <span
                            style={{
                              width: 7,
                              height: 7,
                              borderRadius: '50%',
                              background: '#2563EB',
                              boxShadow: '0 0 6px #2563EB',
                            }}
                          />
                        ) : (
                          <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#CBD5E1' }} />
                        )}
                        <span>{step.name}</span>
                      </div>
                      <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                        {step.status === 'done' && '✓'}
                        {step.status === 'running' && 'Running...'}
                        {step.status === 'pending' && 'Pending'}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Bottom Input Area */}
            <div
              style={{
                padding: '12px 32px 20px',
                borderTop: '1px solid var(--color-border-light)',
                background: 'var(--color-bg-primary)',
                flexShrink: 0,
              }}
            >
              <ChatInput
                onSend={handleSendMessage}
                attachedFile={attachedFile}
                onFileSelect={handleFileSelect}
                onRemoveFile={() => {
                  setAttachedFile(null);
                  setActiveFileId(null);
                }}
                disabled={isProcessing}
                placeholder="Ask about minimum thickness, corrosion rates, or calculations..."
              />
            </div>
          </div>
        )}
      </div>

      {/* Structured Engineering Note Drawer */}
      {showOutput && (
        <OutputPanel
          show={showOutput}
          noteMarkdown={generatedNote}
          filename={attachedFile?.name || 'Inspection_Report'}
          model={systemStatus?.model}
          onClose={() => setShowOutput(false)}
        />
      )}
    </div>
  );
};

export default Workspace;
