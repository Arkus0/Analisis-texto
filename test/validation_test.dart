import 'package:flutter_test/flutter_test.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/services/validation_service.dart';

void main() {
  Assignment makeAssignment({
    DateTime? dueDate,
    AssignmentType type = AssignmentType.comentarioCritico,
    int targetMinWords = 100,
    int targetMaxWords = 500,
  }) {
    return Assignment(
      id: 'a1',
      courseId: 'c1',
      title: 'PEC1',
      type: type,
      dueDate: dueDate,
      targetMinWords: targetMinWords,
      targetMaxWords: targetMaxWords,
    );
  }

  List<Block> makeBlocks({
    String tesisContent = '',
    String otherContent = '',
    bool includeReferences = true,
  }) {
    final blocks = <Block>[
      Block(
          id: 'b1',
          assignmentId: 'a1',
          key: 'tesis',
          title: 'Tesis',
          content: tesisContent,
          sortOrder: 0),
      Block(
          id: 'b2',
          assignmentId: 'a1',
          key: 'resumen',
          title: 'Resumen',
          content: otherContent,
          sortOrder: 1),
      Block(
          id: 'b3',
          assignmentId: 'a1',
          key: 'conceptos_clave',
          title: 'Conceptos clave',
          content: otherContent,
          sortOrder: 2),
      Block(
          id: 'b4',
          assignmentId: 'a1',
          key: 'argumentos_autor',
          title: 'Argumentos del autor',
          content: otherContent,
          sortOrder: 3),
      Block(
          id: 'b5',
          assignmentId: 'a1',
          key: 'critica',
          title: 'Crítica',
          content: otherContent,
          sortOrder: 4),
      Block(
          id: 'b6',
          assignmentId: 'a1',
          key: 'implicaciones',
          title: 'Implicaciones',
          content: otherContent,
          sortOrder: 5),
      Block(
          id: 'b7',
          assignmentId: 'a1',
          key: 'conclusion',
          title: 'Conclusión',
          content: otherContent,
          sortOrder: 6),
    ];
    if (includeReferences) {
      blocks.add(Block(
          id: 'b8',
          assignmentId: 'a1',
          key: 'referencias',
          title: 'Referencias',
          content: '',
          sortOrder: 7));
    }
    return blocks;
  }

  group('ValidationService.validate', () {
    test('fails when due date is missing', () {
      final a = makeAssignment(dueDate: null);
      final blocks = makeBlocks(
        tesisContent: 'test thesis',
        otherContent: 'some content here that has enough words',
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      expect(result.results[0].passed, false);
      expect(result.allPassed, false);
    });

    test('passes when due date is set', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)));
      final blocks = makeBlocks(
        tesisContent: 'test thesis',
        otherContent: 'some content here',
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      expect(result.results[0].passed, true);
    });

    test('fails when thesis block is empty', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)));
      final blocks = makeBlocks(
        tesisContent: '',
        otherContent: 'some content',
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      expect(result.results[1].passed, false);
    });

    test('passes when thesis block has content', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)));
      final blocks = makeBlocks(
        tesisContent: 'La tesis principal es...',
        otherContent: 'content',
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      expect(result.results[1].passed, true);
    });

    test('fails when some required blocks are empty', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)));
      final blocks = makeBlocks(
        tesisContent: 'thesis',
        otherContent: '', // all other blocks empty
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      expect(result.results[2].passed, false);
    });

    test('references block being empty does not count as a failure', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)),
          targetMinWords: 1,
          targetMaxWords: 1000);
      // all blocks have content except references
      final blocks = makeBlocks(
        tesisContent: 'thesis here (Author, 2023) (Smith, 2022) (García, 2021)',
        otherContent: 'some content here',
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      // The "blocks completed" rule should pass
      expect(result.results[2].passed, true);
    });

    test('fails with insufficient citations', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)));
      final blocks = makeBlocks(
        tesisContent: 'thesis without citations',
        otherContent: 'content without citations',
      );
      final result = ValidationService.validate(
          assignment: a, blocks: blocks, minimumCitations: 3);
      expect(result.results[3].passed, false);
    });

    test('passes with enough citations', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)),
          targetMinWords: 1,
          targetMaxWords: 1000);
      final blocks = makeBlocks(
        tesisContent:
            'Según (García, 2023) y (Smith, 2022) además de (López, 2021)',
        otherContent: 'more content here',
      );
      final result = ValidationService.validate(
          assignment: a, blocks: blocks, minimumCitations: 3);
      expect(result.results[3].passed, true);
    });

    test('word count fails when below minimum', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)),
          targetMinWords: 1000,
          targetMaxWords: 2000);
      final blocks = makeBlocks(
        tesisContent: 'short',
        otherContent: 'also short',
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      expect(result.results[4].passed, false);
    });

    test('word count fails when above maximum', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)),
          targetMinWords: 1,
          targetMaxWords: 5);
      final blocks = makeBlocks(
        tesisContent: 'this has quite a few words in it now',
        otherContent: 'and this also has many words',
      );
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      expect(result.results[4].passed, false);
    });

    test('all rules pass for valid submission', () {
      final a = makeAssignment(
          dueDate: DateTime.now().add(const Duration(days: 7)),
          targetMinWords: 10,
          targetMaxWords: 500);
      final blocks = makeBlocks(
        tesisContent:
            'La tesis principal argumenta que (García, 2023) '
            'según (Smith, 2022) y (López, 2021) es correcto',
        otherContent: 'Contenido del bloque con suficientes palabras',
      );
      final result = ValidationService.validate(
          assignment: a, blocks: blocks, minimumCitations: 3);
      expect(result.allPassed, true);
      expect(result.results.every((r) => r.passed), true);
    });
  });

  group('ValidationService.countCitations', () {
    test('counts 0 when no citations', () {
      final blocks = [
        Block(
            id: '1',
            assignmentId: 'a1',
            key: 'k',
            title: 't',
            content: 'no citations here',
            sortOrder: 0),
      ];
      expect(ValidationService.countCitations(blocks), 0);
    });

    test('counts standard citation format', () {
      final blocks = [
        Block(
            id: '1',
            assignmentId: 'a1',
            key: 'k',
            title: 't',
            content: 'Según (García, 2023) y (Smith, 2022)',
            sortOrder: 0),
      ];
      expect(ValidationService.countCitations(blocks), 2);
    });

    test('counts citations with accented characters', () {
      final blocks = [
        Block(
            id: '1',
            assignmentId: 'a1',
            key: 'k',
            title: 't',
            content: 'Referencia (Martínez, 2021) y (Pérez, 2020)',
            sortOrder: 0),
      ];
      expect(ValidationService.countCitations(blocks), 2);
    });

    test('counts citations across multiple blocks', () {
      final blocks = [
        Block(
            id: '1',
            assignmentId: 'a1',
            key: 'k1',
            title: 't1',
            content: '(Author, 2023)',
            sortOrder: 0),
        Block(
            id: '2',
            assignmentId: 'a1',
            key: 'k2',
            title: 't2',
            content: '(Other, 2022) y (More, 2021)',
            sortOrder: 1),
      ];
      expect(ValidationService.countCitations(blocks), 3);
    });
  });

  group('ValidationService for ensayo type', () {
    test('checks pregunta_postura as thesis block', () {
      final a = Assignment(
        id: 'a1',
        courseId: 'c1',
        title: 'Ensayo1',
        type: AssignmentType.ensayo,
        dueDate: DateTime.now().add(const Duration(days: 7)),
        targetMinWords: 1,
        targetMaxWords: 1000,
      );
      final blocks = [
        Block(
            id: 'b1',
            assignmentId: 'a1',
            key: 'pregunta_postura',
            title: 'Pregunta + postura',
            content: '',
            sortOrder: 0),
        Block(
            id: 'b2',
            assignmentId: 'a1',
            key: 'roadmap',
            title: 'Roadmap',
            content: 'content',
            sortOrder: 1),
        Block(
            id: 'b3',
            assignmentId: 'a1',
            key: 'referencias',
            title: 'Referencias',
            content: '',
            sortOrder: 7),
      ];
      final result =
          ValidationService.validate(assignment: a, blocks: blocks);
      // Thesis rule should fail (pregunta_postura is empty)
      expect(result.results[1].passed, false);
    });
  });
}
