import React, { useState } from 'react';
import { StyleAnalysis } from '../types';
import { FileUpload } from './FileUpload';

interface AnalysisResultProps {
  analysis: StyleAnalysis;
  onReset: () => void;
  onRefine: (file: File) => void;
  docCount: number;
}

export const AnalysisResult: React.FC<AnalysisResultProps> = ({ analysis, onReset, onRefine, docCount }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(analysis.systemPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Determine color based on score complexity
  const getScoreColor = (score: number) => {
    if (score < 40) return 'bg-green-500'; // Simple/Accessible
    if (score < 70) return 'bg-gold';      // Moderate
    return 'bg-purple-500';                // Complex/Academic
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-10 animate-fade-in">
      
      {/* Header Result */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center space-x-2 text-gold mb-2 bg-gold/10 px-4 py-1 rounded-full border border-gold/20">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <span className="uppercase tracking-widest text-xs font-bold">ADN Estilístico Extraído</span>
        </div>
        <h2 className="text-4xl md:text-5xl font-display text-white">
          {analysis.personaName}
        </h2>
        
        {/* New Writing Level Section */}
        <div className="max-w-md mx-auto bg-slate-900/50 rounded-xl p-4 border border-slate-800 backdrop-blur-sm">
             <div className="flex justify-between items-center mb-2">
                 <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Nivel de Escritura</span>
                 <span className="text-sm font-bold text-ethereal">{analysis.writingLevel}</span>
             </div>
             <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div 
                    className={`h-2.5 rounded-full ${getScoreColor(analysis.writingScore)} transition-all duration-1000 ease-out`} 
                    style={{ width: `${analysis.writingScore}%` }}
                ></div>
             </div>
             <div className="flex justify-between mt-1 text-[10px] text-slate-500 font-mono">
                 <span>Coloquial</span>
                 <span>Puntaje: {analysis.writingScore}/100</span>
                 <span>Erudito</span>
             </div>
        </div>

        <div className="flex items-center justify-center space-x-3 text-sm text-slate-500 font-mono mt-2">
            <span className="bg-slate-800 px-2 py-0.5 rounded text-xs border border-slate-700">Fuente: {docCount} docs</span>
            <span className="text-slate-700">|</span>
            <span className="bg-slate-800 px-2 py-0.5 rounded text-xs border border-slate-700">Modelo: Gemini 3.0 Pro</span>
        </div>
        
        <p className="text-lg text-mist italic font-serif max-w-3xl mx-auto leading-relaxed border-l-2 border-gold/30 pl-4 py-2 bg-gradient-to-r from-gold/5 to-transparent rounded-r-lg mt-6">
          "{analysis.summary}"
        </p>
      </div>

      {/* Traits Grid */}
      <div className="space-y-4">
        <h3 className="text-xl font-display text-ethereal border-b border-slate-800 pb-2 flex items-center gap-2">
            <span className="text-gold">✦</span>
            Rasgos Dominantes Detectados
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {analysis.keyTraits.map((trait, idx) => (
                <div key={idx} className="group bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 hover:border-gold/30 rounded-xl p-5 transition-all duration-300 flex flex-col">
                    <div className="flex items-start justify-between mb-3">
                        <h4 className="font-bold text-gold/90 group-hover:text-gold text-sm uppercase tracking-wide">
                            {trait.name}
                        </h4>
                        <span className="text-slate-700 text-xs font-mono">0{idx + 1}</span>
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed mb-4 flex-grow">
                        {trait.description}
                    </p>
                    <div className="bg-black/30 rounded-lg p-3 border-l-2 border-slate-600 group-hover:border-gold/50 transition-colors">
                        <p className="text-xs text-mist font-serif italic">
                            "{trait.example}"
                        </p>
                    </div>
                </div>
            ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* System Prompt Section */}
        <div className="lg:col-span-2">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 h-full flex flex-col relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gold/5 rounded-full blur-3xl -z-10"></div>
            
            <div className="flex justify-between items-center mb-4">
              <div className="space-y-1">
                  <h3 className="text-lg font-semibold text-ethereal">
                    Prompt Maestro (System XML)
                  </h3>
                  <p className="text-xs text-slate-500">Copia esto en tu LLM favorito para replicar el estilo.</p>
              </div>
              <button
                onClick={handleCopy}
                className={`
                    text-xs flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all
                    ${copied ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-gold/10 text-gold hover:bg-gold/20 border border-gold/20'}
                `}
              >
                {copied ? (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    <span>Copiado al portapapeles</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                    <span>Copiar XML Prompt</span>
                  </>
                )}
              </button>
            </div>
            
            <div className="flex-grow bg-black/60 rounded-lg p-5 font-mono text-xs text-blue-200/80 leading-relaxed overflow-y-auto max-h-[300px] border border-slate-800/50 shadow-inner">
              <pre className="whitespace-pre-wrap font-mono">{analysis.systemPrompt}</pre>
            </div>
          </div>
        </div>

        {/* Actions Column */}
        <div className="lg:col-span-1 space-y-6">
             <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5">
                <h4 className="text-sm font-bold text-white mb-3">Refinar Análisis</h4>
                <p className="text-xs text-mist mb-4">Añade más textos de este autor para mejorar la precisión del modelo.</p>
                <FileUpload onFileSelect={onRefine} isProcessing={false} variant="compact" />
             </div>
             
             <button 
                onClick={onReset}
                className="w-full group flex items-center justify-center space-x-2 py-4 px-4 rounded-xl border border-dashed border-slate-700 text-slate-500 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/5 transition-all text-sm"
            >
                <svg className="w-4 h-4 group-hover:rotate-90 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Empezar nuevo análisis</span>
            </button>
        </div>
      </div>
    </div>
  );
};