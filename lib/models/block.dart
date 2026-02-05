class Block {
  final String id;
  final String assignmentId;
  final String key;
  final String title;
  final String content;
  final String notes;
  final bool isDone;
  final int sortOrder;

  const Block({
    required this.id,
    required this.assignmentId,
    required this.key,
    required this.title,
    this.content = '',
    this.notes = '',
    this.isDone = false,
    required this.sortOrder,
  });

  Block copyWith({
    String? id,
    String? assignmentId,
    String? key,
    String? title,
    String? content,
    String? notes,
    bool? isDone,
    int? sortOrder,
  }) {
    return Block(
      id: id ?? this.id,
      assignmentId: assignmentId ?? this.assignmentId,
      key: key ?? this.key,
      title: title ?? this.title,
      content: content ?? this.content,
      notes: notes ?? this.notes,
      isDone: isDone ?? this.isDone,
      sortOrder: sortOrder ?? this.sortOrder,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'assignmentId': assignmentId,
      'key': key,
      'title': title,
      'content': content,
      'notes': notes,
      'isDone': isDone ? 1 : 0,
      'sortOrder': sortOrder,
    };
  }

  factory Block.fromMap(Map<String, dynamic> map) {
    return Block(
      id: map['id'] as String,
      assignmentId: map['assignmentId'] as String,
      key: map['key'] as String,
      title: map['title'] as String,
      content: map['content'] as String? ?? '',
      notes: map['notes'] as String? ?? '',
      isDone: (map['isDone'] as int? ?? 0) == 1,
      sortOrder: map['sortOrder'] as int? ?? 0,
    );
  }
}
