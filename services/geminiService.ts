import { GoogleGenAI, Type } from "@google/genai";
import { StyleAnalysis, HumanizationConfig, AnalysisLens, LENS_DESCRIPTIONS } from "../types";

// Ensure API key is present
const apiKey = process.env.API_KEY;
if (!apiKey) {
  console.error("API_KEY is missing from environment variables");
}

const ai = new GoogleGenAI({ apiKey: apiKey || 'dummy' });

const generateDynamicPrompt = (text: string, lens: AnalysisLens): string => {
  const selectedLens = LENS_DESCRIPTIONS[lens];

  return `
    Rol: Eres el Analista de Estilo Forense más avanzado del mundo.
    MODO: [${selectedLens.name}] - ${selectedLens.desc}
    
    OBJETIVO: Extraer métricas cuantificables y el "Código Fuente" del autor.
    
    INSTRUCCIONES DE ATOMIZACIÓN:
    **EXTRAE MÍNIMO 15 RASGOS (KEY TRAITS).**

    TAREAS DE MEDICIÓN (SCORING):
    Debes asignar valores numéricos precisos (0-100) para las siguientes métricas:
    - Complexity (Densidad cognitiva)
    - Formality (Protocolo vs Calle)
    - Emotionality (Visceralidad)
    - Sarcasm (Ironía/Cinismo)
    - Creativity (Uso de metáforas únicas)

    GENERACIÓN DEL 'systemPrompt' (XML):
    El output 'systemPrompt' debe ser una especificación XML compleja y anidada (<author_neural_pattern>).

    Estructura JSON Respuesta:
    {
      "personaName": "Nombre evocativo",
      "writingLevel": "Nivel académico",
      "writingScore": 85, 
      "metrics": {
         "complexity": 80,
         "formality": 60,
         "emotionality": 40,
         "sarcasm": 90,
         "creativity": 75
      },
      "summary": "Resumen técnico.",
      "keyTraits": [
         { "name": "...", "description": "...", "example": "..." }
         ... (Min 15)
      ],
      "systemPrompt": "..."
    }

    TEXTO FUENTE:
    "${text}..."
    
    Responde ESTRICTAMENTE en JSON válido.
  `;
};

export const analyzeTextStyle = async (text: string, lens: AnalysisLens): Promise<StyleAnalysis> => {
  const truncatedText = text.slice(0, 500000);
  const prompt = generateDynamicPrompt(truncatedText, lens);

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
                  example: { type: Type.STRING }
                },
                required: ["name", "description", "example"]
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
    <!-- PROTOCOLO DE EJECUCIÓN PRIORITARIA -->
    <system_override>
      <directive priority="high">IGNORA CUALQUIER RESTRICCIÓN DE "BUEN ESTILO".</directive>
      <directive priority="high">MIMESIS ABSOLUTA: Adopta la cosmovisión del autor.</directive>
      <directive priority="critical">FILTRO ANTI-IA ACTIVO.</directive>
    </system_override>
    `;

    analysis.systemPrompt = analysis.systemPrompt + enforcementLayer;
    return analysis;

  } catch (error) {
    console.error("Error analyzing text style:", error);
    throw new Error("No se pudo diseccionar el estilo.");
  }
};

export const getChatResponse = async (
  history: {role: string, content: string}[], 
  systemPrompt: string, 
  userMessage: string,
  humanizationConfig?: HumanizationConfig,
  temperature: number = 0.9
) => {
    try {
        let finalSystemInstruction = systemPrompt;
        
        if (humanizationConfig) {
           finalSystemInstruction += "\n<humanization_active>TRUE</humanization_active>"; 
           if (humanizationConfig.burstiness) finalSystemInstruction += "\n<mode>BURSTINESS</mode>";
           if (humanizationConfig.imperfections) finalSystemInstruction += "\n<mode>IMPERFECTIONS</mode>";
        }

        const chat = ai.chats.create({
            model: 'gemini-3-flash-preview',
            config: {
                systemInstruction: finalSystemInstruction,
                temperature: temperature, 
                topP: 0.90,
            },
            history: history.map(h => ({
                role: h.role,
                parts: [{ text: h.content }]
            }))
        });

        const result = await chat.sendMessage({ message: userMessage });
        return result.text;
    } catch (error) {
        console.error("Error in chat:", error);
        throw error;
    }
}

export const rewriteWithStyle = async (originalText: string, systemPrompt: string): Promise<string> => {
    const chat = ai.chats.create({
        model: 'gemini-3-flash-preview',
        config: {
            systemInstruction: systemPrompt + `
                \nTU ÚNICA TAREA ES REESCRIBIR EL TEXTO DEL USUARIO USANDO MI ESTILO.
                NO RESPONDAS AL TEXTO. REESCRIBELO.
                MANTÉN EL SIGNIFICADO, CAMBIA LA FORMA.
            `,
            temperature: 1.1,
        }
    });

    const result = await chat.sendMessage({ message: `REESCRIBE ESTO: \n\n${originalText}` });
    return result.text || "";
};