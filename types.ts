export interface StyleTrait {
  name: string;
  description: string;
  example: string;
  impact: 'virtue' | 'vice' | 'neutral'; 
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