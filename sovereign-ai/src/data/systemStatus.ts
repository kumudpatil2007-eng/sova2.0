export interface SystemMetric {
  label: string;
  value: string;
  status: 'active' | 'secure' | 'disconnected';
}

export const systemMetrics: SystemMetric[] = [
  { label: 'Inference Engine', value: 'LOCAL', status: 'active' },
  { label: 'Model', value: 'Qwen2.5-VL-72B (Open-Weight)', status: 'active' },
  { label: 'Knowledge Base', value: 'LOCAL — ChromaDB', status: 'active' },
  { label: 'OCR Engine', value: 'LOCAL — Surya + PaddleOCR', status: 'active' },
  { label: 'Document Parser', value: 'LOCAL — Unstructured.io', status: 'active' },
  { label: 'Agent Framework', value: 'LOCAL — LangGraph', status: 'active' },
  { label: 'Network Status', value: 'DISCONNECTED / AIR-GAPPED', status: 'disconnected' },
  { label: 'External API Calls', value: '0', status: 'secure' },
  { label: 'Data Egress', value: '0 bytes', status: 'secure' },
  { label: 'Outbound Connections', value: '0', status: 'secure' },
  { label: 'GPU', value: 'NVIDIA A100 80GB × 2', status: 'active' },
  { label: 'VRAM Usage', value: '54.2 / 160 GB', status: 'active' },
];

export const systemCapabilities = [
  {
    name: 'Vision & Document Understanding',
    model: 'Qwen2.5-VL-72B',
    description: 'Multimodal understanding of scanned documents, photographs, P&IDs, handwritten notes.',
    status: 'Running',
  },
  {
    name: 'Text Generation & Reasoning',
    model: 'Qwen2.5-72B-Instruct',
    description: 'Engineering reasoning, report generation, calculation verification, code generation.',
    status: 'Running',
  },
  {
    name: 'Optical Character Recognition',
    model: 'Surya + PaddleOCR',
    description: 'Multi-language OCR for scanned documents, handwritten notes, and photographs.',
    status: 'Running',
  },
  {
    name: 'Retrieval-Augmented Generation',
    model: 'BGE-M3 + ChromaDB',
    description: 'Local vector store indexing and retrieval of organizational knowledge.',
    status: 'Running',
  },
];
