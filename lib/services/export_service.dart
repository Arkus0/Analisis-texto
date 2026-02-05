import 'dart:io';
import 'dart:typed_data';

import 'package:archive/archive.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/models/course.dart';
import 'package:pec_killer/models/settings.dart';
import 'package:pec_killer/services/validation_service.dart';
import 'package:pec_killer/services/word_count_service.dart';

class ExportService {
  /// Generate a filename for the PDF.
  /// Pattern: COURSE_TITLE_LastNameFirst.pdf
  static String generateFilename({
    required Course course,
    required Assignment assignment,
    required UserSettings settings,
  }) {
    final courseName =
        course.fileNamePattern ?? course.name.replaceAll(' ', '_');
    final title = assignment.title.replaceAll(' ', '_');
    final userName = settings.lastNameFirst.isNotEmpty
        ? settings.lastNameFirst.replaceAll(' ', '')
        : 'Student';
    return '${courseName}_${title}_$userName.pdf';
  }

  /// Build the PDF document from assignment blocks.
  static Future<Uint8List> generatePdf({
    required Course course,
    required Assignment assignment,
    required List<Block> blocks,
    required UserSettings settings,
  }) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(60),
        build: (context) {
          final widgets = <pw.Widget>[];

          // Title
          widgets.add(pw.Header(
            level: 0,
            child: pw.Text(
              assignment.title,
              style: pw.TextStyle(
                fontSize: 24,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
          ));

          // Subtitle: course + type
          widgets.add(pw.Paragraph(
            text:
                '${course.name} — ${assignment.type.displayName}',
            style: const pw.TextStyle(fontSize: 12, color: PdfColors.grey700),
          ));

          if (settings.userDisplayName.isNotEmpty) {
            widgets.add(pw.Paragraph(
              text: settings.userDisplayName,
              style:
                  const pw.TextStyle(fontSize: 11, color: PdfColors.grey600),
            ));
          }

          widgets.add(pw.SizedBox(height: 20));

          // Blocks
          for (final block in blocks) {
            if (block.content.trim().isEmpty && block.key != 'referencias') {
              continue;
            }

            widgets.add(pw.Header(
              level: 1,
              child: pw.Text(
                block.title,
                style: pw.TextStyle(
                  fontSize: 16,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
            ));

            if (block.content.trim().isNotEmpty) {
              widgets.add(pw.Paragraph(
                text: block.content,
                style: const pw.TextStyle(fontSize: 11, lineSpacing: 4),
              ));
            }

            widgets.add(pw.SizedBox(height: 8));
          }

          // Word count footer
          final totalWords = WordCountService.countAll(
              blocks.map((b) => b.content).toList());
          widgets.add(pw.Divider());
          widgets.add(pw.Paragraph(
            text: 'Palabras: $totalWords',
            style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey500),
          ));

          return widgets;
        },
      ),
    );

    return pdf.save();
  }

  /// Generate a plain text checklist report.
  static String generateChecklistReport({
    required Assignment assignment,
    required List<Block> blocks,
  }) {
    final validation =
        ValidationService.validate(assignment: assignment, blocks: blocks);
    final buffer = StringBuffer();

    buffer.writeln('=== PEC Killer — Checklist de entrega ===');
    buffer.writeln('Trabajo: ${assignment.title}');
    buffer.writeln('Tipo: ${assignment.type.displayName}');
    buffer.writeln('');

    for (final result in validation.results) {
      final icon = result.passed ? '[OK]' : '[!!]';
      buffer.writeln('$icon ${result.rule}: ${result.message}');
    }

    buffer.writeln('');
    buffer.writeln(validation.allPassed
        ? 'RESULTADO: LISTO PARA ENTREGAR'
        : 'RESULTADO: PENDIENTE — revisa los puntos marcados con [!!]');

    final totalWords =
        WordCountService.countAll(blocks.map((b) => b.content).toList());
    buffer.writeln('');
    buffer.writeln('Palabras totales: $totalWords');
    buffer.writeln(
        'Rango objetivo: ${assignment.targetMinWords}–${assignment.targetMaxWords}');

    return buffer.toString();
  }

  /// Save PDF to app documents and return the file path.
  static Future<String> savePdf({
    required Uint8List pdfBytes,
    required String filename,
  }) async {
    final dir = await getApplicationDocumentsDirectory();
    final exportDir = Directory('${dir.path}/exports');
    if (!await exportDir.exists()) {
      await exportDir.create(recursive: true);
    }
    final file = File('${exportDir.path}/$filename');
    await file.writeAsBytes(pdfBytes);
    return file.path;
  }

  /// Create a ZIP submission package containing the PDF and checklist.
  static Future<String> createSubmissionPackage({
    required Course course,
    required Assignment assignment,
    required List<Block> blocks,
    required UserSettings settings,
  }) async {
    final pdfBytes = await generatePdf(
      course: course,
      assignment: assignment,
      blocks: blocks,
      settings: settings,
    );
    final filename = generateFilename(
      course: course,
      assignment: assignment,
      settings: settings,
    );
    final checklistText = generateChecklistReport(
      assignment: assignment,
      blocks: blocks,
    );

    final archive = Archive();
    archive.addFile(ArchiveFile(filename, pdfBytes.length, pdfBytes));
    final checklistBytes = Uint8List.fromList(checklistText.codeUnits);
    archive.addFile(ArchiveFile(
      filename.replaceAll('.pdf', '_checklist.txt'),
      checklistBytes.length,
      checklistBytes,
    ));

    final zipData = ZipEncoder().encode(archive);

    final dir = await getApplicationDocumentsDirectory();
    final exportDir = Directory('${dir.path}/exports');
    if (!await exportDir.exists()) {
      await exportDir.create(recursive: true);
    }
    final zipPath =
        '${exportDir.path}/${filename.replaceAll('.pdf', '.zip')}';
    final zipFile = File(zipPath);
    await zipFile.writeAsBytes(zipData);
    return zipPath;
  }
}
