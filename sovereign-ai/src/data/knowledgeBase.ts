export interface KBDocument {
  id: string;
  name: string;
  type: string;
  category: string;
  status: 'Indexed' | 'Pending' | 'Processing';
  source: string;
  size: string;
  pages: number;
  lastUpdated: string;
  description: string;
}

export const knowledgeBaseDocuments: KBDocument[] = [
  {
    id: 'kb-1',
    name: 'Corrosion Monitoring SOP',
    type: 'Standard Operating Procedure',
    category: 'Operations',
    status: 'Indexed',
    source: 'Local Repository',
    size: '856 KB',
    pages: 34,
    lastUpdated: '2026-08-15',
    description: 'Standard operating procedure for corrosion monitoring across CDU-1, VDU, and HDS units. Covers inspection intervals, acceptance criteria, and escalation procedures.',
  },
  {
    id: 'kb-2',
    name: 'Equipment Inspection Manual',
    type: 'Technical Manual',
    category: 'Inspection',
    status: 'Indexed',
    source: 'Local Repository',
    size: '4.2 MB',
    pages: 186,
    lastUpdated: '2026-07-22',
    description: 'Comprehensive inspection manual covering all static equipment, pressure vessels, heat exchangers, and piping systems within the refinery complex.',
  },
  {
    id: 'kb-3',
    name: 'Equipment Maintenance Manual — E-Series',
    type: 'Technical Manual',
    category: 'Maintenance',
    status: 'Indexed',
    source: 'Local Repository',
    size: '3.1 MB',
    pages: 142,
    lastUpdated: '2026-06-10',
    description: 'Maintenance procedures, material specifications, and design parameters for all E-series heat exchangers including E-201 through E-212.',
  },
  {
    id: 'kb-4',
    name: 'Safety Procedures — Hot Work & Confined Space',
    type: 'Safety Document',
    category: 'Safety',
    status: 'Indexed',
    source: 'Local Repository',
    size: '1.4 MB',
    pages: 56,
    lastUpdated: '2026-09-01',
    description: 'Safety procedures for hot work permits, confined space entry, and associated risk assessments. Aligned with OISD-GDN-196 and IS-3016.',
  },
  {
    id: 'kb-5',
    name: 'Past Engineering Correspondence',
    type: 'Correspondence Archive',
    category: 'Engineering',
    status: 'Indexed',
    source: 'Local Repository',
    size: '12.6 MB',
    pages: 342,
    lastUpdated: '2026-09-18',
    description: 'Archive of engineering notes, technical queries, design review comments, and inter-departmental correspondence from the past 24 months.',
  },
  {
    id: 'kb-6',
    name: 'P&ID Master Set — CDU-1',
    type: 'Engineering Drawing',
    category: 'Design',
    status: 'Indexed',
    source: 'Local Repository',
    size: '28.4 MB',
    pages: 48,
    lastUpdated: '2026-05-20',
    description: 'Complete set of piping and instrumentation diagrams for the Crude Distillation Unit, including all revisions up to Rev.12.',
  },
  {
    id: 'kb-7',
    name: 'API-579-1 Assessment Guidelines',
    type: 'Engineering Standard',
    category: 'Standards',
    status: 'Indexed',
    source: 'Local Repository',
    size: '5.8 MB',
    pages: 892,
    lastUpdated: '2026-01-15',
    description: 'Fitness-for-service assessment guidelines per API-579-1 / ASME FFS-1. Covers general metal loss, local metal loss, pitting, and crack-like flaws.',
  },
  {
    id: 'kb-8',
    name: 'Previous Inspection Reports Archive',
    type: 'Inspection Archive',
    category: 'Inspection',
    status: 'Indexed',
    source: 'Local Repository',
    size: '45.2 MB',
    pages: 1240,
    lastUpdated: '2026-09-20',
    description: 'Historical archive of all inspection reports (UTM, MPI, RT, VT) for static equipment. Includes trend data and analyst observations.',
  },
];
