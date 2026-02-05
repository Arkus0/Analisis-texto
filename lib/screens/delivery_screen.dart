import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:pec_killer/database/assignment_repository.dart';
import 'package:pec_killer/database/block_repository.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/services/validation_service.dart';
import 'package:pec_killer/services/word_count_service.dart';

class DeliveryScreen extends StatefulWidget {
  final String assignmentId;

  const DeliveryScreen({super.key, required this.assignmentId});

  @override
  State<DeliveryScreen> createState() => _DeliveryScreenState();
}

class _DeliveryScreenState extends State<DeliveryScreen> {
  Assignment? _assignment;
  List<Block> _blocks = [];
  DeliveryValidation? _validation;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final assignmentRepo = context.read<AssignmentRepository>();
    final blockRepo = context.read<BlockRepository>();
    final assignment = await assignmentRepo.getById(widget.assignmentId);
    List<Block> blocks = [];
    DeliveryValidation? validation;
    if (assignment != null) {
      blocks = await blockRepo.getByAssignment(assignment.id);
      validation = ValidationService.validate(
          assignment: assignment, blocks: blocks);
    }
    if (mounted) {
      setState(() {
        _assignment = assignment;
        _blocks = blocks;
        _validation = validation;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Modo entrega')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_assignment == null || _validation == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Modo entrega')),
        body: const Center(child: Text('Trabajo no encontrado')),
      );
    }

    final theme = Theme.of(context);
    final v = _validation!;
    final totalWords =
        WordCountService.countAll(_blocks.map((b) => b.content).toList());

    return Scaffold(
      appBar: AppBar(title: const Text('Modo entrega')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Overall status
          _OverallStatusCard(passed: v.allPassed),
          const SizedBox(height: 16),

          // Word count summary
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(Icons.text_fields,
                      color: theme.colorScheme.primary),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('$totalWords palabras',
                          style: theme.textTheme.titleMedium),
                      Text(
                          'Objetivo: ${_assignment!.targetMinWords}–${_assignment!.targetMaxWords}',
                          style: theme.textTheme.bodySmall),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Validation rules
          Text('Checklist de entrega',
              style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          ...v.results.map((r) => _ValidationRuleCard(result: r)),

          const SizedBox(height: 24),

          // Block progress
          Text('Progreso por bloque',
              style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          ..._blocks.map(_buildBlockProgress),
        ],
      ),
    );
  }

  Widget _buildBlockProgress(Block block) {
    final words = WordCountService.count(block.content);
    final hasContent = block.content.trim().isNotEmpty;
    final theme = Theme.of(context);

    return Card(
      child: ListTile(
        leading: Icon(
          hasContent
              ? (block.isDone
                  ? Icons.check_circle
                  : Icons.radio_button_checked)
              : Icons.radio_button_unchecked,
          color: hasContent
              ? (block.isDone
                  ? theme.colorScheme.primary
                  : theme.colorScheme.tertiary)
              : theme.colorScheme.outline,
        ),
        title: Text(block.title),
        trailing: Text('$words',
            style: theme.textTheme.bodySmall),
      ),
    );
  }
}

class _OverallStatusCard extends StatelessWidget {
  final bool passed;

  const _OverallStatusCard({required this.passed});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color =
        passed ? theme.colorScheme.primary : theme.colorScheme.error;

    return Card(
      color: color.withValues(alpha: 0.08),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Icon(
              passed ? Icons.check_circle : Icons.warning_rounded,
              size: 48,
              color: color,
            ),
            const SizedBox(height: 12),
            Text(
              passed ? 'LISTO PARA ENTREGAR' : 'PENDIENTE',
              style: theme.textTheme.titleLarge?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              passed
                  ? 'Todos los criterios cumplidos'
                  : 'Revisa los puntos pendientes',
              style: theme.textTheme.bodyMedium?.copyWith(color: color),
            ),
          ],
        ),
      ),
    );
  }
}

class _ValidationRuleCard extends StatelessWidget {
  final ValidationResult result;

  const _ValidationRuleCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color =
        result.passed ? theme.colorScheme.primary : theme.colorScheme.error;

    return Card(
      child: ListTile(
        leading: Icon(
          result.passed ? Icons.check_circle : Icons.cancel,
          color: color,
        ),
        title: Text(result.rule),
        subtitle: Text(
          result.message,
          style: TextStyle(
            color: result.passed ? null : color,
          ),
        ),
      ),
    );
  }
}
