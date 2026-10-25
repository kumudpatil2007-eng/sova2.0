import React, { useState } from 'react';
import { Search, FileText, BookOpen, Database, Shield, CheckCircle2, Filter } from 'lucide-react';
import { knowledgeBaseDocuments } from '../data/knowledgeBase';

const categoryColors: Record<string, string> = {
  Operations: '#2563EB',
  Inspection: '#F59E0B',
  Maintenance: '#10B981',
  Safety: '#EF4444',
  Engineering: '#8B5CF6',
  Design: '#0D9488',
  Standards: '#64748B',
};

const KnowledgeBase: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = [...new Set(knowledgeBaseDocuments.map((d) => d.category))];

  const filtered = knowledgeBaseDocuments.filter((doc) => {
    const matchesSearch =
      !search ||
      doc.name.toLowerCase().includes(search.toLowerCase()) ||
      doc.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !selectedCategory || doc.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div style={{ maxWidth: 880, margin: '0 auto', padding: '32px 40px' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'rgba(37, 99, 235, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <BookOpen size={18} color="var(--color-accent)" />
          </div>
          <div>
            <h1
              style={{
                fontSize: 20,
                fontWeight: 750,
                color: 'var(--color-text-primary)',
                margin: 0,
                letterSpacing: '-0.02em',
              }}
            >
              Knowledge Base
            </h1>
            <p style={{ fontSize: 13, color: 'var(--color-text-tertiary)', margin: 0 }}>
              Organizational documents indexed for AI-powered retrieval
            </p>
          </div>
        </div>
      </div>

      {/* Search + Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div
          className="input-premium"
          style={{
            flex: 1,
            minWidth: 280,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 14px',
          }}
        >
          <Search size={16} color="var(--color-text-tertiary)" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search organizational knowledge..."
            style={{
              border: 'none',
              outline: 'none',
              background: 'transparent',
              flex: 1,
              fontSize: 13,
              color: 'var(--color-text-primary)',
              fontFamily: 'var(--font-sans)',
            }}
          />
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          <Filter size={14} color="var(--color-text-tertiary)" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
              style={{
                padding: '5px 12px',
                borderRadius: 20,
                border: '1px solid',
                borderColor:
                  selectedCategory === cat ? categoryColors[cat] || 'var(--color-accent)' : 'var(--color-border)',
                background:
                  selectedCategory === cat
                    ? `${categoryColors[cat]}10`
                    : 'var(--color-surface)',
                color:
                  selectedCategory === cat
                    ? categoryColors[cat]
                    : 'var(--color-text-secondary)',
                fontSize: 11.5,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div
        style={{
          display: 'flex',
          gap: 16,
          marginBottom: 20,
          padding: '12px 16px',
          borderRadius: 12,
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
          <Database size={13} color="var(--color-accent)" />
          <span style={{ color: 'var(--color-text-tertiary)' }}>Documents:</span>
          <span style={{ fontWeight: 700, color: 'var(--color-text-primary)' }}>{knowledgeBaseDocuments.length}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
          <CheckCircle2 size={13} color="#10B981" />
          <span style={{ color: 'var(--color-text-tertiary)' }}>Indexed:</span>
          <span style={{ fontWeight: 700, color: '#059669' }}>
            {knowledgeBaseDocuments.filter((d) => d.status === 'Indexed').length}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
          <Shield size={13} color="var(--color-teal)" />
          <span style={{ color: 'var(--color-text-tertiary)' }}>Source:</span>
          <span style={{ fontWeight: 700, color: 'var(--color-teal)' }}>Local Repository</span>
        </div>
      </div>

      {/* Document List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.map((doc) => (
          <div
            key={doc.id}
            className="card"
            style={{
              padding: '16px 20px',
              display: 'flex',
              gap: 16,
              alignItems: 'flex-start',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: `${categoryColors[doc.category] || 'var(--color-accent)'}10`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <FileText size={18} color={categoryColors[doc.category] || 'var(--color-accent)'} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 14, fontWeight: 650, color: 'var(--color-text-primary)' }}>
                  {doc.name}
                </span>
                <span
                  className="badge badge-success"
                  style={{ fontSize: 9, padding: '2px 8px' }}
                >
                  <span className="status-dot status-dot-green" style={{ width: 5, height: 5 }} />
                  {doc.status}
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-tertiary)', marginBottom: 6 }}>
                {doc.type} • {doc.pages} pages • {doc.size}
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', lineHeight: 1.5 }} className="line-clamp-2">
                {doc.description}
              </div>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', marginBottom: 4 }}>
                Updated
              </div>
              <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                {doc.lastUpdated}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KnowledgeBase;
