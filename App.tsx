import React, { useState } from 'react';
import { AppState, StyleAnalysis } from './types';
import { extractTextFromFile } from './services/pdfService';
import { analyzeTextStyle } from './services/geminiService';
import { FileUpload } from './components/FileUpload';
import { AnalysisResult } from './components/AnalysisResult';
import { StyleSummoner } from './components/StyleSummoner';
import { MirrorEditor } from './components/MirrorEditor';

type ViewMode = 'SUMMON' | 'EDITOR';

export default function App() {
  const [appState, setAppState] = useState<AppState>(AppState.IDLE);
  const [corpus, setCorpus] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<StyleAnalysis | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('SUMMON');

  const processText = async (text: string) => {
    if (text.length < 50) {
      setErrorMsg("El espécimen es insuficiente para una autopsia válida.");
      setAppState(AppState.ERROR);
      return;
    }
    
    setAppState(AppState.ANALYZING);
    try {
      const newCorpus = [...corpus, text];
      setCorpus(newCorpus);
      
      const fullText = newCorpus.join('\n\n*** SIGUIENTE DOCUMENTO ***\n\n');
      const result = await analyzeTextStyle(fullText);
      
      setAnalysis(result);
      setAppState(AppState.COMPLETE);
    } catch (error: any) {
      console.error(error);
      setErrorMsg(error.message || "Fallo sistémico en la disección.");
      setAppState(AppState.ERROR);
    }
  };

  const handleFileSelect = async (file: File) => {
    setAppState(AppState.READING_PDF);
    setErrorMsg(null);

    try {
      const text = await extractTextFromFile(file);
      await processText(text);
    } catch (error: any) {
      console.error(error);
      setErrorMsg(error.message || "Error al procesar el cadáver textual.");
      setAppState(AppState.ERROR);
    }
  };

  const handleTextSubmit = async (text: string) => {
    setAppState(AppState.ANALYZING);
    setErrorMsg(null);
    await processText(text);
  };

  const handleReset = () => {
    setAppState(AppState.IDLE);
    setAnalysis(null);
    setCorpus([]);
    setErrorMsg(null);
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-rose-500/30 selection:text-rose-200">
      <header className="fixed top-0 w-full z-50 bg-[#020617]/80 backdrop-blur-md border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center space-x-3">
             <div className="w-10 h-10 bg-gradient-to-br from-rose-600 via-rose-700 to-rose-900 rounded-lg flex items-center justify-center shadow-lg shadow-rose-900/20">
                <span className="text-white font-display font-bold text-xl">S</span>
             </div>
             <h1 className="text-2xl font-display font-bold tracking-tight text-white">
               Soul<span className="text-rose-500">Scribe</span>
             </h1>
          </div>
          <span className="text-xs font-mono text-slate-600">v3.3.0 // FORENSIC SUMMONER</span>
        </div>
      </header>

      <main className="pt-32 pb-20 px-6 relative overflow-hidden">
        <div className="absolute top-20 left-1/4 w-[500px] h-[500px] bg-rose-900/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

        <div className="max-w-7xl mx-auto">
          {appState === AppState.IDLE && (
            <div className="text-center mb-16 space-y-6 animate-fade-in">
              <h2 className="text-5xl md:text-7xl font-display font-bold leading-none tracking-tighter">
                Disección <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-400 to-rose-600">Sin Anestesia</span>
              </h2>
              <p className="text-lg text-slate-500 max-w-2xl mx-auto font-serif leading-relaxed">
                Extracción integral de ADN literario. Analiza vicios y virtudes para invocar textos originales.
              </p>
            </div>
          )}

          <div className="transition-all duration-500 ease-in-out">
            {appState === AppState.IDLE && (
              <div className="max-w-xl mx-auto">
                <FileUpload 
                  onFileSelect={handleFileSelect} 
                  onTextSubmit={handleTextSubmit}
                  isProcessing={false} 
                />
              </div>
            )}

            {(appState === AppState.READING_PDF || appState === AppState.ANALYZING) && (
              <div className="max-w-xl mx-auto text-center py-20">
                <div className="relative w-24 h-24 mx-auto mb-8">
                  <div className="absolute inset-0 border-4 border-slate-800 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-rose-600 rounded-full border-t-transparent animate-spin"></div>
                </div>
                <h3 className="text-2xl font-display text-white mb-2">
                  {appState === AppState.READING_PDF ? "Escaneando Tejido..." : "Abriendo el Estilo..."}
                </h3>
                <p className="text-slate-500 font-serif italic text-sm">
                  {appState === AppState.READING_PDF 
                    ? "Preparando muestras para la autopsia..." 
                    : "Analizando vicios, muletillas y genialidades subconscientes."}
                </p>
              </div>
            )}

            {appState === AppState.ERROR && (
              <div className="max-w-xl mx-auto text-center py-10 bg-rose-950/20 border border-rose-500/20 rounded-2xl">
                <h3 className="text-xl font-bold text-rose-200 mb-2">Error Crítico</h3>
                <p className="text-rose-400/80 mb-6 px-4">{errorMsg}</p>
                <button onClick={handleReset} className="text-rose-500 hover:text-white underline">Reiniciar Proceso</button>
              </div>
            )}

            {appState === AppState.COMPLETE && analysis && (
              <div className="space-y-16">
                <AnalysisResult 
                    analysis={analysis} 
                    onReset={handleReset} 
                    onRefine={handleFileSelect}
                    docCount={corpus.length}
                />
                
                <div className="border-t border-slate-800 pt-10">
                   <div className="flex justify-center mb-8">
                      <div className="bg-slate-900/80 p-1 rounded-xl border border-slate-700 inline-flex">
                          <button 
                            onClick={() => setViewMode('SUMMON')}
                            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${viewMode === 'SUMMON' ? 'bg-rose-600 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
                          >
                            Invocar Texto
                          </button>
                          <button 
                            onClick={() => setViewMode('EDITOR')}
                            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${viewMode === 'EDITOR' ? 'bg-slate-700 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
                          >
                            Mimesis de Texto
                          </button>
                      </div>
                   </div>

                   {viewMode === 'SUMMON' ? (
                       <StyleSummoner analysis={analysis} />
                   ) : (
                       <MirrorEditor analysis={analysis} />
                   )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}