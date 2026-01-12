/**
 * Extracts text from a PDF file object.
 * Uses the pdfjsLib loaded via CDN in index.html to ensure worker compatibility.
 */
export const extractTextFromPdf = async (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = async (event) => {
      try {
        const typedarray = new Uint8Array(event.target?.result as ArrayBuffer);
        
        // @ts-ignore - pdfjsLib is loaded globally via script tag
        const loadingTask = window.pdfjsLib.getDocument({ data: typedarray });
        const pdf = await loadingTask.promise;
        
        let fullText = '';
        // Limit to first 20 pages to avoid crashing browser or token limits, 
        // usually enough to get the style.
        const maxPages = Math.min(pdf.numPages, 20);

        for (let i = 1; i <= maxPages; i++) {
          const page = await pdf.getPage(i);
          const textContent = await page.getTextContent();
          const pageText = textContent.items
            // @ts-ignore
            .map((item) => item.str)
            .join(' ');
          fullText += pageText + '\n\n';
        }

        resolve(fullText.trim());
      } catch (error) {
        console.error("Error parsing PDF:", error);
        reject(new Error("No se pudo leer el PDF. Asegúrate de que no esté corrupto o protegido con contraseña."));
      }
    };

    reader.onerror = () => {
      reject(new Error("Error al leer el archivo."));
    };

    reader.readAsArrayBuffer(file);
  });
};