import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:pec_killer/database/assignment_repository.dart';
import 'package:pec_killer/database/block_repository.dart';
import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/services/word_count_service.dart';
import 'package:pec_killer/widgets/block_card.dart';

class EditorScreen extends StatefulWidget {
  final String assignmentId;

  const EditorScreen({super.key, required this.assignmentId});

  @override
  State<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends State<EditorScreen> {
  Assignment? _assignment;
  List<Block> _blocks = [];
  bool _loading = true;
  int? _expandedIndex;

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
    if (assignment != null) {
      blocks = await blockRepo.getByAssignment(assignment.id);
    }
    if (mounted) {
      setState(() {
        _assignment = assignment;
        _blocks = blocks;
        _loading = false;
      });
    }
  }

  Future<void> _updateBlock(Block block) async {
    await context.read<BlockRepository>().update(block);
    // Update local state without full reload for responsiveness
    setState(() {
      final idx = _blocks.indexWhere((b) => b.id == block.id);
      if (idx != -1) {
        _blocks[idx] = block;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final totalWords =
        WordCountService.countAll(_blocks.map((b) => b.content).toList());
    final minW = _assignment?.targetMinWords ?? 0;
    final maxW = _assignment?.targetMaxWords ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: Text(_assignment?.title ?? 'Editor'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Center(
              child: _WordCountChip(
                  total: totalWords, min: minW, max: maxW),
            ),
          ),
        ],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
        itemCount: _blocks.length,
        itemBuilder: (_, i) {
          final block = _blocks[i];
          return BlockCard(
            block: block,
            isExpanded: _expandedIndex == i,
            onToggleExpand: () {
              setState(() {
                _expandedIndex = _expandedIndex == i ? null : i;
              });
            },
            onUpdate: _updateBlock,
          );
        },
      ),
    );
  }
}

class _WordCountChip extends StatelessWidget {
  final int total;
  final int min;
  final int max;

  const _WordCountChip({
    required this.total,
    required this.min,
    required this.max,
  });

  @override
  Widget build(BuildContext context) {
    final inRange = total >= min && total <= max;
    final theme = Theme.of(context);
    final color = total == 0
        ? theme.colorScheme.outline
        : inRange
            ? theme.colorScheme.primary
            : theme.colorScheme.error;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        '$total palabras',
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
