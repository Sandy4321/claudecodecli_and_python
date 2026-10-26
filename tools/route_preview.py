"""Free offline preview: which skill descriptions share words with a request? (Lesson 2, Step 3; Lesson 5, Test 3)

WHAT
    Scores every skill's name and description against your request, and prints the top 3 with the
    words they share, plus a hint ("No clear match", or "Close call between the top two").

WHY
    To find descriptions that miss the words your users say, for free and in a second. But this is
    NOT how Claude chooses a skill: Claude reads every name and description with the full language
    model, and understands meaning, synonyms and context. For the real choice, run
    tools/routing_eval.py (Lesson 5, Test 4).

HOW IT WORKS
    BM25, the word-scoring formula of search engines: a shared word counts more when few
    descriptions contain it. skilllib.tokens() lowercases the words, drops common words such as
    "the", and cuts endings ("miles" -> "mile"). The "Not for ..." last sentence of each description
    is left out, because a word counter can't read "not". Skills that only you can start
    (disable-model-invocation: true) are not scored.

HOW TO RUN  (in cmd, from the project folder)
    python tools/route_preview.py "convert 26.2 miles to km"
    Without a request it prints this text.

OUTPUT
    Request: convert 26.2 miles to km
       7.06  converting-units       shared words: convert, km, mile
       0.00  tracking-todos         shared words: -
       0.00  plotting-charts        shared words: -
      (not scored, /command only: clear-todos)

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude, and costs nothing.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k route_preview
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 0.033s

           OK
       What it checks: that four typical requests rank the right skill first. Add -v to see the name of
       each test.
    2. By hand: free.
           python tools/route_preview.py "tell me a joke"
               Request: tell me a joke
                  0.00  tracking-todos         shared words: -
                  0.00  plotting-charts        shared words: -
                  0.00  converting-units       shared words: -
                 (not scored, /command only: clear-todos)
                 -> No clear match. Claude would most likely answer without a skill.

IF SOMETHING GOES WRONG
    - A skill never gets a score: its description lacks the words your users say (Lesson 2, Step 3).
    - A good score here doesn't prove Claude's choice; only tools/routing_eval.py does.

FILES IT READS AND WRITES
    Reads the SKILL.md files. Writes nothing.

SEE ALSO
    skilllib.py; tools/routing_eval.py; Lesson 2, Step 3; Lesson 5, Test 3.
"""

import math
import sys
from collections import Counter

from skilllib import DEFAULT_SKILLS_DIR, load_skills, positive_description, tokens

# Standard BM25 constants (Robertson & Zaragoza): k1 controls term-frequency
# saturation, b controls length normalization.
K1, B = 1.2, 0.75
# Below this score we say "no clear match" - roughly one rare shared word.
MIN_SCORE = 1.0


def rank(query: str, skills) -> list[tuple[float, str, list[str]]]:
    docs = {
        s.name: tokens(f"{s.name.replace('-', ' ')} {positive_description(s.description)}")
        for s in skills
        if s.model_invocable
    }
    avg_len = sum(len(d) for d in docs.values()) / max(len(docs), 1)
    df = Counter(word for d in docs.values() for word in set(d))
    q = tokens(query)
    results = []
    for name, doc in docs.items():
        tf = Counter(doc)
        score, hits = 0.0, []
        for word in set(q):
            if word not in tf:
                continue
            idf = math.log(1 + (len(docs) - df[word] + 0.5) / (df[word] + 0.5))
            score += idf * tf[word] * (K1 + 1) / (tf[word] + K1 * (1 - B + B * len(doc) / avg_len))
            hits.append(word)
        results.append((score, name, sorted(hits)))
    return sorted(results, reverse=True)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    query = " ".join(argv)
    skills = load_skills(DEFAULT_SKILLS_DIR)
    ranked = rank(query, skills)
    print(f"Request: {query}\n")
    for score, name, hits in ranked[:3]:
        print(f"  {score:5.2f}  {name:22} shared words: {', '.join(hits) or '-'}")
    manual = [s.name for s in skills if not s.model_invocable]
    if manual:
        print(f"\n  (not scored, /command only: {', '.join(manual)})")
    if not ranked or ranked[0][0] < MIN_SCORE:
        print("\n  -> No clear match. Claude would most likely answer without a skill.")
    elif len(ranked) > 1 and ranked[1][0] > 0.8 * ranked[0][0]:
        print("\n  -> Close call between the top two. Make their descriptions more distinct.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
