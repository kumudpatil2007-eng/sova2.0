export interface Analysis {
  id: string;
  title: string;
  description: string;
  status: 'Completed' | 'In Progress' | 'Pending Review';
  date: string;
  time: string;
  documentsUsed: number;
  deliverable: string;
  confidence: number;
}

export const analysisHistory: Analysis[] = [
  {
    id: 'analysis-1',
    title: 'Heat Exchanger E-204 — Inspection Assessment',
    description: 'Fitness-for-service assessment based on UTM inspection data. Generated engineering approval note.',
    status: 'Completed',
    date: '22 Sep 2026',
    time: '10:24 AM',
    documentsUsed: 3,
    deliverable: 'Engineering Approval Note (EN-2026-0847)',
    confidence: 94,
  },
  {
    id: 'analysis-2',
    title: 'P&ID Equipment Extraction — CDU-1',
    description: 'Extracted 142 equipment tags, 86 instrument tags and 34 valve identifiers from CDU-1 P&ID set.',
    status: 'Completed',
    date: '20 Sep 2026',
    time: '2:15 PM',
    documentsUsed: 6,
    deliverable: 'Equipment Tag Register (Excel)',
    confidence: 91,
  },
  {
    id: 'analysis-3',
    title: 'Vibration Analysis — Pump P-301A',
    description: 'Analyzed vibration spectra from recent condition monitoring. Identified bearing wear pattern.',
    status: 'Completed',
    date: '18 Sep 2026',
    time: '11:40 AM',
    documentsUsed: 2,
    deliverable: 'Condition Assessment Report',
    confidence: 88,
  },
  {
    id: 'analysis-4',
    title: 'Inspection Report Review — Column C-101',
    description: 'Cross-referenced inspection findings against historical data and generated trend analysis.',
    status: 'Completed',
    date: '15 Sep 2026',
    time: '4:52 PM',
    documentsUsed: 5,
    deliverable: 'Corrosion Trend Report',
    confidence: 92,
  },
  {
    id: 'analysis-5',
    title: 'Safety Valve Recertification — PSV-204A/B',
    description: 'Reviewed test certificates and verified set pressure compliance against design basis.',
    status: 'Completed',
    date: '12 Sep 2026',
    time: '9:30 AM',
    documentsUsed: 4,
    deliverable: 'Compliance Verification Note',
    confidence: 97,
  },
];
