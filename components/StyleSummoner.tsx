import React, { useState } from 'react';
import { StyleAnalysis } from '../types';
import { generateStyleContent } from '../services/geminiService';

interface StyleSummonerProps {
  analysis: StyleAnalysis;
}

export const StyleSummoner: React.FC<StyleSummonerProps> = ({ analysis }) => {
  const [topic, setTopic] = useState('');
  const [wordCount, setWordCount] = useState(350);
  const [temperature, setTemperature] = useState(0.9);
  const [result, setResult] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSummon = async () => {
    if (!topic.trim() || isLoading) return;
    
    setIsLoading(true);
    setResult('');
    
    try {
      const generated = await generateStyleContent(
        topic,
        wordCount,
        analysis.systemPrompt,
        temperature
      );
      setResult(generated);
    } catch (e) {
      console.error(e);
      setResult("Error en la transmutación del ADN literario.");
    } finally {
      setIsLoading(false);
    }
  };

  const actualWordCount = result ? result.split(/\s+/).filter(Boolean).length : 0;

  return (
    <div className="mt-12 max-w-5xl mx-auto animate-fade-in space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl backdrop-blur-sm">
            <h3 className="text-sm font-bold text-rose-500 uppercase tracking-[0.2em] border-b border-rose-500/20 pb-2">
              Parámetros de Invocación
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-[10px] uppercase font-bold text-slate-500 mb-2">
                  <span>Extensión del Texto</span>
                  <span className="text-rose-400">{wordCount} PALABRAS</span>
                </div>
                <input 
                  type="range" 
                  min="200" 
                  max="500" 
                  step="50" 
                  value={wordCount}
                  onChange={(e) => setWordCount(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-[10px] uppercase font-bold text-slate-500 mb-2">
                  <span>Nivel de Entropía</span>
                  <span className="text-rose-400">{(temperature * 10).toFixed(1)}</span>
                </div>
                <input 
                  type="range" 
                  min="0.5" 
                  max="1.5" 
                  step="0.1" 
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
                />
              </div>
            </div>

            <div className="pt-4">
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-2">Premisa / Tema del Escrito</label>
              <textarea 
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Ej: Una reflexión sobre el paso del tiempo en una ciudad abandonada..."
                className="w-full bg-black/40 border border-slate-700 rounded-xl p-4 text-sm text-slate-300 focus:outline-none focus:border-rose-500/50 h-32 resize-none transition-all font-serif"
              />
            </div>

            <button
              onClick={handleSummon}
              disabled={!topic.trim() || isLoading}
              className={`
                w-full py-4 rounded-xl font-bold uppercase tracking-widest text-xs transition-all shadow-lg
                ${isLoading 
                  ? 'bg-slate-800 text-slate-600 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-rose-600 to-rose-800 text-white hover:from-rose-500 hover:to-rose-700 shadow-rose-900/20 hover:shadow-rose-500/20 transform hover:-translate-y-0.5 active:translate-y-0'}
              `}
            >
              {isLoading ? 'Inyectando ADN...' : 'Generar Manuscrito'}
            </button>
          </div>
        </div>

        {/* Output Canvas */}
        <div className="lg:col-span-2 relative">
          <div className={`
            h-full min-h-[500px] bg-slate-900/30 border border-slate-800 rounded-2xl overflow-hidden flex flex-col transition-all
            ${isLoading ? 'opacity-40 grayscale-[0.5]' : ''}
          `}>
             <div className="bg-slate-900/80 px-6 py-3 border-b border-slate-800 flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                  {result ? `Evidencia Generada (${actualWordCount} palabras)` : 'Área de Manifestación'}
                </span>
                {result && (
                  <button 
                    onClick={() => navigator.clipboard.writeText(result)}
                    className="text-[10px] text-rose-400 hover:text-white transition-colors uppercase font-bold"
                  >
                    Copiar
                  </button>
                )}
             </div>

             <div className="flex-grow p-8 overflow-y-auto font-serif text-lg leading-loose text-slate-300 selection:bg-rose-500/30">
                {result ? (
                   <div className="animate-fade-in whitespace-pre-wrap">
                      {result}
                   </div>
                ) : (
                   <div className="h-full flex flex-col items-center justify-center text-slate-700 italic opacity-40">
                      <svg className="w-16 h-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={0.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      <p>Define una premisa para invocar la prosa del autor.</p>
                   </div>
                )}
             </div>

             {isLoading && (
               <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-[1px]">
                  <div className="flex flex-col items-center gap-4">
                     <div className="w-12 h-12 border-4 border-rose-500/20 border-t-rose-600 rounded-full animate-spin"></div>
                     <span className="text-xs font-bold text-rose-500 uppercase tracking-widest animate-pulse">Sintetizando Texto...</span>
                  </div>
               </div>
             )}
          </div>
        </div>

      </div>
    </div>
  );
};