import 'package:flutter_test/flutter_test.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/models/course.dart';
import 'package:pec_killer/models/settings.dart';
import 'package:pec_killer/services/export_service.dart';

void main() {
  group('ExportService.generateFilename', () {
    test('generates filename with default course name', () {
      final course = Course(id: 'c1', name: 'Psicología Social');
      final assignment = Assignment(
        id: 'a1',
        courseId: 'c1',
        title: 'PEC2',
        type: AssignmentType.comentarioCritico,
      );
      const settings = UserSettings(lastNameFirst: 'GarcíaJuan');

      final filename = ExportService.generateFilename(
        course: course,
        assignment: assignment,
        settings: settings,
      );
      expect(filename, 'Psicología_Social_PEC2_GarcíaJuan.pdf');
    });

    test('uses fileNamePattern when set', () {
      final course =
          Course(id: 'c1', name: 'Psicología Social', fileNamePattern: 'PSocial');
      final assignment = Assignment(
        id: 'a1',
        courseId: 'c1',
        title: 'PEC2',
        type: AssignmentType.comentarioCritico,
      );
      const settings = UserSettings(lastNameFirst: 'GarcíaJuan');

      final filename = ExportService.generateFilename(
        course: course,
        assignment: assignment,
        settings: settings,
      );
      expect(filename, 'PSocial_PEC2_GarcíaJuan.pdf');
    });

    test('uses Student when lastNameFirst is empty', () {
      final course = Course(id: 'c1', name: 'Math');
      final assignment = Assignment(
        id: 'a1',
        courseId: 'c1',
        title: 'PEC1',
        type: AssignmentType.ensayo,
      );
      const settings = UserSettings();

      final filename = ExportService.generateFilename(
        course: course,
        assignment: assignment,
        settings: settings,
      );
      expect(filename, 'Math_PEC1_Student.pdf');
    });
  });

  group('ExportService.generateChecklistReport', () {
    test('generates plain text report', () {
      final assignment = Assignment(
        id: 'a1',
        courseId: 'c1',
        title: 'PEC1',
        type: AssignmentType.comentarioCritico,
        dueDate: DateTime(2025, 6, 15),
        targetMinWords: 100,
        targetMaxWords: 500,
      );
      final blocks = [
        Block(
            id: 'b1',
            assignmentId: 'a1',
            key: 'tesis',
            title: 'Tesis',
            content: 'Mi tesis (García, 2023) (Smith, 2022) (López, 2021)',
            sortOrder: 0),
        Block(
            id: 'b2',
            assignmentId: 'a1',
            key: 'resumen',
            title: 'Resumen',
            content: 'El resumen del texto',
            sortOrder: 1),
        Block(
            id: 'b3',
            assignmentId: 'a1',
            key: 'conceptos_clave',
            title: 'Conceptos clave',
            content: 'Concepto uno, concepto dos',
            sortOrder: 2),
        Block(
            id: 'b4',
            assignmentId: 'a1',
            key: 'argumentos_autor',
            title: 'Argumentos del autor',
            content: 'El autor argumenta que',
            sortOrder: 3),
        Block(
            id: 'b5',
            assignmentId: 'a1',
            key: 'critica',
            title: 'Crítica',
            content: 'La crítica principal es',
            sortOrder: 4),
        Block(
            id: 'b6',
            assignmentId: 'a1',
            key: 'implicaciones',
            title: 'Implicaciones',
            content: 'Las implicaciones son',
            sortOrder: 5),
        Block(
            id: 'b7',
            assignmentId: 'a1',
            key: 'conclusion',
            title: 'Conclusión',
            content: 'En conclusión podemos afirmar',
            sortOrder: 6),
        Block(
            id: 'b8',
            assignmentId: 'a1',
            key: 'referencias',
            title: 'Referencias',
            content: '',
            sortOrder: 7),
      ];

      final report = ExportService.generateChecklistReport(
        assignment: assignment,
        blocks: blocks,
      );

      expect(report, contains('PEC Killer'));
      expect(report, contains('PEC1'));
      expect(report, contains('Comentario crítico'));
      expect(report, contains('[OK]'));
      expect(report, contains('Palabras totales:'));
    });

    test('shows failures in report', () {
      final assignment = Assignment(
        id: 'a1',
        courseId: 'c1',
        title: 'PEC1',
        type: AssignmentType.comentarioCritico,
        targetMinWords: 1000,
        targetMaxWords: 2000,
      );
      final blocks = [
        Block(
            id: 'b1',
            assignmentId: 'a1',
            key: 'tesis',
            title: 'Tesis',
            content: '',
            sortOrder: 0),
        Block(
            id: 'b8',
            assignmentId: 'a1',
            key: 'referencias',
            title: 'Referencias',
            content: '',
            sortOrder: 7),
      ];

      final report = ExportService.generateChecklistReport(
        assignment: assignment,
        blocks: blocks,
      );

      expect(report, contains('[!!]'));
      expect(report, contains('PENDIENTE'));
    });
  });
}
