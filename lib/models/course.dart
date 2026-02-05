class Course {
  final String id;
  final String name;
  final String? term;
  final String? fileNamePattern;

  const Course({
    required this.id,
    required this.name,
    this.term,
    this.fileNamePattern,
  });

  Course copyWith({
    String? id,
    String? name,
    String? term,
    String? fileNamePattern,
  }) {
    return Course(
      id: id ?? this.id,
      name: name ?? this.name,
      term: term ?? this.term,
      fileNamePattern: fileNamePattern ?? this.fileNamePattern,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'term': term,
      'fileNamePattern': fileNamePattern,
    };
  }

  factory Course.fromMap(Map<String, dynamic> map) {
    return Course(
      id: map['id'] as String,
      name: map['name'] as String,
      term: map['term'] as String?,
      fileNamePattern: map['fileNamePattern'] as String?,
    );
  }
}
