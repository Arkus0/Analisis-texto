import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:pec_killer/database/database_helper.dart';
import 'package:pec_killer/database/course_repository.dart';
import 'package:pec_killer/database/assignment_repository.dart';
import 'package:pec_killer/database/block_repository.dart';
import 'package:pec_killer/database/settings_repository.dart';

class AppProviders extends StatelessWidget {
  final Widget child;

  const AppProviders({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final db = DatabaseHelper();
    return MultiProvider(
      providers: [
        Provider<DatabaseHelper>.value(value: db),
        Provider<CourseRepository>(create: (_) => CourseRepository(db)),
        Provider<AssignmentRepository>(
            create: (_) => AssignmentRepository(db)),
        Provider<BlockRepository>(create: (_) => BlockRepository(db)),
        Provider<SettingsRepository>(create: (_) => SettingsRepository(db)),
      ],
      child: child,
    );
  }
}
