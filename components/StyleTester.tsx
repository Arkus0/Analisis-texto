import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, StyleAnalysis, HumanizationConfig } from '../types';
import { getChatResponse } from '../services/geminiService';

interface StyleTesterProps {
  analysis: StyleAnalysis;
}

export const StyleTester: React.FC<StyleTesterProps> = ({ analysis }) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Humanization Config State
  const [humanConfig, setHumanConfig] = useState<HumanizationConfig>({
    burstiness: true,
    imperfections: false,
    personalTouch: true,
    culturalContext: false,
    antiRepetition: true,
  });

  const toggleConfig = (key: keyof HumanizationConfig) => {
    setHumanConfig(prev => ({ ...prev, [key]: !prev[key] }));
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const responseText = await getChatResponse(
        messages, 
        analysis.systemPrompt, 
        userMsg.content,
        humanConfig // Pass the current config
      );

      if (responseText) {
        setMessages(prev => [...prev, { role: 'model', content: responseText }]);
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'model', content: "Error al generar la respuesta. Por favor intenta de nuevo." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mt-12 max-w-4xl mx-auto animate-fade-in delay-100">
      <div className="flex items-center justify-between mb-4 px-2">
        <div className="flex items-center space-x-3">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <h2 className="text-xl font-display text-ethereal">Prueba el Estilo</h2>
        </div>
        
        <button 
          onClick={() => setShowSettings(!showSettings)}
          className={`
            flex items-center space-x-2 text-xs uppercase font-bold tracking-wider px-3 py-1.5 rounded-lg border transition-all
            ${showSettings 
              ? 'bg-gold/10 border-gold text-gold' 
              : 'bg-slate-800 border-slate-700 text-mist hover:text-white'}
          `}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          <span>Modo Sigilo (Anti-Detectores)</span>
        </button>
      </div>

      {/* Humanization Settings Panel */}
      {showSettings && (
        <div className="mb-6 bg-slate-900/80 border border-gold/30 rounded-xl p-5 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <label className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
              <div>
                <span className="block text-sm font-semibold text-ethereal">Burstiness (Caos Estructural)</span>
                <span className="text-xs text-mist">Mezcla oraciones muy cortas y largas.</span>
              </div>
              <input 
                type="checkbox" 
                checked={humanConfig.burstiness} 
                onChange={() => toggleConfig('burstiness')}
                className="w-5 h-5 accent-gold bg-slate-700 border-slate-600 rounded focus:ring-gold" 
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
              <div>
                <span className="block text-sm font-semibold text-ethereal">Toque Personal</span>
                <span className="text-xs text-mist">Añade opiniones y subjetividad.</span>
              </div>
              <input 
                type="checkbox" 
                checked={humanConfig.personalTouch} 
                onChange={() => toggleConfig('personalTouch')}
                className="w-5 h-5 accent-gold bg-slate-700 border-slate-600 rounded focus:ring-gold" 
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
              <div>
                <span className="block text-sm font-semibold text-ethereal">Imperfecciones Humanas</span>
                <span className="text-xs text-mist">Coloquialismos, muletillas ("pues", "ya sabes").</span>
              </div>
              <input 
                type="checkbox" 
                checked={humanConfig.imperfections} 
                onChange={() => toggleConfig('imperfections')}
                className="w-5 h-5 accent-gold bg-slate-700 border-slate-600 rounded focus:ring-gold" 
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
              <div>
                <span className="block text-sm font-semibold text-ethereal">Anti-Repetición</span>
                <span className="text-xs text-mist">Elimina frases cliché de IA y vaguedades.</span>
              </div>
              <input 
                type="checkbox" 
                checked={humanConfig.antiRepetition} 
                onChange={() => toggleConfig('antiRepetition')}
                className="w-5 h-5 accent-gold bg-slate-700 border-slate-600 rounded focus:ring-gold" 
              />
            </label>

             <label className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors md:col-span-2">
              <div>
                <span className="block text-sm font-semibold text-ethereal">Contexto Cultural / Humor</span>
                <span className="text-xs text-mist">Referencias al mundo real e ironía.</span>
              </div>
              <input 
                type="checkbox" 
                checked={humanConfig.culturalContext} 
                onChange={() => toggleConfig('culturalContext')}
                className="w-5 h-5 accent-gold bg-slate-700 border-slate-600 rounded focus:ring-gold" 
              />
            </label>

          </div>
        </div>
      )}
      
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        {/* Chat Area */}
        <div 
            ref={scrollRef}
            className="h-[400px] overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-slate-900 to-black/80"
        >
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-600 opacity-60">
              <svg className="w-12 h-12 mb-4 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <p className="font-serif">Escribe algo para hablar con<br/> <span className="text-gold font-sans font-bold">{analysis.personaName}</span></p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`
                  max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed
                  ${msg.role === 'user' 
                    ? 'bg-slate-800 text-mist rounded-br-none' 
                    : 'bg-indigo-900/30 border border-indigo-500/30 text-ethereal rounded-bl-none font-serif shadow-[0_0_15px_rgba(99,102,241,0.1)]'}
                `}
              >
                {msg.content}
              </div>
            </div>
          ))}

            {isLoading && (
                 <div className="flex justify-start">
                    <div className="bg-indigo-900/10 border border-indigo-500/10 rounded-2xl rounded-bl-none p-4 flex items-center space-x-2">
                        <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce delay-75"></div>
                        <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce delay-150"></div>
                    </div>
                </div>
            )}
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-slate-900">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe un mensaje para probar el estilo..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl py-4 pl-5 pr-12 text-ethereal focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/50 transition-all font-sans"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gold hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};