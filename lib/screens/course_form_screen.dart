import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import 'package:pec_killer/database/course_repository.dart';
import 'package:pec_killer/models/course.dart';

class CourseFormScreen extends StatefulWidget {
  final Course? course;

  const CourseFormScreen({super.key, this.course});

  @override
  State<CourseFormScreen> createState() => _CourseFormScreenState();
}

class _CourseFormScreenState extends State<CourseFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameCtrl;
  late final TextEditingController _termCtrl;
  late final TextEditingController _patternCtrl;
  bool _saving = false;

  bool get _isEditing => widget.course != null;

  @override
  void initState() {
    super.initState();
    _nameCtrl = TextEditingController(text: widget.course?.name ?? '');
    _termCtrl = TextEditingController(text: widget.course?.term ?? '');
    _patternCtrl =
        TextEditingController(text: widget.course?.fileNamePattern ?? '');
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _termCtrl.dispose();
    _patternCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final repo = context.read<CourseRepository>();
    final course = Course(
      id: widget.course?.id ?? const Uuid().v4(),
      name: _nameCtrl.text.trim(),
      term: _termCtrl.text.trim().isEmpty ? null : _termCtrl.text.trim(),
      fileNamePattern:
          _patternCtrl.text.trim().isEmpty ? null : _patternCtrl.text.trim(),
    );

    if (_isEditing) {
      await repo.update(course);
    } else {
      await repo.insert(course);
    }

    if (mounted) Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Editar asignatura' : 'Nueva asignatura'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _nameCtrl,
              decoration: const InputDecoration(
                labelText: 'Nombre de la asignatura',
                hintText: 'Ej: Psicología Social',
              ),
              textCapitalization: TextCapitalization.sentences,
              autofocus: !_isEditing,
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Obligatorio' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _termCtrl,
              decoration: const InputDecoration(
                labelText: 'Semestre (opcional)',
                hintText: 'Ej: 2024-1',
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _patternCtrl,
              decoration: const InputDecoration(
                labelText: 'Patrón de nombre de archivo (opcional)',
                hintText: 'Ej: PSocial',
                helperText:
                    'Se usa en el nombre del PDF exportado. Por defecto se usa el nombre.',
              ),
            ),
            const SizedBox(height: 32),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(_isEditing ? 'Guardar' : 'Crear asignatura'),
            ),
          ],
        ),
      ),
    );
  }
}
