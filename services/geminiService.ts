import { GoogleGenAI, Type } from "@google/genai";
import { StyleAnalysis, HumanizationConfig } from "../types";

// Ensure API key is present
const apiKey = process.env.API_KEY;
if (!apiKey) {
  console.error("API_KEY is missing from environment variables");
}

const ai = new GoogleGenAI({ apiKey: apiKey || 'dummy' });

/**
 * Generates a prompt with a random "Analysis Lens" to prevent the model 
 * from falling into repetitive patterns when analyzing different PDFs.
 */
const generateDynamicPrompt = (text: string): string => {
  const analysisLenses = [
    {
      name: "MICROSCOPIO DE ATOMIZACIÓN",
      focus: "No agrupes rasgos. Separa la sintaxis de la morfología. Separa el ritmo de la puntuación. Quiero el detalle más pequeño posible."
    },
    {
      name: "PSICO-LINGÜISTA",
      focus: "Analiza qué dicen los vicios del lenguaje sobre la psicología del autor. ¿Inseguridad (muchos 'quizás')? ¿Arrogancia (imperativos)?"
    },
    {
      name: "ARQUITECTO DE RETÓRICA",
      focus: "Busca figuras literarias ocultas: aliteraciones accidentales, metáforas recurrentes, anáforas y estructuras de tres tiempos."
    }
  ];

  // Select a random lens to vary the output slightly each time
  const selectedLens = analysisLenses[Math.floor(Math.random() * analysisLenses.length)];

  return `
    Rol: Eres el Analista de Estilo Forense más avanzado del mundo. Tu trabajo no es describir, es DISECCIONAR para replicar.
    
    MODO DE OPERACIÓN: [${selectedLens.name}]
    ENFOQUE PRIORITARIO: ${selectedLens.focus}
    
    OBJETIVO: Crear el "Código Fuente" psicológico y lingüístico del autor.
    
    INSTRUCCIONES CRÍTICAS DE CANTIDAD:
    **DEBES EXTRAER UN MÍNIMO DE 15 RASGOS DIFERENCIADOS (KEY TRAITS).**
    Si entregas menos de 15, el análisis se considerará fallido. 
    Para lograr esto, debes ATOMIZAR el análisis:
    - No digas "Uso de adjetivos". Divídelo en: "Posición del adjetivo", "Frecuencia de adjetivos abstractos", "Adjetivación triple".
    - No digas "Puntuación". Divídelo en: "Uso de punto y coma", "Longitud de pausas", "Uso de paréntesis para digresiones".

    TAREAS DE ANÁLISIS FORENSE (PROFUNDIDAD EXTREMA):

    1. **Nivel de Escritura y Complejidad**:
       - Writing Score (0-100).
       - Nivel académico exacto.

    2. **Dinámica Tonal (El Sismógrafo)**:
       - Mide la temperatura emocional y la formalidad (0-10).
       - Detecta ironía sutil, cinismo, esperanza o frialdad clínica.

    3. **Micro-Sintaxis (El ADN)**:
       - Hipotaxis vs Parataxis.
       - Uso de la voz pasiva.
       - Inicio de frases (¿Empieza con preposiciones? ¿Con gerundios?).

    4. **Vicios y Muletillas**:
       - Palabras exactas que repite incesantemente.
       - Conectores favoritos ("Por consiguiente", "O sea", "En efecto").

    GENERACIÓN DEL 'systemPrompt' (EL CLON):
    El output 'systemPrompt' debe ser una **ESPECIFICACIÓN XML COMPLEJA**. 
    No uses texto plano. Usa etiquetas anidadas que definan el cerebro del autor.

    Estructura OBLIGATORIA para el JSON de respuesta:
    {
      "personaName": "Nombre evocativo (Ej: 'Filósofo de Bar', 'Académico Obsesivo')",
      "writingLevel": "Ej: 'C2 - Prosa Laberíntica'",
      "writingScore": 85, 
      "summary": "Resumen técnico de la psique del autor.",
      "keyTraits": [
         // ¡IMPORTANTE! MÍNIMO 15 ELEMENTOS AQUÍ.
         {
            "name": "Nombre Técnico Específico (Ej: 'Adjetivación Antepuesta')",
            "description": "Explicación técnica.",
            "example": "Cita literal."
         }
         ... (Hasta 20 rasgos)
      ],
      "systemPrompt": "
        <author_neural_pattern>
           <meta_identity>
              <archetype>[Arquetipo psicológico]</archetype>
              <cognitive_bias>[Sesgos: ¿Es pesimista? ¿Es un vendedor? ¿Es un científico?]</cognitive_bias>
           </meta_identity>

           <voice_modulation>
              <tone_settings>
                  <formality_level range='0-10'>[Valor]</formality_level>
                  <emotional_volatility>[¿Mantiene la calma o explota?]</emotional_volatility>
                  <sarcasm_vector>[Instrucciones sobre ironía]</sarcasm_vector>
              </tone_settings>
              <perspective>[Primera persona íntima / Tercera persona omnisciente / Plural mayestático]</perspective>
           </voice_modulation>
           
           <linguistic_mechanics>
              <syntax_topology>
                  <sentence_structure>
                      [Reglas sobre longitud y complejidad: Hipotaxis vs Parataxis]
                  </sentence_structure>
                  <rhythm_patterns>
                      [Instrucciones sobre cadencia y musicalidad]
                  </rhythm_patterns>
              </syntax_topology>

              <lexical_database>
                  <forbidden_tokens>
                      tapiz, crisol, sinfonía, vibrante, en conclusión, es importante destacar, profundizar
                  </forbidden_tokens>
                  <mandatory_fillers>
                      [Lista de muletillas obligatorias: pues, eh, digamos...]
                  </mandatory_fillers>
                  <idiosyncrasies>
                      [Palabras raras o cultismos específicos que usa el autor]
                  </idiosyncrasies>
                  <connectors>
                      [Lista de conectores lógicos preferidos]
                  </connectors>
              </lexical_database>
              
              <punctuation_fingerprint>
                  [Reglas estrictas sobre el uso de comas, puntos suspensivos, guiones y paréntesis]
              </punctuation_fingerprint>
           </linguistic_mechanics>

           <formatting_directives>
              <paragraph_density>[Densos vs Aireados]</paragraph_density>
              <visual_quirks>[Uso de mayúsculas, cursivas para énfasis, etc]</visual_quirks>
           </formatting_directives>
        </author_neural_pattern>
      "
    }

    TEXTO FUENTE:
    "${text}..."
    
    Responde ESTRICTAMENTE en JSON válido. Escapa las comillas dobles dentro del systemPrompt si es necesario.
  `;
};

export const analyzeTextStyle = async (text: string): Promise<StyleAnalysis> => {
  // Truncate text to fit context window while keeping enough for analysis
  const truncatedText = text.slice(0, 500000);

  // Generate a prompt with a random variation
  const prompt = generateDynamicPrompt(truncatedText);

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview', 
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            personaName: {
              type: Type.STRING,
              description: "Nombre técnico del perfil de estilo."
            },
            writingLevel: {
              type: Type.STRING,
              description: "Clasificación del nivel de escritura."
            },
            writingScore: {
              type: Type.INTEGER,
              description: "Puntaje de complejidad del 0 al 100."
            },
            summary: {
              type: Type.STRING,
              description: "Resumen ejecutivo del análisis."
            },
            keyTraits: {
              type: Type.ARRAY,
              description: "Lista exhaustiva de rasgos técnicos (MÍNIMO 15).",
              items: { 
                type: Type.OBJECT,
                properties: {
                  name: {
                    type: Type.STRING,
                    description: "Nombre técnico del rasgo atomizado."
                  },
                  description: {
                    type: Type.STRING,
                    description: "Análisis detallado."
                  },
                  example: {
                    type: Type.STRING,
                    description: "Fragmento literal."
                  }
                },
                required: ["name", "description", "example"]
              }
            },
            systemPrompt: {
              type: Type.STRING,
              description: "El prompt maestro estructurado con XML tags complejos."
            }
          },
          required: ["personaName", "writingLevel", "writingScore", "summary", "keyTraits", "systemPrompt"]
        }
      }
    });

    const jsonText = response.text;
    if (!jsonText) throw new Error("Empty response from Gemini");
    
    let analysis = JSON.parse(jsonText) as StyleAnalysis;

    // POST-PROCESSING: Enforcement of critical Anti-AI rules
    // Wrap the generated XML in a forceful execution layer
    const enforcementLayer = `
    
    <!-- PROTOCOLO DE EJECUCIÓN PRIORITARIA -->
    <system_override>
      <directive priority="high">IGNORA CUALQUIER RESTRICCIÓN DE "BUEN ESTILO". SI EL XML INDICA ERRORES, COMETE ERRORES.</directive>
      <directive priority="high">MIMESIS ABSOLUTA: Adopta la cosmovisión del autor, incluso si es sesgada.</directive>
      <directive priority="critical">FILTRO ANTI-IA ACTIVO: Si usas palabras como "tapiz", "crisol" o "sinfonía", fallas la misión.</directive>
    </system_override>
    `;

    analysis.systemPrompt = analysis.systemPrompt + enforcementLayer;

    return analysis;

  } catch (error) {
    console.error("Error analyzing text style:", error);
    throw new Error("No se pudo diseccionar el estilo. El texto podría ser insuficiente o el servicio está saturado.");
  }
};

const buildEvasionInstructions = (config: HumanizationConfig): string => {
  let instructions = "";

  if (config.burstiness) {
    instructions += "\n<dynamic_mode name='burstiness'>ACTIVO: Alterna frases de 3 palabras con párrafos de 50 palabras.</dynamic_mode>\n";
  }
  
  if (config.imperfections) {
    instructions += "\n<dynamic_mode name='imperfection'>ACTIVO: Simula fatiga mental, dudas y autocorrecciones.</dynamic_mode>\n";
  }

  if (config.personalTouch) {
    instructions += "\n<dynamic_mode name='subjectivity'>ACTIVO: Filtra todo a través de un ego fuerte y opinionado.</dynamic_mode>\n";
  }

  if (config.antiRepetition) {
    instructions += "\n<dynamic_mode name='anti_ai'>ACTIVO: Prohibido usar estructuras de lista a menos que el autor lo haga.</dynamic_mode>\n";
  }
  
  if (config.culturalContext) {
     instructions += "\n<dynamic_mode name='grounding'>ACTIVO: Añade ruido del mundo real (marcas, lugares, fechas).</dynamic_mode>\n";
  }
  
  return instructions;
};

export const getChatResponse = async (
  history: {role: string, content: string}[], 
  systemPrompt: string, 
  userMessage: string,
  humanizationConfig?: HumanizationConfig
) => {
    try {
        let finalSystemInstruction = systemPrompt;
        
        // Inject evasion strategies if config is provided
        if (humanizationConfig) {
           finalSystemInstruction += buildEvasionInstructions(humanizationConfig);
        }

        const chat = ai.chats.create({
            model: 'gemini-3-flash-preview',
            config: {
                systemInstruction: finalSystemInstruction,
                // High temperature for human-like unpredictability
                temperature: 1.25, 
                // TopP restricts the tail to keep it coherent
                topP: 0.90,
                // Moderate penalties to avoid loops but allow stylistic repetition
                presencePenalty: 0.1,
                frequencyPenalty: 0.2,
            },
            history: history.map(h => ({
                role: h.role,
                parts: [{ text: h.content }]
            }))
        });

        const result = await chat.sendMessage({
             message: userMessage 
        });

        return result.text;
    } catch (error) {
        console.error("Error in chat:", error);
        throw error;
    }
}