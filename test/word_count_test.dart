import 'package:flutter_test/flutter_test.dart';
import 'package:pec_killer/services/word_count_service.dart';

void main() {
  group('WordCountService.count', () {
    test('returns 0 for empty string', () {
      expect(WordCountService.count(''), 0);
    });

    test('returns 0 for whitespace-only string', () {
      expect(WordCountService.count('   '), 0);
      expect(WordCountService.count('\t\n  '), 0);
    });

    test('counts single word', () {
      expect(WordCountService.count('hello'), 1);
    });

    test('counts multiple words', () {
      expect(WordCountService.count('hello world'), 2);
    });

    test('handles multiple spaces between words', () {
      expect(WordCountService.count('hello   world'), 2);
    });

    test('handles tabs and newlines', () {
      expect(WordCountService.count('hello\tworld\nfoo'), 3);
    });

    test('handles leading and trailing whitespace', () {
      expect(WordCountService.count('  hello world  '), 2);
    });

    test('counts words in Spanish text with accents', () {
      expect(WordCountService.count('El análisis crítico es importante'), 5);
    });

    test('counts words in realistic academic paragraph', () {
      const text =
          'Según García (2023), la teoría del aprendizaje significativo '
          'establece que los estudiantes construyen conocimiento de manera '
          'activa cuando relacionan la nueva información con sus esquemas '
          'previos.';
      expect(WordCountService.count(text), 26);
    });
  });

  group('WordCountService.countAll', () {
    test('returns 0 for empty list', () {
      expect(WordCountService.countAll([]), 0);
    });

    test('sums words from multiple texts', () {
      expect(WordCountService.countAll(['hello world', 'foo bar baz']), 5);
    });

    test('handles mix of empty and non-empty strings', () {
      expect(WordCountService.countAll(['', 'hello', '', 'world']), 2);
    });
  });
}
