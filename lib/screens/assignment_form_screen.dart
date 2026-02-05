import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import 'package:pec_killer/database/assignment_repository.dart';
import 'package:pec_killer/database/block_repository.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/services/template_service.dart';

class AssignmentFormScreen extends StatefulWidget {
  final String courseId;
  final Assignment? assignment;

  const AssignmentFormScreen({
    super.key,
    required this.courseId,
    this.assignment,
  });

  @override
  State<AssignmentFormScreen> createState() => _AssignmentFormScreenState();
}

class _AssignmentFormScreenState extends State<AssignmentFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _titleCtrl;
  late final TextEditingController _minWordsCtrl;
  late final TextEditingController _maxWordsCtrl;
  AssignmentType _type = AssignmentType.comentarioCritico;
  DateTime? _dueDate;
  bool _saving = false;

  bool get _isEditing => widget.assignment != null;

  @override
  void initState() {
    super.initState();
    _titleCtrl =
        TextEditingController(text: widget.assignment?.title ?? '');
    _minWordsCtrl = TextEditingController(
        text: '${widget.assignment?.targetMinWords ?? 1500}');
    _maxWordsCtrl = TextEditingController(
        text: '${widget.assignment?.targetMaxWords ?? 3000}');
    if (widget.assignment != null) {
      _type = widget.assignment!.type;
      _dueDate = widget.assignment!.dueDate;
    }
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _minWordsCtrl.dispose();
    _maxWordsCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _dueDate ?? DateTime.now().add(const Duration(days: 14)),
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 365 * 2)),
    );
    if (picked != null) {
      setState(() => _dueDate = picked);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final assignmentRepo = context.read<AssignmentRepository>();
    final blockRepo = context.read<BlockRepository>();

    final id = widget.assignment?.id ?? const Uuid().v4();
    final assignment = Assignment(
      id: id,
      courseId: widget.courseId,
      title: _titleCtrl.text.trim(),
      type: _type,
      dueDate: _dueDate,
      status: widget.assignment?.status ?? AssignmentStatus.draft,
      targetMinWords: int.tryParse(_minWordsCtrl.text) ?? 1500,
      targetMaxWords: int.tryParse(_maxWordsCtrl.text) ?? 3000,
    );

    if (_isEditing) {
      await assignmentRepo.update(assignment);
    } else {
      await assignmentRepo.insert(assignment);
      // Create template blocks for new assignment
      final blocks = TemplateService.createBlocks(id, _type);
      await blockRepo.insertAll(blocks);
    }

    if (mounted) Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Editar trabajo' : 'Nuevo trabajo'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _titleCtrl,
              decoration: const InputDecoration(
                labelText: 'Título',
                hintText: 'Ej: PEC2',
              ),
              textCapitalization: TextCapitalization.sentences,
              autofocus: !_isEditing,
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Obligatorio' : null,
            ),
            const SizedBox(height: 16),

            // Type selector
            if (!_isEditing) ...[
              Text('Tipo de trabajo',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              SegmentedButton<AssignmentType>(
                segments: AssignmentType.values
                    .map((t) => ButtonSegment(
                        value: t, label: Text(t.displayName)))
                    .toList(),
                selected: {_type},
                onSelectionChanged: (v) =>
                    setState(() => _type = v.first),
              ),
              const SizedBox(height: 16),
            ],

            // Due date
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.calendar_today),
              title: Text(_dueDate != null
                  ? DateFormat('dd MMMM yyyy').format(_dueDate!)
                  : 'Fecha de entrega'),
              subtitle: _dueDate == null
                  ? const Text('Pulsa para establecer')
                  : null,
              trailing: _dueDate != null
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () => setState(() => _dueDate = null),
                    )
                  : null,
              onTap: _pickDate,
            ),
            const SizedBox(height: 16),

            // Word count range
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _minWordsCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Mín. palabras',
                    ),
                    keyboardType: TextInputType.number,
                    validator: (v) {
                      final n = int.tryParse(v ?? '');
                      if (n == null || n < 0) return 'Número válido';
                      return null;
                    },
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: TextFormField(
                    controller: _maxWordsCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Máx. palabras',
                    ),
                    keyboardType: TextInputType.number,
                    validator: (v) {
                      final n = int.tryParse(v ?? '');
                      if (n == null || n < 0) return 'Número válido';
                      return null;
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),

            FilledButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(_isEditing ? 'Guardar' : 'Crear trabajo'),
            ),
          ],
        ),
      ),
    );
  }
}
