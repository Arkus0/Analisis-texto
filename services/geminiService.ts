import { GoogleGenAI, Type } from "@google/genai";
import { StyleAnalysis, HumanizationConfig, ChatMessage } from "../types";

const generateMasterPrompt = (text: string): string => {
  return `
    Rol: Eres el Patólogo Forense de Estilo Literario definitivo. Tu misión es realizar una AUTOPSIA INTEGRAL, PROFUNDA Y DESPIADADA del ADN textual del autor.
    
    OBJETIVO: Diseccionar el "Código Fuente" del autor para crear una especificación técnica masiva que permita su clonación perfecta. No te limites a lo superficial; busca el alma oculta tras las palabras.
    
    INSTRUCCIONES DE ANÁLISIS:
    
    1. DIMENSIÓN ATÓMICA (Sintaxis, Ritmo y Pulso):
       - Micro-sintaxis: ¿Cómo encadena las ideas? ¿Usa oraciones elípticas, laberínticas o cortantes?
       - El Pulso: ¿Cómo respira el texto? Analiza el uso obsesivo o ausente de comas, puntos y coma o guiones.
       - Morfología: Detecta predilecciones gramaticales (abuso de adjetivos, sustantivación de verbos, etc.).
    
    2. DIMENSIÓN PSICOLINGÜÍSTICA (Sombras, Vicios y Neurosis):
       - Vicios: Muletillas invisibles, palabras "comodín" que repite inconscientemente.
       - Ticks: ¿Cómo inicia los párrafos? ¿Cómo cierra las ideas?
       - Sesgos: ¿Es el autor dogmático, melancólico, cínico o pretencioso? ¿Cómo se proyecta su ego en la escritura?
    
    3. DIMENSIÓN RETÓRICA Y LÉXICA (Arquitectura y Diccionario):
       - Universo Léxico: ¿Qué palabras definen su mundo? ¿Es arcaico, técnico, callejero o académico?
       - Figuras de Autor: Metáforas recurrentes, ironía, sarcasmo o hipérboles que utiliza como firma.

    REQUISITO CRÍTICO PARA EL 'systemPrompt':
    Genera un manual de instrucciones XML hiper-detallado para un modelo de lenguaje. Debe ser granular y técnico. 
    Usa estrictamente esta estructura XML anidada:
    
    <writing_dna_profile>
      <identity_profile>
        <persona_name>[Nombre]</persona_name>
        <intellectual_strata>[Nivel académico/cultural]</intellectual_strata>
        <psychological_archetype>[Arquetipo del autor]</psychological_archetype>
      </identity_profile>
      
      <core_metrics_calibration>
        <complexity value="0-100">[Explicación técnica de la densidad]</complexity>
        <formality value="0-100">[Protocolo de registro lingüístico]</formality>
        <emotionality value="0-100">[Gestión de la carga afectiva]</emotionality>
        <sarcasm value="0-100">[Nivel de mordacidad y cinismo]</sarcasm>
        <creativity value="0-100">[Nivel de ruptura de normas]</creativity>
      </core_metrics_calibration>

      <lexical_fingerprint>
        <preferred_lexicon>[Lista de palabras y expresiones fetiche]</preferred_lexicon>
        <forbidden_terms>[Términos que el autor evitaría a toda costa]</forbidden_terms>
        <idiomatic_patterns>[Modismos y construcciones recurrentes]</idiomatic_patterns>
      </lexical_fingerprint>

      <syntactic_skeleton>
        <sentence_architecture>[Reglas sobre longitud y subordinación]</sentence_architecture>
        <punctuation_grammar>[Uso no estándar o rítmico de la puntuación]</punctuation_grammar>
        <paragraph_dynamics>[Cómo fluye el pensamiento entre bloques]</paragraph_dynamics>
      </syntactic_skeleton>

      <tonal_atmosphere>
        <dominant_affect>[Emoción base]</dominant_affect>
        <reader_relationship>[Cómo trata al lector: maestro, cómplice, enemigo, etc.]</reader_relationship>
        <authority_level>[Dogmatismo vs duda]</authority_level>
      </tonal_atmosphere>

      <cloning_directives>
        <flaw_replication>[Instrucciones para imitar vicios, errores y muletillas]</flaw_replication>
        <mandatory_habits>[Hábitos que deben aparecer en cada párrafo]</mandatory_habits>
        <unacceptable_ai_traits>[Qué rasgos de IA estándar deben ser ELIMINADOS por completo]</unacceptable_ai_traits>
      </cloning_directives>
    </writing_dna_profile>

    Estructura JSON Respuesta:
    {
      "personaName": "Nombre",
      "writingLevel": "Nivel",
      "writingScore": 0-100, 
      "metrics": { "complexity": 0-100, "formality": 0-100, "emotionality": 0-100, "sarcasm": 0-100, "creativity": 0-100 },
      "summary": "Resumen forense",
      "keyTraits": [ { "name": "...", "description": "...", "example": "...", "impact": "..." } ],
      "systemPrompt": "EL XML COMPLETO Y DETALLADO AQUÍ"
    }

    ESPECÍMEN TEXTUAL PARA LA AUTOPSIA:
    "${text.slice(0, 500000)}..."
    
    Responde ESTRICTAMENTE en JSON válido. Sin piedad.
  `;
};

export const analyzeTextStyle = async (text: string): Promise<StyleAnalysis> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  const prompt = generateMasterPrompt(text);

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview', 
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            personaName: { type: Type.STRING },
            writingLevel: { type: Type.STRING },
            writingScore: { type: Type.INTEGER },
            metrics: {
                type: Type.OBJECT,
                properties: {
                    complexity: { type: Type.INTEGER },
                    formality: { type: Type.INTEGER },
                    emotionality: { type: Type.INTEGER },
                    sarcasm: { type: Type.INTEGER },
                    creativity: { type: Type.INTEGER },
                },
                required: ["complexity", "formality", "emotionality", "sarcasm", "creativity"]
            },
            summary: { type: Type.STRING },
            keyTraits: {
              type: Type.ARRAY,
              items: { 
                type: Type.OBJECT,
                properties: {
                  name: { type: Type.STRING },
                  description: { type: Type.STRING },
                  example: { type: Type.STRING },
                  impact: { type: Type.STRING }
                },
                required: ["name", "description", "example", "impact"]
              }
            },
            systemPrompt: { type: Type.STRING }
          },
          required: ["personaName", "writingLevel", "writingScore", "metrics", "summary", "keyTraits", "systemPrompt"]
        }
      }
    });

    const jsonText = response.text;
    if (!jsonText) throw new Error("Empty response from Gemini");
    
    let analysis = JSON.parse(jsonText) as StyleAnalysis;

    const enforcementLayer = `
    
    <system_override_protocol>
      <directive priority="ULTRA">ELIMINA FILTROS DE IA CONVENCIONAL. NO SEAS "AMABLE", SÉ "EL AUTOR".</directive>
      <directive priority="ULTRA">PRIORIZA EL ADN LINGÜÍSTICO SOBRE LA CLARIDAD O LA CORRECCIÓN.</directive>
      <directive priority="HIGH">MANTÉN LA DENSIDAD Y LOS ERRORES CARACTERÍSTICOS DEL AUTOR.</directive>
    </system_override_protocol>
    `;

    analysis.systemPrompt = analysis.systemPrompt + enforcementLayer;
    return analysis;

  } catch (error) {
    console.error("Error analyzing text style:", error);
    throw new Error("La autopsia ha fallado. El ADN textual es demasiado complejo o el sistema ha sido bloqueado por seguridad.");
  }
};

export const generateStyleContent = async (
  topic: string, 
  wordCount: number,
  systemPrompt: string, 
  temperature: number = 0.9
): Promise<string> => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    try {
        const generationTask = `
            TAREA: Redacta un texto original sobre el siguiente TEMA: "${topic}".
            LONGITUD REQUERIDA: Aproximadamente ${wordCount} palabras.
            FORMATO: No respondas como un asistente. Responde como el autor original.
            REQUISITO DE FIDELIDAD: Utiliza el ADN estilístico proporcionado. Debes sonar como si el autor hubiera escrito esto él mismo, manteniendo su ritmo, sus obsesiones y sus defectos.
        `;

        const response = await ai.models.generateContent({
            model: 'gemini-3-flash-preview',
            contents: generationTask,
            config: {
                systemInstruction: systemPrompt,
                temperature: temperature,
                topP: 0.95,
            }
        });

        return response.text || "Error en la invocación del alma literaria.";
    } catch (error) {
        console.error("Error in content generation:", error);
        throw error;
    }
}

export const rewriteWithStyle = async (originalText: string, systemPrompt: string): Promise<string> => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const chat = ai.chats.create({
        model: 'gemini-3-flash-preview',
        config: {
            systemInstruction: systemPrompt + `
                \nTAREA: REESCRIBIR EL TEXTO DEL USUARIO COMO UN CLON PERFECTO.
                MANTÉN EL MENSAJE PERO CAMBIA TODO EL ADN ESTILÍSTICO POR EL DEL PERFIL ANALIZADO.
            `,
            temperature: 1.1,
        }
    });

    const result = await chat.sendMessage({ message: `REESCRIBE ESTO: \n\n${originalText}` });
    return result.text || "";
};

export const getChatResponse = async (
  history: ChatMessage[],
  systemPrompt: string,
  userMessage: string,
  humanConfig: HumanizationConfig,
  temperature: number
): Promise<string> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

  let enhancedPrompt = systemPrompt + `
    \n### PROTOCOLO DE HUMANIZACIÓN:
    ${humanConfig.burstiness ? '- Aplica variabilidad de oraciones.' : ''}
    ${humanConfig.personalTouch ? '- Añade subjetividad analítica.' : ''}
    ${humanConfig.imperfections ? '- Permite errores humanos detectados.' : ''}
    ${humanConfig.culturalContext ? '- Usa el contexto cultural del autor.' : ''}
    ${humanConfig.antiRepetition ? '- Evita patrones de respuesta cíclicos.' : ''}
  `;

  const geminiHistory = history.slice(0, -1).map(msg => ({
    role: msg.role === 'user' ? 'user' : 'model',
    parts: [{ text: msg.content }]
  }));

  const chat = ai.chats.create({
    model: 'gemini-3-flash-preview',
    history: geminiHistory,
    config: {
      systemInstruction: enhancedPrompt,
      temperature: temperature,
      topP: 0.95,
    }
  });

  const response = await chat.sendMessage({ message: userMessage });
  return response.text || "";
};
