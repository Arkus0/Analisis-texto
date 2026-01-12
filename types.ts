export interface StyleTrait {
  name: string;
  description: string;
  example: string;
}

export interface StyleAnalysis {
  personaName: string;
  writingLevel: string; // Ej: "Universitario", "Literario Denso", "Coloquial"
  writingScore: number; // 0-100 Escala de complejidad
  summary: string;
  keyTraits: StyleTrait[];
  systemPrompt: string;
}

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export enum AppState {
  IDLE = 'IDLE',
  READING_PDF = 'READING_PDF',
  ANALYZING = 'ANALYZING',
  COMPLETE = 'COMPLETE',
  ERROR = 'ERROR'
}

export interface HumanizationConfig {
  burstiness: boolean;      // Variación drástica de estructura
  imperfections: boolean;   // Errores menores, coloquialismos
  personalTouch: boolean;   // Subjetividad y emociones
  culturalContext: boolean; // Referencias y humor ligero
  antiRepetition: boolean;  // Evitar frases cliché de IA
}