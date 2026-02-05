import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import 'package:pec_killer/database/assignment_repository.dart';
import 'package:pec_killer/database/course_repository.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/course.dart';
import 'package:pec_killer/screens/course_detail_screen.dart';
import 'package:pec_killer/screens/course_form_screen.dart';
import 'package:pec_killer/screens/assignment_detail_screen.dart';
import 'package:pec_killer/screens/settings_screen.dart';
import 'package:pec_killer/widgets/status_badge.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Course> _courses = [];
  List<Assignment> _upcoming = [];
  Map<String, String> _courseNames = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final courseRepo = context.read<CourseRepository>();
    final assignmentRepo = context.read<AssignmentRepository>();
    final courses = await courseRepo.getAll();
    final upcoming = await assignmentRepo.getUpcoming(limit: 5);
    final nameMap = {for (final c in courses) c.id: c.name};
    if (mounted) {
      setState(() {
        _courses = courses;
        _upcoming = upcoming;
        _courseNames = nameMap;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('PEC Killer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () async {
              await Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const SettingsScreen()));
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Upcoming section
                  if (_upcoming.isNotEmpty) ...[
                    Text('Próximas entregas',
                        style: theme.textTheme.titleMedium),
                    const SizedBox(height: 8),
                    ..._upcoming.map(_buildUpcomingCard),
                    const SizedBox(height: 24),
                  ],

                  // Courses section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Asignaturas',
                          style: theme.textTheme.titleMedium),
                      if (_courses.isNotEmpty)
                        Text('${_courses.length}',
                            style: theme.textTheme.bodySmall),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (_courses.isEmpty)
                    _buildEmptyState()
                  else
                    ..._courses.map(_buildCourseCard),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await Navigator.push<bool>(context,
              MaterialPageRoute(builder: (_) => const CourseFormScreen()));
          if (created == true) _load();
        },
        icon: const Icon(Icons.add),
        label: const Text('Asignatura'),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          children: [
            Icon(Icons.school_outlined,
                size: 48,
                color: Theme.of(context).colorScheme.outline),
            const SizedBox(height: 12),
            Text('Añade tu primera asignatura',
                style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 4),
            Text('Pulsa + para empezar',
                style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }

  Widget _buildCourseCard(Course course) {
    return Card(
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: CircleAvatar(
          backgroundColor:
              Theme.of(context).colorScheme.primaryContainer,
          child: Text(
            course.name.isNotEmpty ? course.name[0].toUpperCase() : '?',
            style: TextStyle(
                color: Theme.of(context)
                    .colorScheme
                    .onPrimaryContainer),
          ),
        ),
        title: Text(course.name),
        subtitle: course.term != null ? Text(course.term!) : null,
        trailing: const Icon(Icons.chevron_right),
        onTap: () async {
          await Navigator.push(
              context,
              MaterialPageRoute(
                  builder: (_) =>
                      CourseDetailScreen(courseId: course.id)));
          _load();
        },
      ),
    );
  }

  Widget _buildUpcomingCard(Assignment a) {
    final daysLeft = a.dueDate?.difference(DateTime.now()).inDays;
    final dateStr = a.dueDate != null
        ? DateFormat('dd MMM', 'es').format(a.dueDate!)
        : '';
    final courseName = _courseNames[a.courseId] ?? '';

    return Card(
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(dateStr,
                style: Theme.of(context).textTheme.labelSmall),
            if (daysLeft != null)
              Text(
                daysLeft == 0
                    ? 'Hoy'
                    : daysLeft == 1
                        ? 'Mañana'
                        : '$daysLeft días',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: daysLeft <= 2
                      ? Theme.of(context).colorScheme.error
                      : Theme.of(context).colorScheme.primary,
                ),
              ),
          ],
        ),
        title: Text(a.title),
        subtitle: Text(courseName),
        trailing: StatusBadge(status: a.status),
        onTap: () async {
          await Navigator.push(
              context,
              MaterialPageRoute(
                  builder: (_) => AssignmentDetailScreen(
                      assignmentId: a.id)));
          _load();
        },
      ),
    );
  }
}
