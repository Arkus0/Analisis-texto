class WordCountService {
  /// Counts words in a text string.
  /// A word is a sequence of non-whitespace characters separated by whitespace.
  /// Returns 0 for empty or whitespace-only strings.
  static int count(String text) {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return 0;
    return trimmed.split(RegExp(r'\s+')).length;
  }

  /// Counts total words across multiple text strings.
  static int countAll(List<String> texts) {
    return texts.fold(0, (sum, text) => sum + count(text));
  }
}
