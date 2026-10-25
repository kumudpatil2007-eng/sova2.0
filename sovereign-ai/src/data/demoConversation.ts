export interface DemoMessage {
  id: string;
  role: 'user' | 'ai' | 'system';
  content: string;
  attachments?: DemoAttachment[];
  processingSteps?: ProcessingStep[];
  findings?: InspectionFindings;
  sources?: Source[];
  timestamp: string;
}

export interface DemoAttachment {
  name: string;
  type: 'pdf' | 'image' | 'document' | 'csv' | 'pid';
  size: string;
}

export interface ProcessingStep {
  id: string;
  label: string;
  status: 'pending' | 'processing' | 'complete';
  detail?: string;
}

export interface InspectionFindings {
  equipment: string;
  inspectionType: string;
  findings: { label: string; value: string; status?: 'normal' | 'warning' | 'critical' }[];
  riskLevel: string;
  riskExplanation: string;
}

export interface Source {
  name: string;
  type: string;
  relevance: string;
}

export const demoAttachments: DemoAttachment[] = [
  { name: 'Inspection_Report_E204.pdf', type: 'pdf', size: '2.4 MB' },
  { name: 'E204_Inspection_Photo.jpg', type: 'image', size: '1.8 MB' },
  { name: 'Maintenance_SOP_Rev3.pdf', type: 'document', size: '856 KB' },
];

export const demoProcessingSteps: ProcessingStep[] = [
  { id: 'parse', label: 'Document parsed', status: 'pending', detail: '3 files ingested' },
  { id: 'ocr', label: 'OCR completed', status: 'pending', detail: '24 pages processed' },
  { id: 'extract', label: 'Engineering parameters extracted', status: 'pending', detail: '47 data points' },
  { id: 'sop', label: 'Relevant SOP retrieved', status: 'pending', detail: 'Maintenance SOP Rev.3' },
  { id: 'validate', label: 'Findings validated against limits', status: 'pending', detail: 'API-579 / ASME B31.3' },
  { id: 'generate', label: 'Approval note generated', status: 'pending', detail: 'Engineering Note EN-2026-0847' },
];

export const demoFindings: InspectionFindings = {
  equipment: 'Heat Exchanger E-204',
  inspectionType: 'Ultrasonic Thickness Measurement (UTM)',
  findings: [
    { label: 'Minimum Measured Thickness', value: '8.2 mm', status: 'warning' },
    { label: 'Nominal Thickness', value: '10.0 mm', status: 'normal' },
    { label: 'Corrosion Allowance Remaining', value: '1.2 mm', status: 'warning' },
    { label: 'Corrosion Loss', value: '18%', status: 'warning' },
    { label: 'Inspection Points Analyzed', value: '24', status: 'normal' },
    { label: 'Corrosion Rate', value: '0.15 mm/year', status: 'normal' },
    { label: 'Estimated Remaining Life', value: '8.0 years', status: 'warning' },
    { label: 'Next Inspection Due', value: 'September 2029', status: 'normal' },
  ],
  riskLevel: 'Requires Engineering Review',
  riskExplanation:
    'The measured minimum thickness of 8.2 mm is above the retirement thickness of 7.0 mm (per API-579 Level 1 assessment), but the remaining corrosion allowance of 1.2 mm warrants closer monitoring. At the current corrosion rate of 0.15 mm/year, the equipment has an estimated remaining life of 8 years. However, localized thinning at TML-14 and TML-19 suggests non-uniform corrosion that may accelerate. Recommend continued service with reduced inspection interval.',
};

export const demoSources: Source[] = [
  { name: 'Inspection Report E-204 (UTM-2026-0342)', type: 'Inspection Report', relevance: 'Primary data source — thickness measurement readings' },
  { name: 'Corrosion Monitoring SOP Rev.3', type: 'Standard Operating Procedure', relevance: 'Defines inspection intervals and acceptance criteria' },
  { name: 'Equipment Maintenance Manual — E-204', type: 'Technical Manual', relevance: 'Nominal dimensions and material specifications' },
  { name: 'API-579-1 / ASME FFS-1 (2021)', type: 'Engineering Standard', relevance: 'Fitness-for-service assessment methodology' },
];

export const demoUserMessage: DemoMessage = {
  id: 'demo-user-1',
  role: 'user',
  content:
    'Analyze this inspection report for Heat Exchanger E-204. Identify critical findings, compare them against the applicable limits and prepare an approval note for continued operation.',
  attachments: demoAttachments,
  timestamp: '10:24 AM',
};

export const demoAIResponse: DemoMessage = {
  id: 'demo-ai-1',
  role: 'ai',
  content: '',
  processingSteps: demoProcessingSteps,
  findings: demoFindings,
  sources: demoSources,
  timestamp: '10:24 AM',
};

export const approvalNoteContent = {
  title: 'ENGINEERING APPROVAL NOTE',
  documentNumber: 'EN-2026-0847',
  date: '22 September 2026',
  equipment: 'Heat Exchanger E-204',
  location: 'Crude Distillation Unit (CDU-1)',
  preparedBy: 'SOVA — Automated Assessment',
  reviewedBy: 'Pending — Chief Inspector',
  sections: {
    summary:
      'This engineering note presents the fitness-for-service assessment of Heat Exchanger E-204 based on the ultrasonic thickness measurement (UTM) inspection conducted on 18 September 2026. The assessment concludes that E-204 is fit for continued service with conditions.',
    findings: [
      'Minimum measured wall thickness: 8.2 mm (TML-14, Channel Side)',
      'Nominal wall thickness: 10.0 mm (SA-516 Gr.70)',
      'Retirement thickness: 7.0 mm (per design calculation)',
      'Remaining corrosion allowance: 1.2 mm',
      'Maximum corrosion rate: 0.15 mm/year (long-term average)',
      'Localized thinning observed at TML-14 and TML-19',
      'No indications of cracking or pitting',
    ],
    calculation: {
      method: 'API-579-1 Level 1 Assessment — General Metal Loss',
      tMin: '7.0 mm (minimum required thickness per ASME B31.3)',
      tMeasured: '8.2 mm',
      ratio: 'tMeasured / tMin = 1.17 > 1.0 — ACCEPTABLE',
      remainingLife: '(8.2 - 7.0) / 0.15 = 8.0 years',
      nextInspection: 'Half remaining life = 4.0 years → Recommended: 3.0 years (conservative)',
    },
    recommendation: [
      'Heat Exchanger E-204 is FIT FOR CONTINUED SERVICE.',
      'Reduce inspection interval from 5 years to 3 years.',
      'Add TML-14 and TML-19 to the enhanced monitoring program.',
      'Consider internal visual inspection during next turnaround (2028).',
      'Update corrosion loop CML data in the asset management system.',
    ],
    references: [
      'UTM Inspection Report UTM-2026-0342',
      'API-579-1 / ASME FFS-1 (2021) — Fitness-For-Service',
      'ASME B31.3 — Process Piping',
      'Equipment Datasheet — E-204 (Rev.4)',
      'Corrosion Monitoring SOP (Rev.3)',
      'Previous Inspection Report UTM-2023-0198',
    ],
  },
};
