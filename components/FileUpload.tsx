import React, { useCallback, useState } from 'react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onTextSubmit?: (text: string) => void;
  isProcessing: boolean;
  variant?: 'default' | 'compact';
}

export const FileUpload: React.FC<FileUploadProps> = ({ 
  onFileSelect, 
  onTextSubmit,
  isProcessing, 
  variant = 'default'
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

  if (variant === 'compact') {
    return (
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`
          relative group cursor-pointer 
          border border-dashed border-slate-700 hover:border-rose-500/50 
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
          <svg className="w-5 h-5 text-rose-500/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
          </svg>
          <span className="text-sm font-medium text-mist group-hover:text-ethereal transition-colors">
            Añadir más espécimenes (PDF/TXT)
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`
          relative group cursor-pointer 
          border-2 border-dashed border-slate-700 hover:border-rose-500/50 
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
            <svg className="w-8 h-8 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-display font-semibold text-ethereal mb-2">
              Iniciar Disección
            </h3>
            <p className="text-mist text-sm max-w-xs mx-auto font-serif italic">
              Arrastra el PDF o TXT para extraer su ADN estilístico completo.
            </p>
          </div>
          <div className="pt-4 flex justify-center gap-3">
             <span className="inline-block px-4 py-1.5 rounded-full bg-slate-800 text-xs font-semibold text-rose-400/80 border border-slate-700">
               SOPORTE TOTAL PDF / TXT
             </span>
             <button
               onClick={(e) => {
                 e.stopPropagation();
                 e.preventDefault();
                 setShowPasteModal(true);
               }} 
               className="inline-block px-4 py-1.5 rounded-full bg-rose-900/40 hover:bg-rose-800/60 text-xs font-semibold text-white border border-rose-500/30 relative z-20"
             >
               Pegar Texto Directo
             </button>
          </div>
        </div>
      </div>

      {/* Paste Modal */}
      {showPasteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-display text-white mb-4">Muestra de Texto Directa</h3>
            <textarea 
              className="w-full h-64 bg-black/40 border border-slate-700 rounded-lg p-4 text-slate-300 focus:outline-none focus:border-rose-500/50 text-sm font-serif"
              placeholder="Pega aquí el contenido para la autopsia..."
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
            />
            <div className="flex justify-end gap-3 mt-4">
              <button 
                onClick={() => setShowPasteModal(false)}
                className="px-4 py-2 text-slate-400 hover:text-white text-sm"
              >
                Abortar
              </button>
              <button 
                onClick={handlePasteSubmit}
                disabled={pastedText.length < 50}
                className="px-6 py-2 bg-rose-600 text-white font-bold rounded-lg hover:bg-rose-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Analizar Muestra
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};