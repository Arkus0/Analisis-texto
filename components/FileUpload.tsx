import React, { useCallback, useState } from 'react';
import { AnalysisLens, LENS_DESCRIPTIONS } from '../types';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onTextSubmit?: (text: string) => void;
  isProcessing: boolean;
  variant?: 'default' | 'compact';
  selectedLens?: AnalysisLens;
  onLensChange?: (lens: AnalysisLens) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ 
  onFileSelect, 
  onTextSubmit,
  isProcessing, 
  variant = 'default',
  selectedLens,
  onLensChange
}) => {
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pastedText, setPastedText] = useState('');

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (isProcessing) return;
      
      const file = e.dataTransfer.files[0];
      if (file && (file.type === 'application/pdf' || file.type === 'text/plain')) {
        onFileSelect(file);
      }
    },
    [onFileSelect, isProcessing]
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handlePasteSubmit = () => {
    if (pastedText.trim().length > 50) {
      if (onTextSubmit) {
        onTextSubmit(pastedText);
      }
      setShowPasteModal(false);
    }
  };

  // Lens Selector Component
  const LensSelector = () => (
    <div className="flex justify-center gap-2 mb-6">
      {(Object.keys(LENS_DESCRIPTIONS) as AnalysisLens[]).map((lens) => (
        <button
          key={lens}
          onClick={() => onLensChange && onLensChange(lens)}
          className={`
            px-3 py-2 rounded-lg text-xs font-bold transition-all border
            ${selectedLens === lens 
              ? 'bg-gold/20 border-gold text-gold shadow-[0_0_10px_rgba(251,191,36,0.2)]' 
              : 'bg-slate-900 border-slate-700 text-slate-500 hover:text-slate-300 hover:border-slate-500'}
          `}
          title={LENS_DESCRIPTIONS[lens].desc}
        >
          {LENS_DESCRIPTIONS[lens].name}
        </button>
      ))}
    </div>
  );

  if (variant === 'compact') {
    return (
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`
          relative group cursor-pointer 
          border border-dashed border-slate-700 hover:border-gold/50 
          rounded-xl p-4 text-center transition-all duration-300
          bg-slate-900/30 hover:bg-slate-800/50
          ${isProcessing ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isProcessing}
        />
        <div className="flex items-center justify-center space-x-3">
          <svg className="w-5 h-5 text-gold/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
          </svg>
          <span className="text-sm font-medium text-mist group-hover:text-ethereal transition-colors">
            Añadir PDF o TXT para afinar
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Lens Selector above upload area */}
      <div className="text-center">
        <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">Lente de Análisis</label>
        <LensSelector />
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`
          relative group cursor-pointer 
          border-2 border-dashed border-slate-700 hover:border-gold/50 
          rounded-2xl p-12 text-center transition-all duration-300
          bg-slate-900/50 backdrop-blur-sm
          ${isProcessing ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          disabled={isProcessing}
        />
        
        <div className="space-y-4 relative z-0">
          <div className="w-16 h-16 mx-auto bg-slate-800 rounded-full flex items-center justify-center group-hover:bg-slate-700 transition-colors">
            <svg className="w-8 h-8 text-gold" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-display font-semibold text-ethereal mb-2">
              Sube tu Documento
            </h3>
            <p className="text-mist text-sm max-w-xs mx-auto">
              Arrastra PDF o TXT. También puedes pegar texto directamente.
            </p>
          </div>
          <div className="pt-4 flex justify-center gap-3">
             <span className="inline-block px-4 py-1.5 rounded-full bg-slate-800 text-xs font-semibold text-gold/80 border border-slate-700">
               PDF / TXT
             </span>
             <button
               onClick={(e) => {
                 e.stopPropagation();
                 e.preventDefault();
                 setShowPasteModal(true);
               }} 
               className="inline-block px-4 py-1.5 rounded-full bg-slate-700 hover:bg-slate-600 text-xs font-semibold text-white border border-slate-600 relative z-20"
             >
               Pegar Texto
             </button>
          </div>
        </div>
      </div>

      {/* Paste Modal */}
      {showPasteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-display text-white mb-4">Pegar Texto Directo</h3>
            <textarea 
              className="w-full h-64 bg-black/40 border border-slate-700 rounded-lg p-4 text-slate-300 focus:outline-none focus:border-gold/50 text-sm font-serif"
              placeholder="Pega aquí el capítulo, artículo o ensayo..."
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
            />
            <div className="flex justify-end gap-3 mt-4">
              <button 
                onClick={() => setShowPasteModal(false)}
                className="px-4 py-2 text-slate-400 hover:text-white text-sm"
              >
                Cancelar
              </button>
              <button 
                onClick={handlePasteSubmit}
                disabled={pastedText.length < 50}
                className="px-6 py-2 bg-gold text-black font-bold rounded-lg hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Analizar Texto
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};