# Current manuscript

This directory preserves the author-supplied `Request_grounded_authorization_for_agents__1_ (2).zip` and matching PDF received on 28 October 2026. The PDF and LaTeX were not rewritten during repository recovery.

- [Read the manuscript](main.pdf)
- [Edit the LaTeX source](main.tex)
- [Bibliography](references.bib)
- [Exact original ZIP](../releases/2026-10-28/Request_grounded_authorization_for_agents.zip)
- [Evidence and verification](../../research/paper_evidence/README.md)

The manuscript PDF SHA-256 is `65513cafa7f2023cc8e6cf59a7a06915bd7484dc04edb26586fb58bfc3b85458`.
The original ZIP SHA-256 is `7300a4255303e414e5c6c716fd8ad4205ad5e2adaf59d676e2bd6e7141b6b7ba`.

The source uses the included Springer Nature class and bibliography style. A normal build sequence is `pdflatex main`, `bibtex main`, then `pdflatex main` twice. Repository recovery checked the supplied PDF hash and static citation, cross-reference, and figure dependencies; it did not recompile or change the supplied PDF.

All 29 bibliography entries are cited, and the supplied source has no unresolved citation keys, missing figure files, duplicate labels, or unresolved LaTeX cross-reference labels in the static audit. These checks do not independently verify bibliographic metadata or the wording of every scientific claim.
