import React, { useCallback } from 'react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
  variant?: 'default' | 'compact';
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, isProcessing, variant = 'default' }) => {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (isProcessing) return;
      
      const file = e.dataTransfer.files[0];
      if (file && file.type === 'application/pdf') {
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
          accept="application/pdf"
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isProcessing}
        />
        <div className="flex items-center justify-center space-x-3">
          <svg className="w-5 h-5 text-gold/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
          </svg>
          <span className="text-sm font-medium text-mist group-hover:text-ethereal transition-colors">
            Añadir otro PDF para afinar estilo
          </span>
        </div>
      </div>
    );
  }

  return (
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
        accept="application/pdf"
        onChange={handleInputChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        disabled={isProcessing}
      />
      
      <div className="space-y-4">
        <div className="w-16 h-16 mx-auto bg-slate-800 rounded-full flex items-center justify-center group-hover:bg-slate-700 transition-colors">
          <svg className="w-8 h-8 text-gold" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h3 className="text-xl font-display font-semibold text-ethereal mb-2">
            Sube tu PDF aquí
          </h3>
          <p className="text-mist text-sm max-w-xs mx-auto">
            Arrastra y suelta o haz clic para seleccionar un archivo PDF que contenga el texto de referencia.
          </p>
        </div>
        <div className="pt-4">
           <span className="inline-block px-4 py-1.5 rounded-full bg-slate-800 text-xs font-semibold text-gold/80 border border-slate-700">
             Soporta solo PDF
           </span>
        </div>
      </div>
    </div>
  );
};