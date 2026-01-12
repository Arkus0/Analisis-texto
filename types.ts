export interface StyleTrait {
  name: string;
  description: string;
  example: string;
}

export interface StyleMetrics {
  complexity: number; // 0-100
  formality: number;  // 0-100
  emotionality: number; // 0-100
  sarcasm: number;    // 0-100
  creativity: number; // 0-100
}

export interface StyleAnalysis {
  personaName: string;
  writingLevel: string; 
  writingScore: number; 
  metrics: StyleMetrics; 
  summary: string;
  keyTraits: StyleTrait[];
  systemPrompt: string;
}

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
  // Feedback state for RLHF
  feedback?: 'positive' | 'negative' | null;
}

export enum AppState {
  IDLE = 'IDLE',
  READING_PDF = 'READING_PDF',
  ANALYZING = 'ANALYZING',
  COMPLETE = 'COMPLETE',
  ERROR = 'ERROR'
}

export interface HumanizationConfig {
  burstiness: boolean;      
  imperfections: boolean;   
  personalTouch: boolean;   
  culturalContext: boolean; 
  antiRepetition: boolean;  
}

export type AnalysisLens = 'ATOMIZATION' | 'PSYCHOLINGUIST' | 'RHETORIC';

export const LENS_DESCRIPTIONS: Record<AnalysisLens, { name: string; desc: string }> = {
  ATOMIZATION: { name: "Microscopio de Atomización", desc: "Separa sintaxis, morfología y ritmo al detalle." },
  PSYCHOLINGUIST: { name: "Psico-Lingüista", desc: "Deduce la psicología y sesgos a través de los vicios del lenguaje." },
  RHETORIC: { name: "Arquitecto de Retórica", desc: "Prioriza figuras literarias, metáforas y estructuras complejas." }
};