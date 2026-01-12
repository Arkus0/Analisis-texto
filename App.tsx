import React, { useState } from 'react';
import { AppState, StyleAnalysis } from './types';
import { extractTextFromPdf } from './services/pdfService';
import { analyzeTextStyle } from './services/geminiService';
import { FileUpload } from './components/FileUpload';
import { AnalysisResult } from './components/AnalysisResult';
import { StyleTester } from './components/StyleTester';

export default function App() {
  const [appState, setAppState] = useState<AppState>(AppState.IDLE);
  const [corpus, setCorpus] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<StyleAnalysis | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    // If we are already complete, we are refining. Otherwise, we are starting fresh.
    const isRefining = appState === AppState.COMPLETE;
    
    setAppState(AppState.READING_PDF);
    setErrorMsg(null);

    try {
      // 1. Extract Text
      const text = await extractTextFromPdf(file);
      
      if (text.length < 100) {
        throw new Error("El PDF contiene muy poco texto o no es un texto seleccionable (quizás sea una imagen).");
      }

      // Update corpus
      const newCorpus = [...corpus, text];
      setCorpus(newCorpus);

      // 2. Analyze with Gemini (using combined text)
      setAppState(AppState.ANALYZING);
      
      // Combine texts with a separator to help model distinguish, though 
      // usually treating it as one massive work works best for style extraction.
      const fullText = newCorpus.join('\n\n*** SIGUIENTE DOCUMENTO ***\n\n');
      
      const result = await analyzeTextStyle(fullText);
      
      setAnalysis(result);
      setAppState(AppState.COMPLETE);

    } catch (error: any) {
      console.error(error);
      setErrorMsg(error.message || "Ocurrió un error inesperado.");
      setAppState(AppState.ERROR);
    }
  };

  const handleReset = () => {
    setAppState(AppState.IDLE);
    setAnalysis(null);
    setCorpus([]);
    setErrorMsg(null);
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-gold/30 selection:text-gold">
      {/* Navbar / Header */}
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
          <a href="#" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
            Sobre el proyecto
          </a>
        </div>
      </header>

      <main className="pt-32 pb-20 px-6 relative overflow-hidden">
        {/* Decorative background elements */}
        <div className="absolute top-20 left-1/4 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        <div className="absolute bottom-20 right-1/4 w-[500px] h-[500px] bg-amber-600/5 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

        <div className="max-w-5xl mx-auto">
          
          {/* Hero Section - Only show when IDLE */}
          {appState === AppState.IDLE && (
            <div className="text-center mb-16 space-y-6 animate-fade-in">
              <h2 className="text-4xl md:text-6xl font-display font-bold leading-tight">
                Extrae el <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold to-amber-200">Alma</span> <br/>
                de tus Textos
              </h2>
              <p className="text-lg text-slate-400 max-w-2xl mx-auto font-serif leading-relaxed">
                Sube un PDF y nuestra IA diseccionará la sintaxis, el tono y el ritmo para crear un clon estilístico perfecto.
              </p>
            </div>
          )}

          {/* Main Content Area */}
          <div className="transition-all duration-500 ease-in-out">
            {appState === AppState.IDLE && (
              <div className="max-w-xl mx-auto">
                <FileUpload onFileSelect={handleFileSelect} isProcessing={false} />
              </div>
            )}

            {(appState === AppState.READING_PDF || appState === AppState.ANALYZING) && (
              <div className="max-w-xl mx-auto text-center py-20">
                <div className="relative w-24 h-24 mx-auto mb-8">
                  <div className="absolute inset-0 border-4 border-slate-800 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-gold rounded-full border-t-transparent animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl">✨</span>
                  </div>
                </div>
                <h3 className="text-2xl font-display text-white mb-2">
                  {appState === AppState.READING_PDF ? "Leyendo el Manuscrito..." : "Extrayendo la Esencia..."}
                </h3>
                <p className="text-mist font-serif italic">
                  {corpus.length > 0 ? `Analizando ${corpus.length + (appState === AppState.READING_PDF ? 1 : 0)} documentos en conjunto.` : "Analizando patrones sintácticos y voz narrativa."}
                </p>
              </div>
            )}

            {appState === AppState.ERROR && (
              <div className="max-w-xl mx-auto text-center py-10 bg-red-900/10 border border-red-500/20 rounded-2xl">
                <div className="text-red-400 text-5xl mb-4">⚠️</div>
                <h3 className="text-xl font-bold text-red-200 mb-2">Algo salió mal</h3>
                <p className="text-red-300/80 mb-6 px-4">{errorMsg}</p>
                <div className="flex justify-center space-x-4">
                    <button 
                    onClick={() => setAppState(corpus.length > 0 ? AppState.COMPLETE : AppState.IDLE)}
                    className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                    >
                    Volver
                    </button>
                    {corpus.length === 0 && (
                        <button 
                        onClick={handleReset}
                        className="px-6 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg transition-colors"
                        >
                        Reiniciar
                        </button>
                    )}
                </div>
              </div>
            )}

            {appState === AppState.COMPLETE && analysis && (
              <div className="space-y-12">
                <AnalysisResult 
                    analysis={analysis} 
                    onReset={handleReset} 
                    onRefine={handleFileSelect}
                    docCount={corpus.length}
                />
                <StyleTester analysis={analysis} />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}