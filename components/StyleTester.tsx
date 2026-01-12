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
  
  // New States for Improvements
  const [temperature, setTemperature] = useState(0.9);
  const [currentSystemPrompt, setCurrentSystemPrompt] = useState(analysis.systemPrompt);
  const [feedbackModal, setFeedbackModal] = useState<{msgIndex: number, isOpen: boolean}>({ msgIndex: -1, isOpen: false });
  const [feedbackReason, setFeedbackReason] = useState("");

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
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    // CONTEXT WINDOW MANAGEMENT: 
    // Only send the last 15 messages to API to save tokens and keep context fresh.
    const contextWindow = newMessages.slice(-15);

    try {
      const responseText = await getChatResponse(
        contextWindow, 
        currentSystemPrompt, 
        userMsg.content,
        humanConfig,
        temperature
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

  const handleNegativeFeedback = async () => {
    if (!feedbackReason.trim()) return;

    // 1. Inject Negative Constraint into System Prompt
    const constraint = `\n<negative_constraint priority="critical">USER FEEDBACK: ${feedbackReason}</negative_constraint>`;
    const updatedPrompt = currentSystemPrompt + constraint;
    setCurrentSystemPrompt(updatedPrompt);

    // 2. Mark message as negative feedback
    const msgIndex = feedbackModal.msgIndex;
    const updatedMessages = [...messages];
    updatedMessages[msgIndex].feedback = 'negative';
    
    // 3. Regenerate response? 
    // For simplicity, we just acknowledge the feedback and the user can try again.
    // Or we can remove the bad message and regenerate. Let's remove and regenerate.
    
    // Remove the bad model response
    const previousUserMsg = messages[msgIndex - 1];
    const historyBeforeBadResponse = messages.slice(0, msgIndex - 1).slice(-15);
    
    setFeedbackModal({ msgIndex: -1, isOpen: false });
    setFeedbackReason("");
    setMessages(updatedMessages.slice(0, msgIndex)); // Remove bad response
    setIsLoading(true);

    try {
         // Retry with updated prompt
         const responseText = await getChatResponse(
            historyBeforeBadResponse,
            updatedPrompt,
            previousUserMsg.content,
            humanConfig,
            temperature
         );
         setMessages(prev => [...prev, { role: 'model', content: responseText }]);
    } catch(e) {
        console.error(e);
        setIsLoading(false);
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <div className="mt-12 max-w-4xl mx-auto animate-fade-in delay-100 relative">
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
          <span>Configuración</span>
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-6 bg-slate-900/80 border border-gold/30 rounded-xl p-5 animate-fade-in">
          
          {/* Temperature Slider */}
          <div className="mb-6 pb-6 border-b border-slate-700">
             <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-semibold text-ethereal">Creatividad (Temperatura)</label>
                <span className="text-xs text-gold font-mono">{temperature.toFixed(1)}</span>
             </div>
             <input 
               type="range" 
               min="0.1" 
               max="1.5" 
               step="0.1" 
               value={temperature} 
               onChange={(e) => setTemperature(parseFloat(e.target.value))}
               className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-gold"
             />
             <div className="flex justify-between text-[10px] text-mist mt-1 font-mono">
                <span>Rígido / Técnico</span>
                <span>Alucinado / Poético</span>
             </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
              <div>
                <span className="block text-sm font-semibold text-ethereal">Burstiness (Caos)</span>
                <span className="text-xs text-mist">Mezcla oraciones muy cortas y largas.</span>
              </div>
              <input type="checkbox" checked={humanConfig.burstiness} onChange={() => toggleConfig('burstiness')} className="w-5 h-5 accent-gold bg-slate-700 border-slate-600 rounded focus:ring-gold" />
            </label>

            <label className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
              <div>
                <span className="block text-sm font-semibold text-ethereal">Toque Personal</span>
                <span className="text-xs text-mist">Añade opiniones y subjetividad.</span>
              </div>
              <input type="checkbox" checked={humanConfig.personalTouch} onChange={() => toggleConfig('personalTouch')} className="w-5 h-5 accent-gold bg-slate-700 border-slate-600 rounded focus:ring-gold" />
            </label>
             {/* ... other existing checkboxes ... */}
          </div>
        </div>
      )}
      
      {/* Feedback Modal */}
      {feedbackModal.isOpen && (
         <div className="absolute inset-0 z-20 bg-black/80 backdrop-blur-sm flex items-center justify-center rounded-2xl">
            <div className="bg-slate-900 border border-red-500/50 p-6 rounded-xl w-3/4 max-w-md shadow-2xl">
               <h4 className="text-red-400 font-bold mb-2">Refuerzo Negativo</h4>
               <p className="text-xs text-slate-400 mb-4">¿Por qué esa respuesta no se sintió auténtica? Esto ajustará el modelo inmediatamente.</p>
               <input 
                 autoFocus
                 type="text" 
                 className="w-full bg-black/50 border border-slate-700 rounded p-2 text-sm text-white focus:border-red-500 focus:outline-none mb-4"
                 placeholder="Ej: Demasiado formal, usó la palabra 'sinergia'..."
                 value={feedbackReason}
                 onChange={(e) => setFeedbackReason(e.target.value)}
                 onKeyDown={(e) => e.key === 'Enter' && handleNegativeFeedback()}
               />
               <div className="flex justify-end gap-2">
                  <button onClick={() => setFeedbackModal({msgIndex: -1, isOpen: false})} className="text-xs text-slate-500 hover:text-white px-3 py-1">Cancelar</button>
                  <button onClick={handleNegativeFeedback} className="bg-red-900/50 border border-red-500/50 text-red-200 text-xs px-4 py-1.5 rounded hover:bg-red-800 transition-colors">Corregir y Reintentar</button>
               </div>
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
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} group`}
            >
              <div className="flex flex-col gap-1 max-w-[85%]">
                  <div 
                    className={`
                      rounded-2xl p-4 text-sm leading-relaxed relative
                      ${msg.role === 'user' 
                        ? 'bg-slate-800 text-mist rounded-br-none' 
                        : 'bg-indigo-900/30 border border-indigo-500/30 text-ethereal rounded-bl-none font-serif shadow-[0_0_15px_rgba(99,102,241,0.1)]'}
                    `}
                  >
                    {msg.content}
                  </div>
                  
                  {/* RLHF Controls for Model Messages */}
                  {msg.role === 'model' && (
                     <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity px-2">
                        <button 
                           onClick={() => {
                              const updated = [...messages];
                              updated[idx].feedback = 'positive';
                              setMessages(updated);
                           }}
                           className={`text-[10px] flex items-center gap-1 ${msg.feedback === 'positive' ? 'text-green-400' : 'text-slate-600 hover:text-green-400'}`}
                        >
                           <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>
                        </button>
                        <button 
                           onClick={() => setFeedbackModal({ msgIndex: idx, isOpen: true })}
                           className={`text-[10px] flex items-center gap-1 ${msg.feedback === 'negative' ? 'text-red-400' : 'text-slate-600 hover:text-red-400'}`}
                        >
                           <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.007L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" /></svg>
                        </button>
                     </div>
                  )}
              </div>
            </div>
          ))}
          {/* Loading indicator... */}
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-slate-900">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe un mensaje..."
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