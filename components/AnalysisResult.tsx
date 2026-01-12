import React, { useState } from 'react';
import { StyleAnalysis } from '../types';
import { FileUpload } from './FileUpload';
import { RadarChart } from './RadarChart';

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

  const getScoreColor = (score: number) => {
    if (score < 40) return 'bg-green-500'; 
    if (score < 70) return 'bg-gold';      
    return 'bg-purple-500';                
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-12 animate-fade-in">
      
      {/* Header Result */}
      <div className="text-center space-y-6">
        <div className="inline-flex items-center space-x-2 text-gold mb-2 bg-gold/10 px-4 py-1 rounded-full border border-gold/20">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <span className="uppercase tracking-widest text-xs font-bold">ADN Estilístico Extraído</span>
        </div>
        <h2 className="text-5xl md:text-6xl font-display text-white drop-shadow-lg">
          {analysis.personaName}
        </h2>
        
        <p className="text-xl text-mist italic font-serif max-w-4xl mx-auto leading-relaxed border-l-4 border-gold/40 pl-6 py-2 bg-gradient-to-r from-gold/5 to-transparent rounded-r-xl">
          "{analysis.summary}"
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
         {/* Left Col: Radar Chart & Metrics */}
         <div className="lg:col-span-4 space-y-6">
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col items-center">
               <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Huella Biométrica</h4>
               {analysis.metrics && <RadarChart metrics={analysis.metrics} />}
            </div>

            <div className="bg-slate-900/50 rounded-xl p-5 border border-slate-800 backdrop-blur-sm space-y-4">
                 <div className="flex justify-between items-center">
                     <span className="text-xs font-semibold text-slate-400 uppercase">Nivel Cognitivo</span>
                     <span className="text-sm font-bold text-ethereal">{analysis.writingLevel}</span>
                 </div>
                 <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div 
                        className={`h-2 rounded-full ${getScoreColor(analysis.writingScore)}`} 
                        style={{ width: `${analysis.writingScore}%` }}
                    ></div>
                 </div>
            </div>
         </div>

         {/* Right Col: Traits Grid */}
         <div className="lg:col-span-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analysis.keyTraits.map((trait, idx) => (
                    <div key={idx} className="bg-slate-900/40 hover:bg-slate-900/60 border border-slate-800/60 hover:border-gold/30 rounded-lg p-4 transition-all">
                        <div className="flex items-center gap-2 mb-2">
                             <span className="w-1.5 h-1.5 rounded-full bg-gold/50"></span>
                             <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wide truncate">
                                {trait.name}
                            </h4>
                        </div>
                        <p className="text-xs text-slate-400 leading-relaxed mb-2 line-clamp-3">
                            {trait.description}
                        </p>
                        <div className="text-[10px] text-gold/60 font-serif italic border-l border-slate-700 pl-2">
                            "{trait.example.slice(0, 100)}..."
                        </div>
                    </div>
                ))}
            </div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* System Prompt Section */}
        <div className="lg:col-span-2">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 h-full flex flex-col relative overflow-hidden group">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
                 Código Fuente (System Prompt)
              </h3>
              <button
                onClick={handleCopy}
                className="text-xs bg-black/50 hover:bg-gold/20 text-gold border border-gold/30 px-3 py-1 rounded transition-colors"
              >
                {copied ? '¡Copiado!' : 'Copiar XML'}
              </button>
            </div>
            <div className="flex-grow bg-black/80 rounded-lg p-4 font-mono text-[10px] text-blue-200/70 leading-relaxed overflow-y-auto max-h-[200px] shadow-inner border border-white/5">
              <pre className="whitespace-pre-wrap">{analysis.systemPrompt}</pre>
            </div>
          </div>
        </div>

        {/* Actions Column */}
        <div className="lg:col-span-1 space-y-4">
             <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
                <h4 className="text-xs font-bold text-white mb-2 uppercase">Refinar Modelo</h4>
                <FileUpload onFileSelect={onRefine} isProcessing={false} variant="compact" />
             </div>
             
             <button 
                onClick={onReset}
                className="w-full py-3 px-4 rounded-xl border border-dashed border-red-900/50 text-red-400/60 hover:text-red-400 hover:bg-red-900/10 transition-all text-xs uppercase font-bold tracking-widest"
            >
                Destruir y Reiniciar
            </button>
        </div>
      </div>
    </div>
  );
};