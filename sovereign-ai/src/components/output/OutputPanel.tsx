import React, { useState } from 'react';
import { X, Download, Copy, Check, FileSpreadsheet } from 'lucide-react';
import { exportToWord } from '../../utils/exportWord';
import { exportToPdf } from '../../utils/exportPdf';

interface OutputPanelProps {
  show: boolean;
  onClose: () => void;
  noteMarkdown?: string | null;
  filename?: string;
  model?: string;
}

const OutputPanel: React.FC<OutputPanelProps> = ({
  show,
  onClose,
  noteMarkdown,
  filename = 'Inspection_Report',
  model = 'qwen2.5vl:3b'
}) => {
  const [copied, setCopied] = useState(false);

  if (!show) return null;

  const content = noteMarkdown || `# ENGINEERING NOTE: ${filename}\n\nNo engineering note generated yet. Click "Generate Engineering Note" on any model response.`;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMd = () => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Engineering_Note_${filename.replace(/\.[^/.]+$/, "")}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownloadDocx = () => {
    exportToWord(`Engineering_Note_${filename.replace(/\.[^/.]+$/, "")}`, content);
  };

  const handleDownloadPdf = () => {
    exportToPdf(`Engineering_Note_${filename.replace(/\.[^/.]+$/, "")}`, content);
  };

  return (
    <div
      style={{
        width: 440,
        minWidth: 440,
        height: '100%',
        background: 'var(--color-surface)',
        borderLeft: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        animation: 'slide-right 0.25s ease-out',
        overflow: 'hidden',
        zIndex: 20,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'rgba(37, 99, 235, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <FileSpreadsheet size={16} color="var(--color-accent)" />
          </div>
          <div>
            <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Engineering Note
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', fontFamily: 'var(--font-mono)' }}>
              Model: {model} (Local)
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            width: 28,
            height: 28,
            borderRadius: 7,
            border: 'none',
            background: 'var(--color-bg-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-text-secondary)',
          }}
          title="Close panel"
        >
          <X size={15} />
        </button>
      </div>

      {/* Action Bar */}
      <div
        style={{
          padding: '10px 20px',
          borderBottom: '1px solid var(--color-border-light)',
          background: 'var(--color-bg-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          {filename}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={handleCopy}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              fontSize: 11.5,
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              cursor: 'pointer',
              color: 'var(--color-text-secondary)',
            }}
          >
            {copied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            onClick={handleDownloadMd}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              fontSize: 11,
              fontWeight: 600,
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
            title="Download as Markdown"
          >
            <Download size={11} />
            <span>.md</span>
          </button>
          <button
            onClick={handleDownloadDocx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              fontSize: 11,
              fontWeight: 600,
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
            title="Download as Word Document (.docx)"
          >
            <FileSpreadsheet size={11} color="#2563EB" />
            <span>.docx</span>
          </button>
          <button
            onClick={handleDownloadPdf}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              fontSize: 11,
              fontWeight: 600,
              borderRadius: 6,
              border: 'none',
              background: 'var(--color-accent)',
              color: 'white',
              cursor: 'pointer',
            }}
            title="Download as PDF Report"
          >
            <Download size={11} />
            <span>.pdf</span>
          </button>
        </div>
      </div>

      {/* Note Content View */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px 24px',
          fontSize: 13.5,
          lineHeight: 1.65,
          color: 'var(--color-text-primary)',
          whiteSpace: 'pre-wrap',
          fontFamily: 'var(--font-sans)',
        }}
      >
        {content}
      </div>
    </div>
  );
};

export default OutputPanel;
