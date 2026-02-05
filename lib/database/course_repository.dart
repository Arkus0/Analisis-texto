import 'package:pec_killer/database/database_helper.dart';
import 'package:pec_killer/models/course.dart';

class CourseRepository {
  final DatabaseHelper _db;

  CourseRepository(this._db);

  Future<List<Course>> getAll() async {
    final db = await _db.database;
    final maps = await db.query('courses', orderBy: 'name ASC');
    return maps.map((m) => Course.fromMap(m)).toList();
  }

  Future<Course?> getById(String id) async {
    final db = await _db.database;
    final maps = await db.query('courses', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return Course.fromMap(maps.first);
  }

  Future<void> insert(Course course) async {
    final db = await _db.database;
    await db.insert('courses', course.toMap());
  }

  Future<void> update(Course course) async {
    final db = await _db.database;
    await db.update('courses', course.toMap(),
        where: 'id = ?', whereArgs: [course.id]);
  }

  Future<void> delete(String id) async {
    final db = await _db.database;
    await db.delete('courses', where: 'id = ?', whereArgs: [id]);
  }
}
