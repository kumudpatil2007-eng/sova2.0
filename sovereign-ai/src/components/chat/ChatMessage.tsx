import React, { useState } from 'react';
import Logo from '../common/Logo';
import {
  FileText,
  Image as ImageIcon,
  Table,
  File,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Cpu,
  FileSpreadsheet,
  AlertCircle,
  Copy,
  Check,
  Download
} from 'lucide-react';
import type { SourceCitation, GeneratedDocumentInfo } from '../../services/api';

export interface MessageItem {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  timestamp: string;
  model?: string;
  attachedFile?: {
    name: string;
    sizeFormatted: string;
    extension: string;
  };
  sources?: SourceCitation[];
  verification?: {
    is_verified: boolean;
    grounded: boolean;
    leak_count: number;
    verification_label?: string;
    notes?: string;
  };
  generated_document?: GeneratedDocumentInfo;
}

interface ChatMessageProps {
  message: MessageItem;
  onGenerateNote?: () => void;
  isGeneratingNote?: boolean;
}

function getFileIcon(ext: string) {
  const e = ext.toLowerCase();
  if (e === '.pdf') return <FileText size={14} color="#EF4444" />;
  if (['.png', '.jpg', '.jpeg', '.webp'].includes(e)) return <ImageIcon size={14} color="#F59E0B" />;
  if (['.csv', '.xlsx'].includes(e)) return <Table size={14} color="#10B981" />;
  return <File size={14} color="#2563EB" />;
}

// Lightweight Markdown renderer for engineering text
function renderMarkdownContent(content: string) {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockLines: string[] = [];

  lines.forEach((line, index) => {
    // Code block toggle
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        elements.push(
          <pre
            key={`code-${index}`}
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 8,
              padding: '10px 14px',
              overflowX: 'auto',
              fontSize: 12.5,
              fontFamily: 'var(--font-mono)',
              lineHeight: 1.5,
              margin: '8px 0',
              color: 'var(--color-text-primary)',
            }}
          >
            <code>{codeBlockLines.join('\n')}</code>
          </pre>
        );
        codeBlockLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      return;
    }

    // Headers
    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={index} style={{ fontSize: 14, fontWeight: 700, margin: '14px 0 6px', color: 'var(--color-text-primary)' }}>
          {formatInline(line.replace('### ', ''))}
        </h4>
      );
      return;
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h3 key={index} style={{ fontSize: 15, fontWeight: 750, margin: '18px 0 8px', color: 'var(--color-text-primary)', borderBottom: '1px solid var(--color-border-light)', paddingBottom: 4 }}>
          {formatInline(line.replace('## ', ''))}
        </h3>
      );
      return;
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={index} style={{ fontSize: 17, fontWeight: 800, margin: '20px 0 10px', color: 'var(--color-text-primary)' }}>
          {formatInline(line.replace('# ', ''))}
        </h2>
      );
      return;
    }

    // Bullet points
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      elements.push(
        <div key={index} style={{ display: 'flex', gap: 8, margin: '4px 0', paddingLeft: 8 }}>
          <span style={{ color: 'var(--color-accent)', fontWeight: 'bold' }}>•</span>
          <span style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--color-text-primary)' }}>
            {formatInline(line.trim().substring(2))}
          </span>
        </div>
      );
      return;
    }

    // Numbered list
    const numberedMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
    if (numberedMatch) {
      elements.push(
        <div key={index} style={{ display: 'flex', gap: 8, margin: '4px 0', paddingLeft: 8 }}>
          <span style={{ color: 'var(--color-accent)', fontWeight: 600, fontSize: 13 }}>{numberedMatch[1]}.</span>
          <span style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--color-text-primary)' }}>
            {formatInline(numberedMatch[2])}
          </span>
        </div>
      );
      return;
    }

    // Empty lines
    if (!line.trim()) {
      elements.push(<div key={index} style={{ height: 6 }} />);
      return;
    }

    // Standard paragraph
    elements.push(
      <p key={index} style={{ fontSize: 14, lineHeight: 1.65, margin: '6px 0', color: 'var(--color-text-primary)' }}>
        {formatInline(line)}
      </p>
    );
  });

  return elements;
}

// Inline formatting helper (**bold**, `code`)
function formatInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ fontWeight: 650, color: 'var(--color-text-primary)' }}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={i}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            background: 'var(--color-bg-secondary)',
            padding: '2px 5px',
            borderRadius: 4,
            border: '1px solid var(--color-border-light)',
          }}
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onGenerateNote,
  isGeneratingNote = false
}) => {
  const isUser = message.role === 'user';
  const isError = message.role === 'error';
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: 14,
        maxWidth: 780,
        width: '100%',
        margin: '0 auto',
        padding: '16px 0',
        animation: 'slide-up 0.3s ease-out',
        flexDirection: isUser ? 'row-reverse' : 'row',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: 10,
          background: isUser
            ? 'linear-gradient(135deg, #64748B, #475569)'
            : isError
            ? 'linear-gradient(135deg, #EF4444, #DC2626)'
            : 'linear-gradient(135deg, #2563EB, #0D9488)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: 2,
          boxShadow: 'var(--shadow-xs)',
        }}
      >
        {isUser ? (
          <span style={{ fontSize: 11, fontWeight: 700, color: 'white' }}>YOU</span>
        ) : isError ? (
          <AlertCircle size={18} color="white" />
        ) : (
          <Logo size={20} />
        )}
      </div>

      {/* Message Body */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header (sender & timestamp) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 6,
            justifyContent: isUser ? 'flex-end' : 'flex-start',
          }}
        >
          <span style={{ fontSize: 12.5, fontWeight: 650, color: 'var(--color-text-secondary)' }}>
            {isUser ? 'Engineer' : isError ? 'System Alert' : 'SOVA'}
          </span>
          {message.model && !isUser && (
            <span
              style={{
                fontSize: 10.5,
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-accent)',
                background: 'rgba(37, 99, 235, 0.08)',
                padding: '1px 6px',
                borderRadius: 4,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <Cpu size={10} /> {message.model}
            </span>
          )}
          {message.verification?.verification_label && !isUser && (
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                color: message.verification.is_verified ? '#059669' : '#D97706',
                background: message.verification.is_verified ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
                border: `1px solid ${message.verification.is_verified ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
                padding: '1px 6px',
                borderRadius: 4,
                letterSpacing: '0.03em',
              }}
              title={message.verification.notes || 'Evidence Grounding Verification'}
            >
              {message.verification.verification_label}
            </span>
          )}
          <span style={{ fontSize: 11, color: 'var(--color-text-tertiary)' }}>
            {message.timestamp}
          </span>
        </div>

        {/* User Attachment Pill */}
        {message.attachedFile && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 12px',
              borderRadius: 8,
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              fontSize: 12,
              fontWeight: 500,
              color: 'var(--color-text-primary)',
              marginBottom: 8,
              maxWidth: 'fit-content',
              marginLeft: isUser ? 'auto' : 0,
            }}
          >
            {getFileIcon(message.attachedFile.extension)}
            <span style={{ fontWeight: 600 }}>{message.attachedFile.name}</span>
            <span style={{ fontSize: 10.5, color: 'var(--color-text-tertiary)' }}>
              ({message.attachedFile.sizeFormatted})
            </span>
          </div>
        )}

        {/* Main Content Box */}
        <div
          style={{
            borderRadius: isUser ? 14 : 0,
            padding: isUser ? '12px 18px' : 0,
            background: isUser ? 'var(--color-surface)' : 'transparent',
            border: isUser ? '1px solid var(--color-border)' : 'none',
            boxShadow: isUser ? 'var(--shadow-xs)' : 'none',
          }}
        >
          {isError ? (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.06)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                borderRadius: 10,
                padding: '14px 18px',
                color: '#DC2626',
                fontSize: 13.5,
                lineHeight: 1.5,
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                <AlertCircle size={15} /> System Alert
              </div>
              <div style={{ color: 'var(--color-text-primary)', fontSize: 13 }}>
                {message.content}
              </div>
              {message.content.includes('qwen2.5vl:3b') && (
                <div
                  style={{
                    marginTop: 10,
                    padding: '8px 12px',
                    background: 'var(--color-surface)',
                    borderRadius: 6,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Run in terminal: <strong>ollama pull qwen2.5vl:3b</strong>
                </div>
              )}
            </div>
          ) : isUser ? (
            <span style={{ fontSize: 14, color: 'var(--color-text-primary)', whiteSpace: 'pre-wrap' }}>
              {message.content}
            </span>
          ) : (
            <div>
              {renderMarkdownContent(message.content)}
            </div>
          )}
        </div>

        {/* Generated Document Download Card */}
        {message.generated_document && (
          <div
            style={{
              marginTop: 14,
              borderRadius: 10,
              border: '1px solid rgba(37, 99, 235, 0.3)',
              background: 'var(--color-surface)',
              overflow: 'hidden',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
            }}
          >
            {/* Success Status Notice */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 16px',
                background: 'rgba(16, 185, 129, 0.08)',
                borderBottom: '1px solid rgba(16, 185, 129, 0.2)',
                fontSize: 12,
                fontWeight: 650,
                color: '#059669',
              }}
            >
              <Check size={14} />
              <span>Document generated successfully</span>
            </div>

            {/* Card Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                borderBottom: '1px solid var(--color-border)',
                background: 'rgba(37, 99, 235, 0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: 8,
                    background: 'rgba(37, 99, 235, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-accent)',
                  }}
                >
                  <FileText size={18} />
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13.5, color: 'var(--color-text-primary)' }}>
                    {message.generated_document.title}
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--color-text-tertiary)', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                    <span>
                      {message.generated_document.formats.map((f: string) => f.toUpperCase()).join(' & ')} Document
                    </span>
                    <span>•</span>
                    <span>{message.generated_document.page_count} {message.generated_document.page_count === 1 ? 'page' : 'pages'}</span>
                    <span>•</span>
                    <span style={{ color: '#10B981', fontWeight: 600 }}>100% On-Premise Air-Gapped</span>
                  </div>
                </div>
              </div>

              <span
                className="badge badge-blue"
                style={{ fontSize: 10, padding: '2px 8px', letterSpacing: '0.04em' }}
              >
                DOCUMENT READY
              </span>
            </div>

            {/* Card Action Buttons */}
            <div
              style={{
                padding: '12px 16px',
                display: 'flex',
                flexWrap: 'wrap',
                gap: 10,
                alignItems: 'center',
                background: 'var(--color-bg-secondary)',
              }}
            >
              {message.generated_document.files.docx && (
                <a
                  href={message.generated_document.files.docx.download_url}
                  download={message.generated_document.files.docx.filename}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 7,
                    padding: '7px 14px',
                    borderRadius: 6,
                    background: '#2563EB',
                    color: '#FFFFFF',
                    fontSize: 12,
                    fontWeight: 650,
                    textDecoration: 'none',
                    cursor: 'pointer',
                    transition: 'opacity 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
                >
                  <Download size={14} />
                  <span>Download DOCX</span>
                  <span style={{ opacity: 0.85, fontSize: 10.5, fontWeight: 500 }}>
                    ({message.generated_document.files.docx.size_formatted})
                  </span>
                </a>
              )}

              {message.generated_document.files.pdf && (
                <a
                  href={message.generated_document.files.pdf.download_url}
                  download={message.generated_document.files.pdf.filename}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 7,
                    padding: '7px 14px',
                    borderRadius: 6,
                    background: '#DC2626',
                    color: '#FFFFFF',
                    fontSize: 12,
                    fontWeight: 650,
                    textDecoration: 'none',
                    cursor: 'pointer',
                    transition: 'opacity 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
                >
                  <Download size={14} />
                  <span>Download PDF</span>
                  <span style={{ opacity: 0.85, fontSize: 10.5, fontWeight: 500 }}>
                    ({message.generated_document.files.pdf.size_formatted})
                  </span>
                </a>
              )}
            </div>
          </div>
        )}

        {/* Evidence / Sources Section */}
        {message.sources && message.sources.length > 0 && (
          <div
            style={{
              marginTop: 12,
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 10,
              overflow: 'hidden',
            }}
          >
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 14px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <BookOpen size={14} color="var(--color-accent)" />
                <span>Evidence & Citations ({message.sources.length} sources)</span>
              </div>
              {sourcesOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {sourcesOpen && (
              <div style={{ padding: '0 14px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                {message.sources.map((src, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'var(--color-bg-secondary)',
                      borderRadius: 8,
                      padding: '8px 12px',
                      fontSize: 12,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontWeight: 650, color: 'var(--color-text-primary)' }}>
                        📄 {src.name}
                      </span>
                      <span className="badge badge-teal" style={{ fontSize: 9.5, padding: '1px 6px' }}>
                        {src.relevance}
                      </span>
                    </div>
                    <div style={{ color: 'var(--color-text-secondary)', lineHeight: 1.45, fontStyle: 'italic', fontSize: 11.5 }}>
                      "{src.excerpt}"
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* AI Action Toolbar (Copy & Generate Engineering Note) */}
        {!isUser && !isError && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10 }}>
            <button
              onClick={handleCopy}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: 'none',
                border: '1px solid var(--color-border)',
                borderRadius: 6,
                padding: '4px 10px',
                fontSize: 11.5,
                color: 'var(--color-text-tertiary)',
                cursor: 'pointer',
              }}
              title="Copy response"
            >
              {copied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            {onGenerateNote && (
              <button
                onClick={onGenerateNote}
                disabled={isGeneratingNote}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  background: 'rgba(37, 99, 235, 0.08)',
                  border: '1px solid rgba(37, 99, 235, 0.25)',
                  borderRadius: 6,
                  padding: '4px 12px',
                  fontSize: 11.5,
                  fontWeight: 600,
                  color: 'var(--color-accent)',
                  cursor: isGeneratingNote ? 'default' : 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <FileSpreadsheet size={13} />
                <span>{isGeneratingNote ? 'Generating Note...' : 'Generate Engineering Note'}</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
