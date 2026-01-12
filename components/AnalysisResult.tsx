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

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'virtue': return 'border-emerald-500/40 bg-emerald-500/5 text-emerald-400';
      case 'vice': return 'border-rose-500/40 bg-rose-500/5 text-rose-400';
      default: return 'border-slate-700 bg-slate-900/40 text-slate-400';
    }
  };

  const getImpactTag = (impact: string) => {
    switch (impact) {
      case 'virtue': return 'VIRTUD';
      case 'vice': return 'VICIO/MULETILLA';
      default: return 'PATRÓN';
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-12 animate-fade-in">
      
      {/* Header Result */}
      <div className="text-center space-y-6">
        <div className="inline-flex items-center space-x-2 text-rose-500 mb-2 bg-rose-500/10 px-4 py-1 rounded-full border border-rose-500/20">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="uppercase tracking-widest text-xs font-bold">Autopsia Estilística Completada</span>
        </div>
        <h2 className="text-5xl md:text-6xl font-display text-white drop-shadow-lg">
          {analysis.personaName}
        </h2>
        
        <p className="text-xl text-mist italic font-serif max-w-4xl mx-auto leading-relaxed border-l-4 border-rose-500/40 pl-6 py-2 bg-gradient-to-r from-rose-500/5 to-transparent rounded-r-xl">
          "{analysis.summary}"
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
         <div className="lg:col-span-4 space-y-6">
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col items-center">
               <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Métricas de ADN</h4>
               {analysis.metrics && <RadarChart metrics={analysis.metrics} />}
            </div>

            <div className="bg-slate-900/50 rounded-xl p-5 border border-slate-800 backdrop-blur-sm space-y-4">
                 <div className="flex justify-between items-center">
                     <span className="text-xs font-semibold text-slate-400 uppercase">Nivel de Escritura</span>
                     <span className="text-sm font-bold text-ethereal">{analysis.writingLevel}</span>
                 </div>
            </div>
         </div>

         <div className="lg:col-span-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analysis.keyTraits.map((trait, idx) => (
                    <div key={idx} className={`border rounded-lg p-4 transition-all ${getImpactColor(trait.impact)}`}>
                        <div className="flex justify-between items-start mb-2">
                             <h4 className="font-bold text-xs uppercase tracking-wide truncate pr-2">
                                {trait.name}
                            </h4>
                            <span className="text-[8px] font-black px-1.5 py-0.5 rounded border border-current opacity-70">
                                {getImpactTag(trait.impact)}
                            </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed mb-2 opacity-80">
                            {trait.description}
                        </p>
                        <div className="text-[10px] italic border-l border-current/20 pl-2 opacity-60">
                            "{trait.example.slice(0, 120)}..."
                        </div>
                    </div>
                ))}
            </div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 h-full flex flex-col relative overflow-hidden group">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
                 Código Fuente de Mimesis (XML)
              </h3>
              <button
                onClick={handleCopy}
                className="text-xs bg-black/50 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 px-3 py-1 rounded transition-colors"
              >
                {copied ? 'Copiado' : 'Copiar ADN'}
              </button>
            </div>
            <div className="flex-grow bg-black/80 rounded-lg p-4 font-mono text-[10px] text-rose-200/50 leading-relaxed overflow-y-auto max-h-[200px] shadow-inner border border-white/5">
              <pre className="whitespace-pre-wrap">{analysis.systemPrompt}</pre>
            </div>
          </div>
        </div>

        <div className="lg:col-span-1 space-y-4">
             <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
                <h4 className="text-xs font-bold text-white mb-2 uppercase">Inyectar más muestras</h4>
                <FileUpload onFileSelect={onRefine} isProcessing={false} variant="compact" />
             </div>
             
             <button 
                onClick={onReset}
                className="w-full py-3 px-4 rounded-xl border border-dashed border-rose-900/50 text-rose-500/60 hover:text-rose-400 hover:bg-rose-900/10 transition-all text-xs uppercase font-bold tracking-widest"
            >
                Cerrar Caso y Destruir
            </button>
        </div>
      </div>
    </div>
  );
};