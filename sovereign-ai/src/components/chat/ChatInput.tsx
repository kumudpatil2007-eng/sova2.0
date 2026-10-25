import React, { useState, useRef } from 'react';
import { Send, Paperclip, FileText, Image as ImageIcon, Table, File, X, CheckCircle2, Loader2 } from 'lucide-react';

export interface AttachedFileState {
  file: File;
  name: string;
  sizeFormatted: string;
  extension: string;
  uploadStatus?: 'pending' | 'uploading' | 'ready' | 'error';
  fileId?: string;
  error?: string;
}

interface ChatInputProps {
  onSend: (message: string, attachedFile?: AttachedFileState | null) => void;
  attachedFile?: AttachedFileState | null;
  onFileSelect?: (file: File) => void;
  onRemoveFile?: () => void;
  disabled?: boolean;
  placeholder?: string;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function getFileIcon(ext: string) {
  const e = ext.toLowerCase();
  if (e === '.pdf') return <FileText size={16} color="#EF4444" />;
  if (['.png', '.jpg', '.jpeg', '.webp'].includes(e)) return <ImageIcon size={16} color="#F59E0B" />;
  if (['.csv', '.xlsx', '.xls'].includes(e)) return <Table size={16} color="#10B981" />;
  return <File size={16} color="#2563EB" />;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  attachedFile = null,
  onFileSelect,
  onRemoveFile,
  disabled = false,
  placeholder = 'Ask about your engineering document...'
}) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAttachClick = () => {
    if (disabled) return;
    // Trigger real OS native file picker
    fileInputRef.current?.click();
  };

  const handleNativeFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onFileSelect) {
      onFileSelect(file);
    }
  };

  const handleSend = () => {
    if ((value.trim() || attachedFile) && !disabled) {
      onSend(value.trim(), attachedFile);
      setValue('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const autoResize = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 140) + 'px';
    }
  };

  const hasContent = value.trim().length > 0 || !!attachedFile;

  return (
    <div
      style={{
        maxWidth: 760,
        width: '100%',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      {/* Hidden real native HTML file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.webp,.csv,.txt,.docx,.xlsx"
        style={{ display: 'none' }}
        onChange={handleNativeFileChange}
      />

      {/* Selected File Card Pill */}
      {attachedFile && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 12,
            padding: '8px 14px',
            boxShadow: 'var(--shadow-xs)',
            animation: 'slide-up 0.2s ease-out',
            gap: 12,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
            {getFileIcon(attachedFile.extension)}
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  maxWidth: 420,
                }}
              >
                {attachedFile.name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', display: 'flex', gap: 8 }}>
                <span>{attachedFile.sizeFormatted}</span>
                {attachedFile.uploadStatus === 'uploading' && (
                  <span style={{ color: 'var(--color-accent)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Loader2 size={11} className="animate-spin" /> Uploading & Extracting...
                  </span>
                )}
                {attachedFile.uploadStatus === 'ready' && (
                  <span style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 500 }}>
                    <CheckCircle2 size={11} /> Document Processed
                  </span>
                )}
                {attachedFile.uploadStatus === 'error' && (
                  <span style={{ color: '#DC2626' }}>
                    {attachedFile.error || 'Upload error'}
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={() => {
              if (fileInputRef.current) fileInputRef.current.value = '';
              if (onRemoveFile) onRemoveFile();
            }}
            disabled={disabled}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-tertiary)',
              cursor: disabled ? 'default' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 4,
              borderRadius: 6,
              transition: 'background 0.15s, color 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
              e.currentTarget.style.color = '#EF4444';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'none';
              e.currentTarget.style.color = 'var(--color-text-tertiary)';
            }}
            title="Remove attached document"
          >
            <X size={15} />
          </button>
        </div>
      )}

      {/* Main Composer Box */}
      <div
        className="input-premium"
        style={{
          display: 'flex',
          flexDirection: 'column',
          padding: '10px 14px 10px 16px',
          width: '100%',
          boxSizing: 'border-box',
          gap: 6,
        }}
      >
        {/* Text input area */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            autoResize();
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          rows={1}
          style={{
            width: '100%',
            resize: 'none',
            border: 'none',
            outline: 'none',
            background: 'transparent',
            fontSize: 14.5,
            lineHeight: 1.5,
            color: 'var(--color-text-primary)',
            fontFamily: 'var(--font-sans)',
            padding: '4px 0',
            maxHeight: 140,
          }}
        />

        {/* Action buttons row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: 4,
          }}
        >
          {/* Attach Button triggering real OS file picker */}
          <button
            type="button"
            onClick={handleAttachClick}
            disabled={disabled}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              padding: '6px 12px',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg-secondary)',
              color: 'var(--color-text-secondary)',
              fontSize: 12.5,
              fontWeight: 600,
              cursor: disabled ? 'default' : 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              if (!disabled) {
                e.currentTarget.style.background = 'var(--color-surface)';
                e.currentTarget.style.borderColor = 'var(--color-accent)';
                e.currentTarget.style.color = 'var(--color-accent)';
              }
            }}
            onMouseLeave={(e) => {
              if (!disabled) {
                e.currentTarget.style.background = 'var(--color-bg-secondary)';
                e.currentTarget.style.borderColor = 'var(--color-border)';
                e.currentTarget.style.color = 'var(--color-text-secondary)';
              }
            }}
          >
            <Paperclip size={14} />
            <span>Attach Document</span>
          </button>

          {/* Send Button */}
          <button
            type="button"
            onClick={handleSend}
            disabled={!hasContent || disabled}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 36,
              height: 36,
              borderRadius: 10,
              border: 'none',
              background:
                hasContent && !disabled
                  ? 'linear-gradient(135deg, #2563EB, #1D4ED8)'
                  : 'var(--color-bg-secondary)',
              color: hasContent && !disabled ? 'white' : 'var(--color-text-tertiary)',
              cursor: hasContent && !disabled ? 'pointer' : 'default',
              transition: 'all 0.2s',
              boxShadow:
                hasContent && !disabled ? '0 2px 8px rgba(37, 99, 235, 0.3)' : 'none',
            }}
            title="Send query"
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
export { formatBytes };
