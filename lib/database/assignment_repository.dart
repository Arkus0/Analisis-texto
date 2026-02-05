import 'package:pec_killer/database/database_helper.dart';
import 'package:pec_killer/models/assignment.dart';

class AssignmentRepository {
  final DatabaseHelper _db;

  AssignmentRepository(this._db);

  Future<List<Assignment>> getByCourse(String courseId) async {
    final db = await _db.database;
    final maps = await db.query('assignments',
        where: 'courseId = ?',
        whereArgs: [courseId],
        orderBy: 'dueDate ASC');
    return maps.map((m) => Assignment.fromMap(m)).toList();
  }

  Future<List<Assignment>> getUpcoming({int limit = 10}) async {
    final db = await _db.database;
    final now = DateTime.now().millisecondsSinceEpoch;
    final maps = await db.query('assignments',
        where: "dueDate IS NOT NULL AND dueDate >= ? AND status != 'done'",
        whereArgs: [now],
        orderBy: 'dueDate ASC',
        limit: limit);
    return maps.map((m) => Assignment.fromMap(m)).toList();
  }

  Future<List<Assignment>> getAll() async {
    final db = await _db.database;
    final maps = await db.query('assignments', orderBy: 'dueDate ASC');
    return maps.map((m) => Assignment.fromMap(m)).toList();
  }

  Future<Assignment?> getById(String id) async {
    final db = await _db.database;
    final maps =
        await db.query('assignments', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return Assignment.fromMap(maps.first);
  }

  Future<void> insert(Assignment assignment) async {
    final db = await _db.database;
    await db.insert('assignments', assignment.toMap());
  }

  Future<void> update(Assignment assignment) async {
    final db = await _db.database;
    await db.update('assignments', assignment.toMap(),
        where: 'id = ?', whereArgs: [assignment.id]);
  }

  Future<void> delete(String id) async {
    final db = await _db.database;
    await db.delete('assignments', where: 'id = ?', whereArgs: [id]);
  }
}
