import React, { useState } from 'react';
import { AppState, StyleAnalysis, AnalysisLens } from './types';
import { extractTextFromFile } from './services/pdfService';
import { analyzeTextStyle } from './services/geminiService';
import { FileUpload } from './components/FileUpload';
import { AnalysisResult } from './components/AnalysisResult';
import { StyleTester } from './components/StyleTester';
import { MirrorEditor } from './components/MirrorEditor';

type ViewMode = 'CHAT' | 'EDITOR';

export default function App() {
  const [appState, setAppState] = useState<AppState>(AppState.IDLE);
  const [corpus, setCorpus] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<StyleAnalysis | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('CHAT');
  const [selectedLens, setSelectedLens] = useState<AnalysisLens>('ATOMIZATION');

  const processText = async (text: string) => {
    if (text.length < 50) {
      setErrorMsg("El texto es demasiado corto para un análisis estilístico serio.");
      setAppState(AppState.ERROR);
      return;
    }
    
    setAppState(AppState.ANALYZING);
    try {
      const newCorpus = [...corpus, text];
      setCorpus(newCorpus);
      
      const fullText = newCorpus.join('\n\n*** SIGUIENTE DOCUMENTO ***\n\n');
      const result = await analyzeTextStyle(fullText, selectedLens);
      
      setAnalysis(result);
      setAppState(AppState.COMPLETE);
    } catch (error: any) {
      console.error(error);
      setErrorMsg(error.message || "Error inesperado durante el análisis.");
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
      setErrorMsg(error.message || "Error inesperado leyendo el archivo.");
      setAppState(AppState.ERROR);
    }
  };

  const handleTextSubmit = async (text: string) => {
    setAppState(AppState.ANALYZING); // Skip "READING"
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
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-gold/30 selection:text-gold">
      <header className="fixed top-0 w-full z-50 bg-[#020617]/80 backdrop-blur-md border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center space-x-3">
             <div className="w-10 h-10 bg-gradient-to-br from-gold via-amber-600 to-yellow-800 rounded-lg flex items-center justify-center shadow-lg shadow-gold/20">
                <span className="text-white font-display font-bold text-xl">S</span>
             </div>
             <h1 className="text-2xl font-display font-bold tracking-tight text-white">
               Soul<span className="text-gold">Scribe</span>
             </h1>
          </div>
          <span className="text-xs font-mono text-slate-500">v3.0.0 // AI CLONING ENGINE</span>
        </div>
      </header>

      <main className="pt-32 pb-20 px-6 relative overflow-hidden">
        <div className="absolute top-20 left-1/4 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        <div className="absolute bottom-20 right-1/4 w-[500px] h-[500px] bg-amber-600/5 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

        <div className="max-w-7xl mx-auto">
          {appState === AppState.IDLE && (
            <div className="text-center mb-16 space-y-6 animate-fade-in">
              <h2 className="text-5xl md:text-7xl font-display font-bold leading-none tracking-tighter">
                Disección <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold to-amber-200">Estilística</span>
              </h2>
              <p className="text-lg text-slate-400 max-w-2xl mx-auto font-serif leading-relaxed">
                Muestreo inteligente, análisis de métricas biométricas y clonación profunda.
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
                  selectedLens={selectedLens}
                  onLensChange={setSelectedLens}
                />
              </div>
            )}

            {(appState === AppState.READING_PDF || appState === AppState.ANALYZING) && (
              <div className="max-w-xl mx-auto text-center py-20">
                <div className="relative w-24 h-24 mx-auto mb-8">
                  <div className="absolute inset-0 border-4 border-slate-800 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-gold rounded-full border-t-transparent animate-spin"></div>
                </div>
                <h3 className="text-2xl font-display text-white mb-2">
                  {appState === AppState.READING_PDF ? "Muestreo Inteligente..." : "Atomizando Estilo..."}
                </h3>
                <p className="text-mist font-serif italic text-sm">
                  {appState === AppState.READING_PDF 
                    ? "Procesando archivo..." 
                    : "Calculando métricas de formalidad, complejidad y sarcasmo."}
                </p>
              </div>
            )}

            {appState === AppState.ERROR && (
              <div className="max-w-xl mx-auto text-center py-10 bg-red-900/10 border border-red-500/20 rounded-2xl">
                <h3 className="text-xl font-bold text-red-200 mb-2">Error Crítico</h3>
                <p className="text-red-300/80 mb-6 px-4">{errorMsg}</p>
                <button onClick={handleReset} className="text-red-400 hover:text-white underline">Reiniciar</button>
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
                
                {/* TOOLBAR FOR APPS */}
                <div className="border-t border-slate-800 pt-10">
                   <div className="flex justify-center mb-8">
                      <div className="bg-slate-900/80 p-1 rounded-xl border border-slate-700 inline-flex">
                          <button 
                            onClick={() => setViewMode('CHAT')}
                            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${viewMode === 'CHAT' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
                          >
                            Chat Interactivo
                          </button>
                          <button 
                            onClick={() => setViewMode('EDITOR')}
                            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${viewMode === 'EDITOR' ? 'bg-gold text-black shadow-lg' : 'text-slate-400 hover:text-white'}`}
                          >
                            Editor Espejo
                          </button>
                      </div>
                   </div>

                   {viewMode === 'CHAT' ? (
                       <StyleTester analysis={analysis} />
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