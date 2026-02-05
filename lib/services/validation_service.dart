import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/services/template_service.dart';
import 'package:pec_killer/services/word_count_service.dart';

class ValidationResult {
  final String rule;
  final bool passed;
  final String message;

  const ValidationResult({
    required this.rule,
    required this.passed,
    required this.message,
  });
}

class DeliveryValidation {
  final List<ValidationResult> results;
  final bool allPassed;

  const DeliveryValidation({required this.results, required this.allPassed});
}

class ValidationService {
  /// Citation pattern: (Author, Year) or (Author, 2023) etc.
  /// Matches patterns like (Smith, 2023), (García & López, 2021),
  /// (Author et al., 2020)
  static final RegExp citationPattern = RegExp(
    r'\([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s&.,]+\d{4}\)',
  );

  /// Count citation markers in all blocks' content.
  static int countCitations(List<Block> blocks) {
    int count = 0;
    for (final block in blocks) {
      count += citationPattern.allMatches(block.content).length;
    }
    return count;
  }

  /// Run all delivery validation rules.
  static DeliveryValidation validate({
    required Assignment assignment,
    required List<Block> blocks,
    int minimumCitations = 3,
  }) {
    final results = <ValidationResult>[];

    // Rule 1: Due date is set
    results.add(ValidationResult(
      rule: 'Fecha de entrega',
      passed: assignment.dueDate != null,
      message: assignment.dueDate != null
          ? 'Fecha de entrega establecida'
          : 'Falta establecer la fecha de entrega',
    ));

    // Rule 2: Thesis/pregunta block is not empty
    final thesisKey = TemplateService.getThesisKey(assignment.type);
    final thesisBlock = blocks.where((b) => b.key == thesisKey).firstOrNull;
    final thesisNotEmpty =
        thesisBlock != null && thesisBlock.content.trim().isNotEmpty;
    results.add(ValidationResult(
      rule: 'Tesis / Pregunta',
      passed: thesisNotEmpty,
      message: thesisNotEmpty
          ? 'Bloque de tesis completado'
          : 'El bloque de tesis/pregunta está vacío',
    ));

    // Rule 3: All required blocks have content (exclude referencias)
    final requiredBlocks =
        blocks.where((b) => b.key != 'referencias').toList();
    final emptyBlocks =
        requiredBlocks.where((b) => b.content.trim().isEmpty).toList();
    final allBlocksFilled = emptyBlocks.isEmpty;
    results.add(ValidationResult(
      rule: 'Bloques completados',
      passed: allBlocksFilled,
      message: allBlocksFilled
          ? 'Todos los bloques tienen contenido'
          : 'Bloques vacíos: ${emptyBlocks.map((b) => b.title).join(", ")}',
    ));

    // Rule 4: Minimum citations
    final citationCount = countCitations(blocks);
    final hasCitations = citationCount >= minimumCitations;
    results.add(ValidationResult(
      rule: 'Citas',
      passed: hasCitations,
      message: hasCitations
          ? '$citationCount citas encontradas'
          : '$citationCount/$minimumCitations citas mínimas (formato: Autor, Año)',
    ));

    // Rule 5: Word count within range
    final totalWords = WordCountService.countAll(
        blocks.map((b) => b.content).toList());
    final inRange = totalWords >= assignment.targetMinWords &&
        totalWords <= assignment.targetMaxWords;
    results.add(ValidationResult(
      rule: 'Recuento de palabras',
      passed: inRange,
      message: inRange
          ? '$totalWords palabras (rango: ${assignment.targetMinWords}–${assignment.targetMaxWords})'
          : '$totalWords palabras — objetivo: ${assignment.targetMinWords}–${assignment.targetMaxWords}',
    ));

    final allPassed = results.every((r) => r.passed);
    return DeliveryValidation(results: results, allPassed: allPassed);
  }
}
