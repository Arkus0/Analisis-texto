enum AssignmentType {
  comentarioCritico,
  ensayo;

  String get displayName {
    switch (this) {
      case AssignmentType.comentarioCritico:
        return 'Comentario crítico';
      case AssignmentType.ensayo:
        return 'Ensayo';
    }
  }

  String get dbValue {
    switch (this) {
      case AssignmentType.comentarioCritico:
        return 'comentario_critico';
      case AssignmentType.ensayo:
        return 'ensayo';
    }
  }

  static AssignmentType fromDb(String value) {
    switch (value) {
      case 'comentario_critico':
        return AssignmentType.comentarioCritico;
      case 'ensayo':
        return AssignmentType.ensayo;
      default:
        return AssignmentType.comentarioCritico;
    }
  }
}

enum AssignmentStatus {
  draft,
  inProgress,
  review,
  done;

  String get displayName {
    switch (this) {
      case AssignmentStatus.draft:
        return 'Borrador';
      case AssignmentStatus.inProgress:
        return 'En progreso';
      case AssignmentStatus.review:
        return 'Revisión';
      case AssignmentStatus.done:
        return 'Entregado';
    }
  }

  String get dbValue {
    switch (this) {
      case AssignmentStatus.draft:
        return 'draft';
      case AssignmentStatus.inProgress:
        return 'in_progress';
      case AssignmentStatus.review:
        return 'review';
      case AssignmentStatus.done:
        return 'done';
    }
  }

  static AssignmentStatus fromDb(String value) {
    switch (value) {
      case 'draft':
        return AssignmentStatus.draft;
      case 'in_progress':
        return AssignmentStatus.inProgress;
      case 'review':
        return AssignmentStatus.review;
      case 'done':
        return AssignmentStatus.done;
      default:
        return AssignmentStatus.draft;
    }
  }
}

class Assignment {
  final String id;
  final String courseId;
  final String title;
  final AssignmentType type;
  final DateTime? dueDate;
  final AssignmentStatus status;
  final int targetMinWords;
  final int targetMaxWords;

  const Assignment({
    required this.id,
    required this.courseId,
    required this.title,
    required this.type,
    this.dueDate,
    this.status = AssignmentStatus.draft,
    this.targetMinWords = 1500,
    this.targetMaxWords = 3000,
  });

  Assignment copyWith({
    String? id,
    String? courseId,
    String? title,
    AssignmentType? type,
    DateTime? dueDate,
    bool clearDueDate = false,
    AssignmentStatus? status,
    int? targetMinWords,
    int? targetMaxWords,
  }) {
    return Assignment(
      id: id ?? this.id,
      courseId: courseId ?? this.courseId,
      title: title ?? this.title,
      type: type ?? this.type,
      dueDate: clearDueDate ? null : (dueDate ?? this.dueDate),
      status: status ?? this.status,
      targetMinWords: targetMinWords ?? this.targetMinWords,
      targetMaxWords: targetMaxWords ?? this.targetMaxWords,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'courseId': courseId,
      'title': title,
      'type': type.dbValue,
      'dueDate': dueDate?.millisecondsSinceEpoch,
      'status': status.dbValue,
      'targetMinWords': targetMinWords,
      'targetMaxWords': targetMaxWords,
    };
  }

  factory Assignment.fromMap(Map<String, dynamic> map) {
    return Assignment(
      id: map['id'] as String,
      courseId: map['courseId'] as String,
      title: map['title'] as String,
      type: AssignmentType.fromDb(map['type'] as String),
      dueDate: map['dueDate'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['dueDate'] as int)
          : null,
      status: AssignmentStatus.fromDb(map['status'] as String),
      targetMinWords: map['targetMinWords'] as int? ?? 1500,
      targetMaxWords: map['targetMaxWords'] as int? ?? 3000,
    );
  }
}
