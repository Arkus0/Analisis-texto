import React, { useState } from 'react';
import { StyleAnalysis } from '../types';
import { rewriteWithStyle } from '../services/geminiService';

interface MirrorEditorProps {
  analysis: StyleAnalysis;
}

export const MirrorEditor: React.FC<MirrorEditorProps> = ({ analysis }) => {
  const [original, setOriginal] = useState('');
  const [transformed, setTransformed] = useState('');
  const [isTransforming, setIsTransforming] = useState(false);

  const handleTransform = async () => {
    if (!original.trim()) return;
    
    setIsTransforming(true);
    setTransformed(''); 
    
    try {
      const result = await rewriteWithStyle(original, analysis.systemPrompt);
      setTransformed(result);
    } catch (e) {
      console.error(e);
      setTransformed("Error en la transformación.");
    } finally {
      setIsTransforming(false);
    }
  };

  return (
    <div className="animate-fade-in space-y-6 max-w-6xl mx-auto mt-8">
      <div className="flex items-center justify-between">
         <h2 className="text-xl font-display text-ethereal flex items-center gap-2">
            <span className="text-gold">✦</span> Editor Espejo
         </h2>
         <p className="text-xs text-slate-500 font-mono">Transforma tu borrador al estilo de {analysis.personaName}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[500px]">
        {/* Input Pane */}
        <div className="flex flex-col bg-slate-900/50 border border-slate-700 rounded-xl overflow-hidden focus-within:ring-1 focus-within:ring-slate-500 transition-all">
          <div className="bg-slate-800/50 px-4 py-2 border-b border-slate-700 flex justify-between items-center">
            <span className="text-xs font-bold text-slate-400 uppercase">Tu Borrador</span>
            <button 
              onClick={() => setOriginal('')}
              className="text-[10px] text-slate-500 hover:text-red-400"
            >
              LIMPIAR
            </button>
          </div>
          <textarea
            value={original}
            onChange={(e) => setOriginal(e.target.value)}
            placeholder="Pega aquí tu texto aburrido..."
            className="flex-grow bg-transparent p-5 text-slate-300 resize-none focus:outline-none font-sans leading-relaxed text-sm"
          />
        </div>

        {/* Output Pane */}
        <div className="flex flex-col bg-black/40 border border-gold/20 rounded-xl overflow-hidden relative">
           {isTransforming && (
             <div className="absolute inset-0 bg-black/60 z-10 flex items-center justify-center backdrop-blur-sm">
                <div className="flex flex-col items-center gap-3">
                   <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin"></div>
                   <span className="text-xs text-gold animate-pulse">Invocando al autor...</span>
                </div>
             </div>
           )}
           
           <div className="bg-gold/5 px-4 py-2 border-b border-gold/10 flex justify-between items-center">
             <span className="text-xs font-bold text-gold uppercase">Versión {analysis.personaName}</span>
             <button 
                onClick={() => navigator.clipboard.writeText(transformed)}
                className="text-[10px] text-gold/70 hover:text-gold"
                disabled={!transformed}
             >
               COPIAR
             </button>
           </div>
           
           <div className="flex-grow p-5 overflow-y-auto">
             {transformed ? (
                <div className="text-ethereal font-serif leading-loose text-sm whitespace-pre-wrap">
                   {transformed}
                </div>
             ) : (
                <div className="h-full flex items-center justify-center text-slate-600 text-xs italic">
                   El resultado aparecerá aquí...
                </div>
             )}
           </div>
        </div>
      </div>

      <div className="flex justify-center">
        <button
          onClick={handleTransform}
          disabled={!original.trim() || isTransforming}
          className="bg-gold text-black font-bold py-3 px-8 rounded-full shadow-[0_0_20px_rgba(251,191,36,0.3)] hover:bg-amber-400 hover:shadow-[0_0_30px_rgba(251,191,36,0.5)] transition-all disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-1"
        >
           {isTransforming ? 'Reescribiendo...' : 'Transmutar Texto'}
        </button>
      </div>
    </div>
  );
};