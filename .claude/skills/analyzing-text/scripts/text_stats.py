"""Word counts, reading time and readability of a text. The script of the analyzing-text skill (Lesson 3, Pattern A).

WHAT
    Two commands; SOURCE is a file, or - to read the text from a pipe (stdin):
        stats SOURCE                              words, sentences, paragraphs, characters, reading
                                                  time, average sentence length, Flesch reading ease,
                                                  and the 3 longest sentences
        top-words SOURCE [--n 10] [--min-len 3]   the most frequent words, without common words such
                                                  as "the" and "and"

WHY
    Language models can't count words reliably: they see tokens, not words. Python counts exactly.

HOW CLAUDE USES IT
    For a file, the analyzing-text SKILL.md tells Claude to run
        python "${CLAUDE_SKILL_DIR}/scripts/text_stats.py" stats data/article.txt
    For text pasted into the chat, Claude pipes it in, so no file has to be written:
        echo "Paste the text here." | python "${CLAUDE_SKILL_DIR}/scripts/text_stats.py" stats -
    Claude reads only the JSON that the script prints, never this file.

HOW TO RUN IT YOURSELF  (in cmd, from the project folder)
    python .claude/skills/analyzing-text/scripts/text_stats.py stats data/article.txt
        {"words": 180, "sentences": 15, "paragraphs": 5, "characters": 957, "reading_time_min": 0.8,
         "avg_sentence_words": 12.0, "flesch_reading_ease": 83.7, "longest_sentences": [...]}
    python .claude/skills/analyzing-text/scripts/text_stats.py top-words data/article.txt --n 3
        {"top_words": [["model", 5], ["skill", 4], ["script", 3]], "distinct_words": 113}
    echo The quick brown fox. It runs. | python .claude/skills/analyzing-text/scripts/text_stats.py stats -

HOW IT WORKS
    Words are runs of letters; sentences end at . ! or ?; paragraphs are separated by empty lines.
    Reading time assumes 238 words per minute. The Flesch score (0 to 100, higher is easier) uses
    words per sentence and syllables per word; syllables are estimated from groups of vowels.

NEEDS
    Only the standard library. It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k AnalyzingText
       Expected (4 tests; the time differs):
           ....
           ----------------------------------------------------------------------
           Ran 4 tests in 0.174s

           OK
       What they check: word, sentence and paragraph counts, a heading without a full stop as its own
       sentence, frequent words without common words, and text from a pipe. Add -v to see the name of
       each test.
    2. By hand: free.
           echo One two three. Four five. | python .claude/skills/analyzing-text/scripts/text_stats.py stats -
               {"words": 5, "sentences": 2, "paragraphs": 1, "characters": 27, "reading_time_min": 0.0,
                "avg_sentence_words": 2.5, "flesch_reading_ease": 119.7, "longest_sentences": ["One two three.", "Four five."]}
           python .claude/skills/analyzing-text/scripts/text_stats.py stats data/missing.txt
               {"error": "File not found: data/missing.txt", "hint": "Pass a path relative to the current directory, or - for stdin."}
    3. With Claude: uses a little Pro allowance.
           claude -p "How many words and sentences are in data/article.txt?" --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
               Expected: 180 words and 15 sentences (the real run also named 5 paragraphs).

IF SOMETHING GOES WRONG
    - A Flesch score above 100 or a reading time of 0.0 for very short text is normal: the formula and
      the rounding (to 0.1 minute) were made for longer texts.
    - The script waits and prints nothing: you gave - but piped no text in. Press Ctrl+Z, then Enter.

FILES IT READS AND WRITES
    Reads the file you name, or the text piped in (stdin). Writes nothing.

SEE ALSO
    analyzing-text/SKILL.md; class AnalyzingText; Lesson 3, Step A4 (the pipe).
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Average adult silent reading speed for non-fiction (Brysbaert, 2019).
WORDS_PER_MINUTE = 238
# Number of long sentences returned, enough to point at the worst offenders.
LONGEST_SENTENCES_SHOWN = 3

STOP_WORDS = set(
    """a about after all also an and any are as at be because been but by can could did do does
    for from had has have he her his how i if in into is it its just like may more most my no not
    of on one only or other our out over she so some such than that the their them then there these
    they this to up us was we were what when which who will with would you your""".split()
)

WORD_RE = re.compile(r"[A-Za-zÀ-ɏ']+")
SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def read_input(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return path.read_text(encoding="utf-8", errors="replace")


def count_syllables(word: str) -> int:
    """Rough English syllable count: vowel groups, minus a silent final 'e'."""
    word = word.lower().strip("'")
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ee")) and count > 1:
        count -= 1
    return max(count, 1)


def split_sentences(text: str) -> list[str]:
    # Split per paragraph first, so a heading without a full stop stays its own sentence.
    sentences = []
    for block in re.split(r"\n\s*\n", text):
        flat = " ".join(block.split())
        sentences += [s for s in SENTENCE_END_RE.split(flat) if WORD_RE.search(s)]
    return sentences


def stats(text: str) -> dict:
    words = WORD_RE.findall(text)
    sentences = split_sentences(text)
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not words:
        return {"words": 0, "sentences": 0, "paragraphs": 0, "characters": len(text)}

    syllables = sum(count_syllables(w) for w in words)
    words_per_sentence = len(words) / max(len(sentences), 1)
    flesch = 206.835 - 1.015 * words_per_sentence - 84.6 * (syllables / len(words))
    longest = sorted(sentences, key=lambda s: len(WORD_RE.findall(s)), reverse=True)

    return {
        "words": len(words),
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        "characters": len(text),
        "reading_time_min": round(len(words) / WORDS_PER_MINUTE, 1),
        "avg_sentence_words": round(words_per_sentence, 1),
        "flesch_reading_ease": round(flesch, 1),
        "longest_sentences": longest[:LONGEST_SENTENCES_SHOWN],
    }


def top_words(text: str, n: int = 10, min_len: int = 3) -> dict:
    words = [w.lower().strip("'") for w in WORD_RE.findall(text)]
    counts = Counter(w for w in words if len(w) >= min_len and w not in STOP_WORDS)
    return {"top_words": counts.most_common(n), "distinct_words": len(set(words))}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Measure a text.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_stats = sub.add_parser("stats", help="counts, reading time, readability")
    p_stats.add_argument("source", help="file path, or - for stdin")
    p_top = sub.add_parser("top-words", help="most frequent non-stop words")
    p_top.add_argument("source", help="file path, or - for stdin")
    p_top.add_argument("--n", type=int, default=10)
    p_top.add_argument("--min-len", type=int, default=3)

    args = parser.parse_args(argv)
    try:
        text = read_input(args.source)
    except FileNotFoundError as err:
        print(json.dumps({"error": str(err), "hint": "Pass a path relative to the current directory, or - for stdin."}))
        return 1

    result = stats(text) if args.command == "stats" else top_words(text, args.n, args.min_len)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
