import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import 'package:pec_killer/database/assignment_repository.dart';
import 'package:pec_killer/database/course_repository.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/course.dart';
import 'package:pec_killer/screens/assignment_detail_screen.dart';
import 'package:pec_killer/screens/assignment_form_screen.dart';
import 'package:pec_killer/screens/course_form_screen.dart';
import 'package:pec_killer/widgets/status_badge.dart';

class CourseDetailScreen extends StatefulWidget {
  final String courseId;

  const CourseDetailScreen({super.key, required this.courseId});

  @override
  State<CourseDetailScreen> createState() => _CourseDetailScreenState();
}

class _CourseDetailScreenState extends State<CourseDetailScreen> {
  Course? _course;
  List<Assignment> _assignments = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final courseRepo = context.read<CourseRepository>();
    final assignmentRepo = context.read<AssignmentRepository>();
    final course = await courseRepo.getById(widget.courseId);
    final assignments = await assignmentRepo.getByCourse(widget.courseId);
    if (mounted) {
      setState(() {
        _course = course;
        _assignments = assignments;
        _loading = false;
      });
    }
  }

  Future<void> _deleteCourse() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar asignatura'),
        content: const Text(
            '¿Eliminar esta asignatura y todos sus trabajos? Esta acción no se puede deshacer.'),
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
      await context.read<CourseRepository>().delete(widget.courseId);
      if (mounted) Navigator.pop(context);
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

    if (_course == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: Text('Asignatura no encontrada')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_course!.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            onPressed: () async {
              final updated = await Navigator.push<bool>(
                  context,
                  MaterialPageRoute(
                      builder: (_) =>
                          CourseFormScreen(course: _course)));
              if (updated == true) _load();
            },
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline),
            onPressed: _deleteCourse,
          ),
        ],
      ),
      body: _assignments.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.assignment_outlined,
                      size: 48,
                      color: Theme.of(context).colorScheme.outline),
                  const SizedBox(height: 12),
                  Text('Sin trabajos todavía',
                      style: Theme.of(context).textTheme.bodyLarge),
                  const SizedBox(height: 4),
                  Text('Pulsa + para crear tu primera PEC',
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            )
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _assignments.length,
                itemBuilder: (_, i) =>
                    _buildAssignmentCard(_assignments[i]),
              ),
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await Navigator.push<bool>(
              context,
              MaterialPageRoute(
                  builder: (_) => AssignmentFormScreen(
                      courseId: widget.courseId)));
          if (created == true) _load();
        },
        icon: const Icon(Icons.add),
        label: const Text('PEC'),
      ),
    );
  }

  Widget _buildAssignmentCard(Assignment a) {
    final dateStr = a.dueDate != null
        ? DateFormat('dd MMM yyyy').format(a.dueDate!)
        : 'Sin fecha';

    return Card(
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        title: Text(a.title),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text('${a.type.displayName} · $dateStr'),
          ],
        ),
        trailing: StatusBadge(status: a.status),
        onTap: () async {
          await Navigator.push(
              context,
              MaterialPageRoute(
                  builder: (_) =>
                      AssignmentDetailScreen(assignmentId: a.id)));
          _load();
        },
      ),
    );
  }
}
