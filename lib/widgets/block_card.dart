import 'dart:async';

import 'package:flutter/material.dart';
import 'package:pec_killer/models/block.dart';
import 'package:pec_killer/services/word_count_service.dart';

class BlockCard extends StatefulWidget {
  final Block block;
  final bool isExpanded;
  final VoidCallback onToggleExpand;
  final Future<void> Function(Block) onUpdate;

  const BlockCard({
    super.key,
    required this.block,
    required this.isExpanded,
    required this.onToggleExpand,
    required this.onUpdate,
  });

  @override
  State<BlockCard> createState() => _BlockCardState();
}

class _BlockCardState extends State<BlockCard> {
  late TextEditingController _contentCtrl;
  late TextEditingController _notesCtrl;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _contentCtrl = TextEditingController(text: widget.block.content);
    _notesCtrl = TextEditingController(text: widget.block.notes);
  }

  @override
  void didUpdateWidget(BlockCard old) {
    super.didUpdateWidget(old);
    if (old.block.id != widget.block.id) {
      _contentCtrl.text = widget.block.content;
      _notesCtrl.text = widget.block.notes;
    }
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _contentCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  void _onContentChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      widget.onUpdate(widget.block.copyWith(content: value));
    });
    // Update word count immediately in UI
    setState(() {});
  }

  void _onNotesChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      widget.onUpdate(widget.block.copyWith(notes: value));
    });
  }

  void _toggleDone() {
    widget.onUpdate(widget.block.copyWith(isDone: !widget.block.isDone));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final words = WordCountService.count(_contentCtrl.text);
    final isDone = widget.block.isDone;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header (always visible)
          InkWell(
            onTap: widget.onToggleExpand,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: _toggleDone,
                    child: Icon(
                      isDone
                          ? Icons.check_circle
                          : Icons.radio_button_unchecked,
                      color: isDone
                          ? theme.colorScheme.primary
                          : theme.colorScheme.outline,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.block.title,
                          style: theme.textTheme.titleSmall?.copyWith(
                            decoration: isDone
                                ? TextDecoration.lineThrough
                                : null,
                          ),
                        ),
                        if (!widget.isExpanded &&
                            widget.block.content.isNotEmpty)
                          Text(
                            widget.block.content.length > 80
                                ? '${widget.block.content.substring(0, 80)}...'
                                : widget.block.content,
                            style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.outline),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '$words',
                      style: theme.textTheme.labelSmall,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    widget.isExpanded
                        ? Icons.expand_less
                        : Icons.expand_more,
                    color: theme.colorScheme.outline,
                  ),
                ],
              ),
            ),
          ),

          // Expanded content
          if (widget.isExpanded) ...[
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Content field
                  TextField(
                    controller: _contentCtrl,
                    onChanged: _onContentChanged,
                    maxLines: null,
                    minLines: 4,
                    decoration: const InputDecoration(
                      hintText: 'Escribe aquí...',
                      border: OutlineInputBorder(),
                    ),
                    style: const TextStyle(fontSize: 14, height: 1.6),
                  ),
                  const SizedBox(height: 12),

                  // Notes field (collapsed by default)
                  ExpansionTile(
                    title: Text('Notas',
                        style: theme.textTheme.labelMedium),
                    tilePadding: EdgeInsets.zero,
                    childrenPadding: EdgeInsets.zero,
                    initiallyExpanded: widget.block.notes.isNotEmpty,
                    children: [
                      TextField(
                        controller: _notesCtrl,
                        onChanged: _onNotesChanged,
                        maxLines: null,
                        minLines: 2,
                        decoration: InputDecoration(
                          hintText: 'Notas personales...',
                          border: const OutlineInputBorder(),
                          fillColor:
                              theme.colorScheme.surfaceContainerHighest,
                        ),
                        style:
                            TextStyle(fontSize: 12, color: theme.colorScheme.outline),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
