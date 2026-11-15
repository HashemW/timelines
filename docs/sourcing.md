# Sourcing rules

The whole point of Timelines is that a reader can check where every claim comes from.

1. **Cite only what was actually read.** Never list a book, page number or URL that the
   researcher (human or Claude) did not open. If a web page cites a book, the web page is
   the source and the book goes in `via`.
2. **Every event has at least one source.** Events with `importance: 1`, and anything
   contested, need at least two independent sources, ideally from different perspectives.
3. **Prefer stronger sources.** Primary documents and scholarship beat reference works,
   and reference works beat advocacy and journalism. Wikipedia is a fine place to start, but
   it shouldn't be the only source for anything important.
4. **Don't settle disputes by omission.** Where sources disagree (death tolls, who started
   what, whether people fled or were expelled), record each claim in `disputes` and attribute
   it to its sources.
5. **Write neutrally.** Describe what happened and who did it. Give the names each side uses
   (`altNames` / `names`). Quote loaded terms; don't adopt them.
6. **Places use the name from the period.** Add the modern name, or a note if the place
   was destroyed or renamed. Record coordinate `precision` honestly.
7. **Drafts are drafts.** Everything Claude produces is `status: "draft"` until a human
   has checked it and changed it to `reviewed`.
