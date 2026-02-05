import 'package:pec_killer/database/database_helper.dart';
import 'package:pec_killer/models/block.dart';

class BlockRepository {
  final DatabaseHelper _db;

  BlockRepository(this._db);

  Future<List<Block>> getByAssignment(String assignmentId) async {
    final db = await _db.database;
    final maps = await db.query('blocks',
        where: 'assignmentId = ?',
        whereArgs: [assignmentId],
        orderBy: 'sortOrder ASC');
    return maps.map((m) => Block.fromMap(m)).toList();
  }

  Future<void> insert(Block block) async {
    final db = await _db.database;
    await db.insert('blocks', block.toMap());
  }

  Future<void> update(Block block) async {
    final db = await _db.database;
    await db.update('blocks', block.toMap(),
        where: 'id = ?', whereArgs: [block.id]);
  }

  Future<void> delete(String id) async {
    final db = await _db.database;
    await db.delete('blocks', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> deleteByAssignment(String assignmentId) async {
    final db = await _db.database;
    await db.delete('blocks',
        where: 'assignmentId = ?', whereArgs: [assignmentId]);
  }

  Future<void> insertAll(List<Block> blocks) async {
    final db = await _db.database;
    final batch = db.batch();
    for (final block in blocks) {
      batch.insert('blocks', block.toMap());
    }
    await batch.commit(noResult: true);
  }
}
