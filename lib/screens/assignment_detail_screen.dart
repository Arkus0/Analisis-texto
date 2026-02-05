import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';

import 'package:pec_killer/database/assignment_repository.dart';
import 'package:pec_killer/database/block_repository.dart';
import 'package:pec_killer/database/course_repository.dart';
import 'package:pec_killer/database/settings_repository.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/models/course.dart';
import 'package:pec_killer/models/settings.dart';
import 'package:pec_killer/screens/assignment_form_screen.dart';
import 'package:pec_killer/screens/delivery_screen.dart';
import 'package:pec_killer/screens/editor_screen.dart';
import 'package:pec_killer/services/export_service.dart';
import 'package:pec_killer/services/word_count_service.dart';
import 'package:pec_killer/widgets/status_badge.dart';

class AssignmentDetailScreen extends StatefulWidget {
  final String assignmentId;

  const AssignmentDetailScreen({super.key, required this.assignmentId});

  @override
  State<AssignmentDetailScreen> createState() =>
      _AssignmentDetailScreenState();
}

class _AssignmentDetailScreenState extends State<AssignmentDetailScreen> {
  Assignment? _assignment;
  Course? _course;
  List<Block> _blocks = [];
  UserSettings _settings = const UserSettings();
  bool _loading = true;
  bool _exporting = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final assignmentRepo = context.read<AssignmentRepository>();
    final blockRepo = context.read<BlockRepository>();
    final courseRepo = context.read<CourseRepository>();
    final settingsRepo = context.read<SettingsRepository>();

    final assignment = await assignmentRepo.getById(widget.assignmentId);
    List<Block> blocks = [];
    Course? course;
    if (assignment != null) {
      blocks = await blockRepo.getByAssignment(assignment.id);
      course = await courseRepo.getById(assignment.courseId);
    }
    final settings = await settingsRepo.get();

    if (mounted) {
      setState(() {
        _assignment = assignment;
        _blocks = blocks;
        _course = course;
        _settings = settings;
        _loading = false;
      });
    }
  }

  Future<void> _updateStatus(AssignmentStatus status) async {
    if (_assignment == null) return;
    final updated = _assignment!.copyWith(status: status);
    await context.read<AssignmentRepository>().update(updated);
    _load();
  }

  Future<void> _deleteAssignment() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar trabajo'),
        content: const Text(
            '¿Eliminar este trabajo y todos sus bloques? Esta acción no se puede deshacer.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              style: FilledButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.error),
              child: const Text('Eliminar')),
        ],
      ),
    );
    if (confirm == true && mounted) {
      final blockRepo = context.read<BlockRepository>();
      await blockRepo.deleteByAssignment(widget.assignmentId);
      await context.read<AssignmentRepository>().delete(widget.assignmentId);
      if (mounted) Navigator.pop(context);
    }
  }

  Future<void> _exportPdf() async {
    if (_assignment == null || _course == null) return;
    setState(() => _exporting = true);

    try {
      final pdfBytes = await ExportService.generatePdf(
        course: _course!,
        assignment: _assignment!,
        blocks: _blocks,
        settings: _settings,
      );
      final filename = ExportService.generateFilename(
        course: _course!,
        assignment: _assignment!,
        settings: _settings,
      );
      final path =
          await ExportService.savePdf(pdfBytes: pdfBytes, filename: filename);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('PDF guardado: $filename')));
        await Share.shareXFiles([XFile(path)]);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error al exportar: $e')));
      }
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  Future<void> _exportPackage() async {
    if (_assignment == null || _course == null) return;
    setState(() => _exporting = true);

    try {
      final zipPath = await ExportService.createSubmissionPackage(
        course: _course!,
        assignment: _assignment!,
        blocks: _blocks,
        settings: _settings,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Paquete de entrega creado')));
        await Share.shareXFiles([XFile(zipPath)]);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_assignment == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: Text('Trabajo no encontrado')),
      );
    }

    final a = _assignment!;
    final totalWords =
        WordCountService.countAll(_blocks.map((b) => b.content).toList());
    final completedBlocks = _blocks.where((b) => b.isDone).length;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(a.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            onPressed: () async {
              final updated = await Navigator.push<bool>(
                  context,
                  MaterialPageRoute(
                      builder: (_) => AssignmentFormScreen(
                          courseId: a.courseId, assignment: a)));
              if (updated == true) _load();
            },
          ),
          PopupMenuButton<String>(
            onSelected: (v) {
              switch (v) {
                case 'delete':
                  _deleteAssignment();
              }
            },
            itemBuilder: (_) => [
              const PopupMenuItem(
                  value: 'delete', child: Text('Eliminar trabajo')),
            ],
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Status + info card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      StatusBadge(status: a.status),
                      const Spacer(),
                      Text(a.type.displayName,
                          style: theme.textTheme.bodySmall),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (a.dueDate != null)
                    Row(
                      children: [
                        const Icon(Icons.calendar_today, size: 16),
                        const SizedBox(width: 8),
                        Text(
                            DateFormat('dd MMMM yyyy').format(a.dueDate!)),
                      ],
                    ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.text_fields, size: 16),
                      const SizedBox(width: 8),
                      Text(
                          '$totalWords palabras (${a.targetMinWords}–${a.targetMaxWords})'),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.check_circle_outline, size: 16),
                      const SizedBox(width: 8),
                      Text(
                          '$completedBlocks/${_blocks.length} bloques completados'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Status change
                  Wrap(
                    spacing: 8,
                    children: AssignmentStatus.values.map((s) {
                      final isActive = a.status == s;
                      return ChoiceChip(
                        label: Text(s.displayName),
                        selected: isActive,
                        onSelected: isActive
                            ? null
                            : (_) => _updateStatus(s),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Action buttons
          _ActionButton(
            icon: Icons.edit_note,
            label: 'Escribir',
            subtitle: 'Abrir el editor de bloques',
            onTap: () async {
              await Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => EditorScreen(
                          assignmentId: a.id)));
              _load();
            },
          ),
          const SizedBox(height: 8),
          _ActionButton(
            icon: Icons.checklist,
            label: 'Modo entrega',
            subtitle: 'Validar y revisar checklist',
            onTap: () async {
              await Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => DeliveryScreen(
                          assignmentId: a.id)));
              _load();
            },
          ),
          const SizedBox(height: 8),
          _ActionButton(
            icon: Icons.picture_as_pdf,
            label: 'Exportar PDF',
            subtitle: 'Generar y compartir PDF',
            loading: _exporting,
            onTap: _exportPdf,
          ),
          const SizedBox(height: 8),
          _ActionButton(
            icon: Icons.folder_zip_outlined,
            label: 'Paquete de entrega',
            subtitle: 'ZIP con PDF + checklist',
            loading: _exporting,
            onTap: _exportPackage,
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;
  final bool loading;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.onTap,
    this.loading = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: ListTile(
        leading: Icon(icon, color: theme.colorScheme.primary),
        title: Text(label),
        subtitle: Text(subtitle),
        trailing: loading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2))
            : const Icon(Icons.chevron_right),
        onTap: loading ? null : onTap,
      ),
    );
  }
}
