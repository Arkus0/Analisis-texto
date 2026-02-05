import 'package:flutter/material.dart';
import 'package:pec_killer/models/assignment.dart';

class StatusBadge extends StatelessWidget {
  final AssignmentStatus status;

  const StatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (color, bgColor) = _colors(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        status.displayName,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  (Color, Color) _colors(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    switch (status) {
      case AssignmentStatus.draft:
        return (scheme.outline, scheme.surfaceContainerHighest);
      case AssignmentStatus.inProgress:
        return (scheme.primary, scheme.primaryContainer);
      case AssignmentStatus.review:
        return (scheme.tertiary, scheme.tertiaryContainer);
      case AssignmentStatus.done:
        return (scheme.onPrimaryContainer, scheme.primaryContainer);
    }
  }
}
