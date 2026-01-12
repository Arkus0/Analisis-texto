/**
 * Extracts text from a File object (PDF or TXT).
 * For PDFs, it uses Smart Sampling.
 * For TXT, it reads the content directly.
 */
export const extractTextFromFile = async (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    
    // Handle Text Files
    if (file.type === 'text/plain') {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = () => reject(new Error("Error leyendo archivo de texto."));
      reader.readAsText(file);
      return;
    }

    // Handle PDF Files
    if (file.type === 'application/pdf') {
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          const typedarray = new Uint8Array(event.target?.result as ArrayBuffer);
          
          // @ts-ignore - pdfjsLib is loaded globally via script tag
          const loadingTask = window.pdfjsLib.getDocument({ data: typedarray });
          const pdf = await loadingTask.promise;
          const totalPages = pdf.numPages;
          
          let fullText = '';
          const pagesToExtract = new Set<number>();
          
          // SMART SAMPLING STRATEGY
          if (totalPages <= 15) {
            for (let i = 1; i <= totalPages; i++) pagesToExtract.add(i);
          } else {
            // 1. The Hook (First 5 pages)
            for (let i = 1; i <= 5; i++) pagesToExtract.add(i);
            // 2. The Core (Middle 5 pages)
            const mid = Math.floor(totalPages / 2);
            for (let i = mid - 2; i <= mid + 2; i++) pagesToExtract.add(i);
            // 3. The Climax/Resolution (Last 5 pages)
            for (let i = totalPages - 4; i <= totalPages; i++) {
              if (i > 0) pagesToExtract.add(i);
            }
          }

          const sortedPages = Array.from(pagesToExtract).sort((a, b) => a - b);
          console.log(`Smart Sampling: Extracting ${sortedPages.length} pages from ${totalPages} total.`);

          for (const pageNum of sortedPages) {
            const page = await pdf.getPage(pageNum);
            const textContent = await page.getTextContent();
            const pageText = textContent.items
              // @ts-ignore
              .map((item) => item.str)
              .join(' ');
            
            if (pagesToExtract.has(pageNum - 1) === false && pageNum > 1) {
               fullText += '\n\n[...GAP IN MANUSCRIPT...]\n\n';
            }
            fullText += pageText + '\n\n';
          }

          resolve(fullText.trim());
        } catch (error) {
          console.error("Error parsing PDF:", error);
          reject(new Error("No se pudo leer el PDF. Asegúrate de que no esté corrupto o protegido con contraseña."));
        }
      };
      reader.onerror = () => reject(new Error("Error al leer el archivo."));
      reader.readAsArrayBuffer(file);
      return;
    }

    reject(new Error("Formato no soportado. Usa PDF o TXT."));
  });
};