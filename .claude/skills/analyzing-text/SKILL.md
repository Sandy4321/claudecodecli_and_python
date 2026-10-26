---
name: analyzing-text
description: Measures prose in .txt or .md documents - word, sentence and paragraph counts, reading time, Flesch reading-ease score, average sentence length, and most frequent words. Use when the user asks how long, how readable, or how wordy a text, article, essay, or README is. Not for tables or .csv data (use analyzing-csv).
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Analyzing text

## Statistics for a file

```bash
python "${CLAUDE_SKILL_DIR}/scripts/text_stats.py" stats data/article.txt
```

## Most frequent words

```bash
python "${CLAUDE_SKILL_DIR}/scripts/text_stats.py" top-words data/article.txt --n 10
```

Common English stop words ("the", "and", ...) are excluded. Use `--min-len 5` to skip short words.

## Text the user pasted into chat

Pipe it in with `-` instead of a file name:

```bash
echo "Paste the text here." | python "${CLAUDE_SKILL_DIR}/scripts/text_stats.py" stats -
```

## Reading the results

- `reading_time_min` assumes 238 words per minute (average adult silent reading speed).
- `flesch_reading_ease`: 90-100 very easy, 60-70 plain English, 30-50 difficult, below 30 very hard.
  The syllable count is a heuristic, so treat the score as approximate (about +/- 5).
- When the user wants the text improved, quote the longest sentences from `longest_sentences`.
