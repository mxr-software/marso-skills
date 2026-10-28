# The match pass

Read this when a brief names you as a match batch, or when you are judging a batch yourself in a serial run. The brief file carries every group to judge; this page carries the rules.

This pass decides which objects seen in different photographs are the same physical thing. A script has already matched everything unmistakable. You judge the cases it could not settle, looking at each photograph whole with the candidates boxed and numbered, and at a close-up of the same carrier (the worktop, the tray, the table) in each photograph when you need detail.

Hold this picture: this is the pass that goes wrong. Two identical chairs around a table, photographed twice, will tempt you into a merge you cannot justify. Over-counting is recoverable by a person looking at the result; a wrong merge is invisible downstream and looks exactly like a right one. When in doubt, refuse. A refusal is a result, not a failure.

## Hard rules

- Never edit the skill's files or an earlier round's outputs. Write only the one file your brief names.
- **Merge only on two independent lines of evidence**, written down in `evidence`: how it looks, what it rests on or stands next to, where it is. One line is not enough and the script will refuse the merge. "It is also a chair" is not a line.
- **When two candidates fit equally well, refuse.** Write a refusal with what argues for and against. Never pick the better-looking one.
- **At most one object from any one photograph in a merge.** If you want two, you have mis-matched, or detect saw one thing twice. Say which, and don't merge.
- **Believe the closer view about what a thing is, and the wider view about where it sits**, unless the closer view cuts it off or hides it.
- **A thing at or past the edge of the other view is simply absent there.** That is not evidence for a merge or against one. Two chairs in the wide shot and one in the close-up is one chair out of frame, not two merged.
- **Colour is weak evidence across photographs.** Lighting changes it. Shape, printed text and position are better.
- **A reading the better view contradicts is a correction**, not a merge and not a quiet rename. A difference in detail (one cabinet against a run of six doors) is not a correction; it is a different grain, and a refusal.
- Never invent an object, and never edit the detections to make a match work.

## What counts as evidence

Merge on two lines from different rows of this table. Two readings of the same thing are one line: "it looks like a black camera" and "it is black" are not two lines. Independent means the lines could fail separately.

| Line | When it is strong |
|---|---|
| **Registration**: the images overlap and both objects fall in the overlapping region | when one image is a close-up of a named region of the other |
| **Matched parent**: both hang off a parent already matched | strong, and the reason to work top-down. Weak if the parent is the floor |
| **Position under that parent**: the near-left corner of the table, the second shelf down | when the parent has a clear orientation in both views |
| **Distinctive appearance**: a mark, wear, a pattern, printed text you can read | when the detail is rare in this room. Weak for anything mass-produced |
| **Size**: the estimates agree | supporting only; it rules matches out more than in |
| **Neighbours**: the same neighbours, themselves already matched | when two or more agree |

Not evidence: the same category, the same label (labels agree by construction), being the only one left, tidiness, or the user's expectation.

**A merge carried by position is a real merge.** Rooms are full of identical siblings, and that is the case this pass exists for. Where appearance cannot separate them but position under a matched, clearly oriented parent can, that position is a full strong line. What would sink it is two candidates whose positions fit equally well: that is a refusal.

## What you write

One JSON file, and nothing else. Local ids only.

```json
{
  "batch_id": "m1",
  "merges": [
    {"members": ["img001-041", "img003-016"], "confidence": "high",
     "evidence": ["both stand behind the headphones, left of the laptop",
                  "the only camera in either photograph"]}
  ],
  "refusals": [
    {"candidates": ["img001-050", "img001-052", "img003-025", "img003-026"],
     "for": "same design, in the same caddy",
     "against": "left and right cannot be told apart between the views",
     "distinct_objects": 2}
  ],
  "corrections": [
    {"target": "img001-039", "better_view": "img003-008",
     "problem": "named 'chain strap'", "shows": "tortoiseshell sunglasses"}
  ],
  "vetoes": [
    {"check": "k2", "reason": "one is a clear glass vase, the other a matt black one",
     "drop": ["img001-031"]}
  ],
  "notes": ""
}
```

| Part | |
|---|---|
| `merges` | `members` (two or more local ids, one per photograph), `confidence` (`high`, `medium`, `low`), and `evidence`: **two or more** strings, each a different kind of line |
| `refusals` | `candidates`, `for`, `against` (never empty: if nothing argues against, you should have merged), and `distinct_objects`: how many physical things the candidates stand for. At least the most that share one photograph, at most the number of candidates |
| `corrections` | `target` (the wrong reading), `better_view` (the object in the view you believe), `problem`, `shows` |
| `vetoes` | only if your brief has an "Automatic matches to verify" section: `check` (its id), `reason`, and `drop` (the object that does not belong; leave it out to separate them all). Say nothing about a pair that is right |

**Confidence:** `high` is distinctive text or shape plus a matched parent or position, both unmistakable; `medium` is two lines that each have a plausible alternative; `low` is two weak lines, and it will be shown to the user as uncertain.

## Workflow

1. **Read your brief.** It lists each group and what the registration says about how the photographs relate.
2. **Open the whole photographs your brief lists.** Every candidate is boxed and numbered, the number being the last digits of its id in the brief's tables, and each group has its own colour. For each group, work out which object in each view is which from what is around it, and settle the unambiguous ones first. Open the group's close-up only when you need detail.
3. **If your brief has "Automatic matches to verify",** open its picture: each row is one pair the script matched on different names, each cropped with its surroundings. Veto a pair you can see is two objects; leave one that is right, or that you cannot tell.
4. **Write the file** and reply with one line: merges, refusals, corrections, vetoes.

Everything not mentioned stays its own object, which is the safe direction. Don't draw anything, zoom, or re-check.
