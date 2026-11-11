# strop docs: plain-wording worklist

Scope: `docs/*.md` in the strop repo, which the site renders as they are.
The docs are accurate. The problem is the vocabulary: many sentences describe
how the code is organised, not what the editor does or what you see.
This file lists the passages to change, with a rewrite to paste for each.
A rewrite marked **ask** is one where I could not tell what the user sees;
the text after it is a guess to correct, not a fact.

## Words to replace everywhere

| Word in the docs now | Say instead |
| --- | --- |
| owned job, owned work, worker, "off the input path/thread" | "in the background", "you can keep typing" |
| revision-owned, revision-checked, stale witness | "never shown/applied for an older version of the text" |
| admission, admits, admitted | "matches", "is listed", "is accepted" |
| receipt | "the record of what was done" (or just say what the review buffer shows) |
| barrier, write barrier | "one disk change at a time; the second one is refused until the first finishes" |
| source (meaning a file), source-backed | "file", "buffer" |
| surface, workspace (meaning a screen), investigation | "view", "picker", "Search" |
| namespace, endpoint, authority, resource URI | "host", "this machine or an SSH host", "an `ssh://` address" |
| refuses / is refused | fine, but say what message appears and what to do next |
| bounded | drop it, or give the limit as a number |
| retained, captured, pinned | "kept", "remembered", "as it was when..." |

## Highest-value fixes

1. **filesystem.md, "Relocation and barriers"** (F6-F10). The whole section is
   internal vocabulary. It holds real rules a user needs (finish a save
   before a rename; `:qa` refuses while an outcome is unknown).
2. **search.md, the review paragraph and "What each qualifier narrows"**
   (S1-S4). On `origin/main` they describe commands that 0.61 removes, in
   words like "stale witnesses refuse". The 0.61 text is already plain; take it.
3. **editor.md title, "Sessions", "Syntax and display", completion** (E1-E8).
   The title does not say what the page is for, and these paragraphs are
   lists of implementation properties.
4. **terminal-and-scripting.md**: the `settle` paragraph, the "Terminal
   buffers use bounded history..." paragraph and the two links into `plans/`
   (T1-T5). Also move `docs/nucleo-decision.md` out of the user docs (N1).

## Read this before merging the branches

The three track branches fork from a point 11-13 commits behind
`origin/main`. Their docs are older than main in some places and newer in
others. When they merge, the old text can come back.

- `origin/track/0.60-find`, `0.61-change` and `0.62-git` all still carry an
  editor.md paragraph that main has deleted ("owner-scoped retained
  feedback", entry E9), and lack main's "The project root", "Registers" and
  "Windows" sections.
- The same three say "**Ctrl-R** toggles the With field" in search.md. Main
  (0.58) changed that key to **Ctrl-T** and made `Ctrl-R {register}` paste a
  register. Keep main's wording.
- `0.61-change` and `0.62-git` still mention `:search-options`, which
  `0.60-find` removes. `0.60-find` and `0.62-git` still describe
  `:apply-change` and friends, which `0.61-change` removes.
- `:s` replacement: the local branch `worktree-agent-a035efe6a1607ffd6`
  (0.59) says the replacement is Vim's (`&`, `\1`). `0.61-change` still says
  "Replacement text is literal". Keep the 0.59 text.
- `:s` case: 0.59 says "same case rule as buffer search", 0.60 makes buffer
  search smart-case, 0.61 says `:s` "matches case exactly unless the pattern
  says otherwise". Keep the 0.61 sentence.

Entry format: where it is, the current words and the ref they were read
from, why a user trips on it, and the rewrite.

---

## docs/editor.md

Refs: `origin/main` unless stated.

### E1. Title and lead

- Now: "# Editor surfaces" / "the parts of strop you configure rather than
  drive. For the input grammar see the README's card"
- Problem: "surfaces" means nothing to a user, and the page also covers
  registers, windows, stdin and sessions, which you do drive. The site has no
  "README's card".
- Rewrite:

  > # Editing: indentation, themes, completion, registers, windows
  >
  > How strop indents, what the screen shows, how to change the theme, and
  > how completion, registers, windows and sessions behave. The keys are
  > listed in [vim-compat.md](vim-compat.md) and under `Space ?`. Searching
  > is in [search.md](search.md).

### E2. Sessions, first two sentences

- Now: "File/native work runs on owned jobs rather than blocking keystrokes.
  Sessions use private atomic files and lossless native paths, including undo
  history and the active window's jump history."
- Problem: describes the code; the user wants to know what comes back after a
  restart.
- Rewrite (whole section):

  > ## Sessions
  >
  > strop remembers each project. When you start it again in the same
  > directory, your cursor and scroll positions, undo history and jump
  > history are back. The session file is readable only by you.
  >
  > Each pane has its own jump list of 100 entries; a split starts with a
  > copy. `Ctrl-O` and `Ctrl-I` go back and forward through it. Jumping
  > somewhere new from the middle of the list does not throw away the newer
  > entries. `Space u` opens the undo history as a tree.
  >
  > Files on SSH hosts are not reopened from a saved session.

- **ask**: "lossless native paths" (file names that are not valid UTF-8
  survive?) and "retained jump records also restore their selections" (which
  selections?). I left both out.

### E3. Sessions, last sentence

- Now: "Remote contents and write permits are never restored from persisted
  sessions."
- Problem: "write permits" is from an older design; remote.md now says a
  connected host is simply editable.
- Rewrite: "Files on SSH hosts are not reopened from a saved session.
  Connect again and open them."
- **ask**: what does the user see after a restart where a remote file was
  open: an empty pane, a message, nothing?

### E4. Sessions, quit

- Now: "Quit-all writes one complete project snapshot before closing any
  buffer."
- Problem: "snapshot" is an internal thing here.
- Rewrite: "`:qa` saves the session for the whole project before it closes
  anything."

### E5. Syntax and display, second paragraph

- Now: "Syntax, structural indentation guides and search counts are
  revision-owned worker results. Long-line byte/cell checkpoints keep
  horizontal navigation and typing from repeatedly walking the line prefix.
  Horizontal views, block selection and carets share display-cell geometry;
  new edits preserve the buffer's line endings."
- Problem: all four sentences describe mechanisms.
- Rewrite:

  > Highlighting, indent guides and the search match count are worked out
  > in the background. They are never shown for an older version of the
  > text. Very long lines stay fast to scroll sideways and to type in.
  > Tabs and wide characters line up the same way for the cursor, block
  > selection and sideways scrolling. A file keeps its line endings (LF or
  > CRLF) when you edit it.

### E6. Indentation, last sentence

- Now: "Large-file analysis runs on the existing revision-checked worker,
  never the render path."
- Problem: "revision-checked worker" and "render path" are code terms.
- Rewrite: "In a large file the indentation is worked out in the
  background, so typing never waits for it."

### E7. Code completion, the paragraph after the key list

- Now: "Primary edits and represented imports are validated together and
  share the Insert undo group. Stale, overlapping or invalid edits are
  refused as a whole; unsupported snippets and commands are not approximated
  by a label insertion. Read-only and partial sources do not gain write
  authority through completion."
- Problem: "represented imports", "approximated by a label insertion" and
  "write authority" are not things a user can picture.
- Rewrite:

  > When a candidate also adds an import, both edits are made together and
  > one `u` undoes both. If the text changed so that the server's edit no
  > longer fits, nothing is inserted. A candidate that needs a snippet or a
  > server command strop does not support is not inserted at all. Completion
  > never changes a read-only buffer.

- **ask**: what is a "partial source"? A file still loading?

### E8. Code completion, broken sentence

- Now: "Read-only source collections do not open completion or gain edit
  server. The menu shows kind, source and detail."
- Problem: the first sentence is cut off mid-phrase ("gain edit server"),
  and 0.61 removes read-only collections. `origin/track/0.61-change` already
  deletes it.
- Rewrite: delete the sentence on main too.

### E9. Paragraph that exists only on the track branches

- Now (`origin/track/0.60-find`, `0.61-change`, `0.62-git`; not on main):
  "Failed or unconfirmed saves, connection/admission failures and terminal
  decisions use the same owner-scoped retained feedback. ... **`:explain`**
  retains the complete owner, detail and evidence. ... it never cancels
  work, clears a save barrier or marks an unconfirmed outcome as successful."
- Problem: main dropped it; a merge can bring it back. It is the densest
  jargon in the docs.
- Rewrite: resolve the merge in main's favour. If you want the facts kept:

  > A failed save, a failed connection or a terminal that needs a decision
  > leaves a message that stays until you deal with it. Moving, searching or
  > a later success message does not clear it. `Space a` lists what you can
  > do about it and `:explain` shows the full detail. Dismissing the message
  > only hides it. It does not cancel anything and does not mark a save as
  > done.

### E10. Panes, previews and language services: the LSP sentences

- Now: "The modeline presents owned LSP starting, ready, refused and failed
  states as compact badges. Long server prose does not displace mode and
  position." and "the next language request names the failure and starts one
  scoped reattach; repeat the request after it is ready."
- Problem: "owned", "scoped reattach", "language request".
- Rewrite:

  > The status line shows a short badge while a language server is
  > starting, and `LSP!` when it failed or was refused. A long error from
  > the server never pushes the mode or the position off the line.
  > `:explain` opens the full story in a read-only buffer: which server,
  > which project, and why it failed.
  >
  > ... After the third restart, or if the server never started, the next
  > thing you ask of it (go to definition, hover, and so on) shows the
  > reason and tries once more to start it. Repeat the command when the
  > server is ready.

### E11. Same section: recovered servers

- Now: "recovered servers clear their old failure without erasing another
  workspace's problem or an independent warning"
- Problem: hard to parse.
- Rewrite: "When a server recovers, its failure message goes away. Messages
  about other projects or other problems stay."

### E12. Same section: pane titles

- Now: "Local pane titles use workspace-relative paths; duplicate
  directories, outside-workspace paths and remote authority remain
  identifiable."
- Problem: "remote authority" is URL-spec vocabulary.
- Rewrite: "A pane title is the file's path inside the project. Files with
  the same name show enough of the path to tell them apart, files outside
  the project show their full path, and files on an SSH host show the host."
- **ask**: confirm that is what the titles show.

### E13. Same section: preview width

- Now: "File, search and symbol previews automatically reclaim unused
  result-list width from short admitted labels, within bounded stable layout
  limits. Long paths keep their list budget; narrow terminals retain stacked
  or omitted preview fallbacks."
- Problem: "admitted labels", "bounded stable layout limits", "list budget".
- Rewrite: "When the result rows are short, the preview takes the spare
  width. When paths are long, the list keeps its width. In a narrow terminal
  the preview moves below the list, or is hidden."

### E14. Section heading

- Now: "## Panes, previews and language services"
- Problem: three unrelated things; the language-server part is the bulk and
  is hard to find.
- Rewrite: split into "## Pane titles and previews" and "## Language
  servers".

### E15. The look, first paragraph

- Now: "Every surface reads its colours from one token set: three background
  planes (`base` < `surface` < `raised`), four greys for text, one accent
  ... Cards ... share one primitive ... Chrome appears only when it carries
  information"
- Problem: this is the design system. "token set", "planes", "primitive" and
  "chrome" are designer words. The useful part (what each indicator means,
  and when it appears) is buried.
- Rewrite:

  > ## What is on screen
  >
  > The accent colour marks where you are and what will happen next: the
  > mode chip, the current line number, a pending operator, the cursor in an
  > input field, and the characters a search matched. In a list, the
  > selected row has a `▌` at its left. `●` marks the theme in use and
  > buffers with unsaved changes.
  >
  > Things appear only when they have something to say. The scrollbar is
  > hidden when the whole file fits. Pane titles appear when there are two
  > or more panes. `LSP!` appears when a language server failed. `Spaces:N`
  > appears when a buffer's indent differs from your default.

- **ask**: "the picker's scope row only when a scope differs from the
  default": what is a scope here (a directory other than the project root)?

### E16. The look, second paragraph

- Now: "then retained feedback by severity (`✗` failure, `▲` warning, `●`
  info) with its `space a` or `:explain` hint" and "the service badge"
- Problem: "retained feedback", "service badge".
- Rewrite: "Messages appear on a row above the status line, and only while
  there is one to show: first the answer to your last key, then any message
  still waiting for you (`✗` failure, `▲` warning, `●` info) with the key
  that deals with it, `Space a` or `:explain`. The status line itself shows
  the mode, the branch, the path, then, only when not zero, the diagnostics
  count (`●1 ▲2`), the language-server badge, the indent and the position."

### E17. Indentation: design aside

- Now: "one punctuation rule decided by the language registry, not
  per-language editor code:"
- Problem: tells the reader how the code is organised.
- Rewrite: "A colon at the end of a line indents the next line one level
  deeper, in the languages where it opens a block:"

### E18. Indentation: cursors and repeat

- Now: "Each cursor uses its own source context, indentation unit and line
  endings. Undo, counted insertion and dot repeat preserve the operation
  rather than copying generated indentation from a different location."
- Problem: abstract.
- Rewrite: "With several cursors, each new line is indented for the place
  it is in. `.` and a count work out the indentation again at the new place.
  They do not copy the spaces from the first one."

### E19. Indentation: other files

- Now: "Named prose/unsupported files inherit whitespace; unnamed scratch
  buffers retain generic brace behavior. This is not a formatter, HTML tag
  indentation, or keyword-based `end`/`else` alignment."
- Problem: "inherit whitespace" and "generic brace behavior" need decoding.
- Rewrite: "In prose and in languages not listed here, a new line copies the
  indentation of the line above. A new buffer with no name still indents
  after an opening brace. strop does not reformat code, does not indent HTML
  tags, and does not line up `end` or `else` with their opening keyword."
- **ask**: confirm "inherit whitespace" means "copy the line above".

### E20. Indentation: C/C++ details

- Now: "C-mapped buffers (`.h`, `.c`) behave like C++, since headers detect
  as C. The second colon in a C++ scope operator (`std::`) restores
  statement indentation after the first colon's possible-label
  interpretation."
- Problem: explains the detector, not the result.
- Rewrite: "`.c` and `.h` files get the same rules as C++. Typing `std::`
  does not leave the line pulled out as a label: the second colon puts the
  indentation back."

### E21. Themes: picker details

- Now: "the selected row's canonical name and full description appear in a
  bounded detail area. Small terminals omit decoration before hiding
  identity or input."
- Problem: "canonical name", "bounded detail area", "identity".
- Rewrite: "Below the list you see the selected theme's name, as you would
  type it, and its description. In a small terminal the swatches and the
  description go first; the names and the search field stay."

### E22. Themes: terminals

- Now: "Existing terminal sessions update their default colors without
  overwriting child-selected truecolor or OSC palette customizations."
- Problem: "child-selected", "OSC palette".
- Rewrite: "Open terminals switch to the new theme's default colours.
  Colours a program inside the terminal chose for itself are left alone."

### E23. Themes: retired names

- Now: "(including the retired `dark`, `light`, `strop-ink`, `catppuccin-*`
  and `nord`)"
- Problem: lists themes that no longer exist; a new user reads it as a list
  of themes.
- Rewrite: "A config that names a theme strop does not have starts on
  `hone` and shows a warning with the six names." Move the removed names to
  the changelog entry that removed them.

### E24. Themes: contrast sentence

- Now: "every one holding the same contrast contract: text ≥ 10:1, secondary
  ≥ 7:1, comments and every syntax ink ≥ 4.5:1 on both the base and the
  surface plane, a visible Visual selection"
- Problem: "contract", "ink", "plane".
- Rewrite: "All six meet the same contrast minimums: main text at least
  10:1, secondary text 7:1, comments and syntax colours 4.5:1."

### E25. Syntax and display, first paragraph

- Now: "the same injection pipeline highlights fenced examples inside Rust
  documentation comments ... Comment delimiters remain comments; independent
  documentation groups cannot leak unclosed fences into each other. Only
  rustdoc defaults unlabelled fences to Rust."
- Problem: "injection pipeline", "leak unclosed fences".
- Rewrite: "Code blocks inside Markdown are highlighted in their own
  language, for any of the 26. The same goes for code examples in
  documentation comments: Rust doc comments, JS/TS/TSX, C/C++ and Java doc
  blocks, Go block comments above a declaration, and Python docstrings. A
  code block you forgot to close ends with its comment. In Rust doc
  comments a block with no language is treated as Rust."

### E26. Code completion, first paragraph

- Now: "incremental words from the current editable source" / "Kind chips
  use the symbol picker's quiet family colors, and the ASCII `lsp` / `buf`
  provenance tags stay color-coded without requiring an icon font"
- Problem: "editable source", "provenance tags", "quiet family colors".
- Rewrite: "In Insert mode strop suggests completions from the language
  server and words from the current buffer. Words work without a language
  server. Each row shows the kind (function, struct, ...), where it came
  from (`lsp` or `buf`) and a short detail. No icon font is needed."

### E27. Code completion, config

- Now: "an opened manual session still follows typing. `enabled = false`
  also disables manual invocation and retires completion-only work."
- Problem: "session", "retires completion-only work".
- Rewrite: "With `auto_popup = false` the menu opens only when you ask
  (`Ctrl-Space`), and then updates as you type. `enabled = false` turns
  completion off, the keys included."

### E28. Registers, first sentence

- Now: "One register file serves every text input."
- Problem: "register file" reads as a file on disk.
- Rewrite: "The same registers work everywhere you type: buffers, the `:`
  and `/` lines, and every picker field."

### E29. The project root (0.59 wording)

- Now (`worktree-agent-a035efe6a1607ffd6`): "The session and draft-recovery
  files, buffer names and the file watcher follow the new root." and, on
  main too, "does not re-root anything"
- Problem: "file watcher" and "re-root" are internal.
- Rewrite: "After `:cd`, buffer names are shown relative to the new
  directory, and the saved session is the new project's." / "does not change
  the project".
- **ask**: what does "the file watcher follows" mean for the user: changes
  on disk are noticed under the new directory?

---

## docs/search.md

Refs: `origin/main` unless stated. For passages the tracks rewrote, the
newest wording is named.

### S1. Review paragraph (stale after 0.61)

- Now (`origin/main`, also 0.60 and 0.62): "Review preparation is cancellable
  background work. **Space a** on a review or receipt exposes **Apply to
  buffers**, **Save files** ... `:apply-change`, `:save-change` and
  `:cancel-change` are the Ex shortcuts. ... Dirty open source text wins
  over disk, stale witnesses refuse ... `:undo-change` ... reverts the
  newest applied multi-file change only while its recorded target revisions
  still own that change."
- Problem: 0.61's changelog removes all four commands and both receipts.
  "Stale witnesses refuse" and "target revisions still own that change" are
  not readable.
- Rewrite: use the "## Replace across files" section from
  `origin/track/0.61-change`. It is already plain ("`Enter` in the review
  changes every file and writes it", "`u` puts the buffers and the files
  back"). Nothing to add.

### S2. What each qualifier narrows

- Now: "**File find** narrows the walk; **search/replace** narrows admission
  per line." / "Evidence a row cannot decide (a scratch buffer with no path)
  admits — overfetch, never a silent drop." / "Operator-free content never
  enters admission; the local fuzzy ranker narrows it."
- Problem: "the walk", "admission", "overfetch", "local fuzzy ranker".
- Rewrite:

  > ## Where the filters apply
  >
  > - In **Files** the filters decide which files are listed.
  > - In **Search** and **Replace** they decide which files are searched.
  > - In **document symbols** and the **jump list** they filter the rows
  >   already in the list, as you type. On the jump list,
  >   `language:cpp path:tests` keeps the jumps inside C++ files under
  >   `tests/`, and plain words match the text of the line you jumped to.
  > - A row a filter cannot judge is kept, not hidden. A scratch buffer has
  >   no path, so `path:` keeps it.

- **ask**: the last bullet on main ("Operator-free content never enters
  admission; the local fuzzy ranker narrows it"). My guess is "plain words
  with no qualifier are fuzzy-matched against the rows", but I cannot tell
  where that applies.

### S3. Jump list description

- Now: "retained lists" / "The jump list contains origins left by jump
  commands, with a synthetic row for the current position; it is navigation
  history, not an undo list."
- Problem: "retained", "origins", "synthetic row".
- Rewrite: "The jump list holds the places you jumped from, plus a row for
  where you are now. It is a history of places, not of edits."

### S4. Coming back to Search

- Now: "Opening a source hides Search; `Space /` returns to the retained
  investigation. Re-entry refreshes through owned work in its captured
  namespace/root even if focus or cwd changed."
- Problem: "retained investigation", "owned work", "captured namespace/root".
- Rewrite: "Opening a result hides Search. `Space /` brings it back with
  your query and results. It searches again in the directory (and on the
  host) it was first opened for, even if you are now in a file somewhere
  else."

### S5. `:search-options` (removed in 0.60)

- Now (`origin/main`, 0.61, 0.62): "`:search-options` shows the separate
  visibility controls."
- Problem: the 0.60 changelog removes the command.
- Rewrite (already on `origin/track/0.60-find`): "`Alt-H` and `Alt-I` in the
  field turn hidden and ignored files on and off."

### S6. The Ctrl-O collection bullets (stale after 0.61)

- Now (`origin/main`): "**Ctrl-O** collects exactly the included matches
  into a read-only source-backed collection." / "with surrounding context,
  source syntax, match evidence and line numbers" / "never write through to
  source buffers or save them"
- Problem: 0.61 makes collections editable and removes the read-only kind.
  "Source-backed" and "match evidence" are internal.
- Rewrite: use "## Collections: edit every hit in one buffer" from
  `origin/track/0.61-change`. One touch-up there: "It is an ordinary editing
  buffer whose text is the files' text" reads better as "It is an ordinary
  buffer. What you edit in it is edited in the files."

### S7. Lead paragraph

- Now: "One bounded qualifier grammar is shared by every picker surface"
- Problem: "bounded qualifier grammar", "picker surface".
- Rewrite: "The same filters work in every search field: Files (`Space f`),
  Search (`Space /`), Replace (`Space R`), document symbols, workspace
  symbols (`Space S`) and the jump list (`Space j`). Learn them once."

### S8. The With toggle

- Now (`origin/main`): "**Ctrl-T** toggles the With field without restarting
  the search or losing either field's text, caret, mode, selection or
  workset."
- Problem: "workset" is not defined anywhere. (The track branches say
  Ctrl-R here; that is the old key. See the merge note at the top.)
- Rewrite: "**Ctrl-T** shows or hides the With field. The search keeps
  running, both fields keep their text and cursor, and the hits you excluded
  stay excluded."
- **ask**: confirm "workset" means the included and excluded hits.

### S9. Built-in search

- Now: "Local enumeration and content matching run entirely in Rust using
  the `ignore`/`grep` crate family — `rg` is not required on your machine."
- Problem: names crates; the user fact is at the end.
- Rewrite: "Search is built in. You do not need `rg` on your own machine.
  It follows your `.gitignore` rules the way `rg` does."

### S10. "Search workspace" and "investigation"

- Now: "## The Search workspace" / "`Space /` opens or resumes one large
  Search workspace; `Space R` resumes the same investigation with the
  replacement field visible."
- Problem: "workspace" also means the project elsewhere in the docs;
  "investigation" is coined.
- Rewrite: "## Search across the project" / "`Space /` opens Search, or
  brings it back as you left it. `Space R` does the same with the With
  (replacement) field showing."

### S11. Filter-only queries

- Now: "Filter-only file finding lists eligible files; content search needs
  an expression. Unignored dotfiles are included by default; `.git` metadata
  is excluded."
- Problem: "eligible", "expression", "`.git` metadata".
- Rewrite: "With only filters typed (`language:rust path:src/`), Search
  lists the files they match. To search inside the files, add the text to
  look for. Dotfiles are searched unless your ignore rules skip them. The
  `.git` directory never is."

### S12. Ex substitution: the preview paragraph

- Now (0.61 wording, `origin/track/0.61-change`): "While composing, Strop
  shows the actual removed and inserted lines, substitution count, scope and
  offscreen extent; ... Enter applies that displayed plan as one undo unit.
  Invalid or incomplete input replaces the previous preview rather than
  executing it, large plans resolve off the input path, and Esc cancellation
  leaves bytes, registers and undo history untouched."
- Problem: "displayed plan", "offscreen extent", "resolve off the input
  path".
- Rewrite:

  > While you type the command, strop shows the lines it would remove and
  > the lines it would add, how many replacements there are, and how many of
  > them are off screen. Enter makes exactly the change shown, and one `u`
  > undoes it. A pattern that is not finished or not valid changes nothing.
  > On a big file the preview is worked out in the background and typing
  > stays quick. Esc cancels and leaves the text, the registers and the undo
  > history as they were.

  Also rename the heading "## Ex substitution" to "## Substitute: `:s`".

### S13. Buffer search: dialect

- Now (0.60 wording): "The dialect is bounded Vim-magic (and `\v` very
  magic): collections, groups, alternation, repetition and backreferences;
  unsupported constructs report an error instead of becoming literals.
  Search previews and Enter use the same counted resolver."
- Problem: "bounded Vim-magic", "counted resolver".
- Rewrite: "Patterns use Vim's default syntax, and `\v`: `[...]`, groups,
  `\|`, repetition and backreferences. Anything not supported gives an
  error; it is never searched for as plain text. The match shown while you
  type is the one Enter goes to, with a count as well."

### S14. SSH scopes

- Now: "## SSH scopes" / "Search here uses the same query fields, inclusion
  decisions and source previews as local Search, on explicitly scoped SSH
  directories: ... a host without `rg` refuses search without a fallback."
- Problem: "scopes", "inclusion decisions", "explicitly scoped".
- Rewrite: "## Searching on an SSH host" / "Search works the same in a
  directory on an SSH host: the same fields, the same include and exclude
  keys, the same previews. It runs `rg` on the host. If the host has no
  `rg`, Search says so and does not run. Collections work there. Replace
  does not, yet." (The last two sentences follow `origin/track/0.61-change`.)

### S15. SSH limits

- Now: "Source enumeration is limited to 100,000 selected paths or 16 MiB of
  names; rg records to 1 MiB and 4,096 submatches; decoded batches to 4 MiB;
  a request publishes at most 100,000 rows or 64 MiB of owned row data."
- Problem: half of these are protocol buffer sizes no user can act on.
- Rewrite: "A search on a host stops with an error when it passes 100,000
  files, 100,000 result rows, or a line longer than 1 MiB. It never shows
  part of the results as if they were all of them."
- **ask**: which of the other limits (16 MiB of names, 4,096 submatches,
  4 MiB batches, 64 MiB) can a user actually hit, and what message appears?

### S16. The grammar: small terms

- Now: "`kind:` — on symbol surfaces, the declaration's classification" /
  "juxtaposition is an implicit AND" / "each content atom" / "visibility
  overrides for this query" / "any query surface"
- Problem: each needs a second reading.
- Rewrite: "`kind:` — in the symbol pickers, what the symbol is
  (`kind:function`, `kind:struct`, ...)." / "words side by side mean AND" /
  "each word" / "`hidden:` / `ignored:` — include or exclude hidden files
  and ignored files for this query" / "any search field".

### S17. The grammar: suggestions and old flags

- Now: "`Ctrl-Space` in any query field offers parser-driven suggestions
  from the caret's position ... Old `-t`/`-g` UI flags are ordinary text
  now."
- Problem: "parser-driven"; the second sentence is history a new user never
  saw.
- Rewrite: "`Ctrl-Space` in any search field suggests what can come next at
  the cursor. `:help query` covers quoting, the language names, errors and
  examples." Move the `-t`/`-g` note to the changelog.

### S18. Case sentence that refers to the past

- Now (`origin/main`): "or `case:smart` for the former uppercase-sensitive
  behavior"
- Problem: "former" assumes the reader knows an old version.
- Rewrite: take the paragraph from `origin/track/0.60-find`: "**Case is
  smart everywhere:** an all-lowercase query matches either case; one
  capital letter makes case count."

### S19. Replace with several terms (0.61 wording)

- Now (`origin/track/0.61-change`): "A query with several positive terms is
  a fine search and an ambiguous replace; With asks for exactly one."
- Problem: "positive terms"; the sentence is a little too neat.
- Rewrite: "Replace needs exactly one thing to look for. A query with
  several words can be searched but not replaced; With says so."

### S20. Quickfix note (0.61 wording)

- Now (`origin/track/0.61-change`): "`:cdo norm …` waits for `:norm`."
- Problem: unclear whether this means "not available until `:norm` ships"
  or something about ordering.
- **ask**: if it means "`:norm` is not in this version yet", say "`:cdo
  norm ...` is not available yet." Note 0.59 adds `:norm`, so the sentence
  may be wrong once both are merged.

### S21. Search here

- Now: "**Space a → Search here** captures that directory without changing
  cwd."
- Problem: "captures", "cwd".
- Rewrite: "... searches only that directory. The project root stays where
  it is."

---

## docs/filesystem.md

Refs: `origin/track/0.61-change` is the newest for the top of this file;
the rest is the same on every ref.

### F1. Title and lead

- Now (0.61): "# The filesystem workspace" / "`Space e` reveals the current
  source in its parent. Browsing keeps the process cwd unchanged; Enter
  opens a structured entry"
- Problem: "filesystem workspace", "source", "process cwd", "structured
  entry".
- Rewrite:

  > # Files and directories
  >
  > Browse a directory, and create, rename, move, copy and delete files
  > without leaving strop.
  >
  > Open a directory with `strop DIRECTORY`, `:browse` or `:e DIRECTORY`.
  > `Space e` opens the directory of the current file with the cursor on
  > it. Enter opens the entry under the cursor; `-` or Backspace goes up.
  > Browsing does not change the project root.

### F2. Review → Apply → Receipt

- Now: "Filesystem mutations use **Review → Apply → Receipt**, locally and
  on SSH hosts"
- Problem: three capitalised stage names with no explanation. "Receipt" is
  never defined. `:fs operations`, `:fs verify` and `:fs undo` appear in the
  code block and are never explained.
- Rewrite:

  > Nothing changes on disk until you confirm. Each `:fs` command opens a
  > review that lists the exact steps. `Enter` (or `:fs apply`) does them;
  > `q` (or `:fs cancel`) drops them. Afterwards strop keeps a record of
  > each step and whether it succeeded.
  >
  > - `:fs operations` lists what was done in this run of strop.
  > - `:fs verify OPERATION STEP` checks the disk to see whether a step
  >   really happened. Use it when a step's result is unknown.
  > - `:fs undo OPERATION STEP` reverses a step.

- **ask**: confirm the three one-line descriptions, and where the user
  finds the OPERATION and STEP numbers.

### F3. `:apply-change` / `:cancel-change`

- Now (`origin/main`, 0.60, 0.62): the code block lists `:apply-change` and
  `:cancel-change`; "The filename draft" says "`:apply-change` performs
  filesystem changes; `:cancel-change` returns to the intact draft".
- Problem: the 0.61 changelog removes both.
- Rewrite: already fixed on `origin/track/0.61-change` ("`Enter` or `:fs
  apply` performs the filesystem changes; `q` or `:fs cancel` returns to the
  intact draft"). Make sure 0.62's copy does not win the merge.

### F4. The rules paragraph

- Now: "Relative filesystem destinations use the current Directory, or the
  current source's parent; source-less buffers use the workspace root.
  Explicit resource URIs select another namespace. Creation never truncates
  an occupied name; rename/move is no-clobber. Review lists missing-parent
  creation explicitly. Stored-copy and buffer-copy select different versions
  without saving the source."
- Problem: "resource URIs", "namespace", "no-clobber", "missing-parent
  creation", "stored-copy".
- Rewrite:

  > A relative name is taken from the directory you are browsing, or from
  > the directory of the current file. In a buffer with no file it is taken
  > from the project root. strop never overwrites: creating, renaming or
  > moving onto a name that exists is refused. If parent directories have
  > to be created, the review lists each one. `:fs copy stored` copies the
  > file as it is on disk; `:fs copy buffer` copies the text in the buffer,
  > unsaved edits included. Neither saves the file.

- **ask**: "Explicit resource URIs select another namespace". Does it mean
  you can give an `ssh://` address as a destination? Can you copy between
  this machine and a host? I left the sentence out.

### F5. Trash and refusals

- Now: "Trash uses native recovery facilities where supported; remote Trash
  is unavailable, not an alias for permanent removal. Recursive removal of
  non-empty directories and unsafe alias/root operations are refused."
- Problem: "native recovery facilities", "unsafe alias/root operations".
- Rewrite: "`:fs trash` moves the file to your system's trash. On an SSH
  host there is no trash, and `:fs trash` is refused; it never deletes
  instead. `:fs remove` deletes for good. It will not remove a directory
  that still has files in it, and it will not remove `/` or the project
  root."
- **ask**: what is an "alias" operation: a symlink to the same directory?

### F6. Heading "Relocation and barriers"

- Now: "## Relocation and barriers"
- Problem: neither word is a user's word.
- Rewrite: "## Open files, saves in progress, and quitting"

### F7. Same section, first paragraph

- Now: "Confirmed relocation keeps source text, history and document
  identity. Pending saves and unconfirmed operations block conflicting work.
  Receipts survive leaving the view; verification never blindly retries a
  mutation."
- Problem: every noun is internal.
- Rewrite: "When you rename or move a file that is open, the buffer follows
  it and keeps its text, unsaved edits and undo history. While a save is
  running, or while a step's result is unknown, strop refuses another
  change to the same file. The record of steps stays after you leave the
  review. `:fs verify` only looks at the disk. It never does the step
  again."

### F8. Same section: the write barrier

- Now: "Local saves/save-as and local filesystem mutations use a
  conservative per-editor write barrier, including parent aliases. Let a
  pending save finish before applying a local filesystem review, and resolve
  unconfirmed receipts before saving."
- Problem: "per-editor write barrier", "parent aliases", "unconfirmed
  receipts".
- Rewrite: "On your own machine strop does one disk change at a time. If a
  save is still running, wait for it before you confirm a file operation.
  If a file operation ended with an unknown result, settle it with `:fs
  verify` before you save."
- **ask**: is the second change refused with a message, or queued? What
  does the message say?

### F9. Same section: move verification

- Now: "Move verification and recovery require the recorded post-publication
  version: finding the same inode at a pathname is not sufficient ownership
  evidence."
- Problem: unreadable for a user.
- **ask: what does the user see?** Guess: "`:fs verify` and `:fs undo` on a
  move act only if the file is still exactly as strop left it. If another
  program changed it since, they refuse and say so."

### F10. Same section: quitting

- Now: "Receipts are in-memory, not crash recovery. Graceful global exit
  refuses unresolved outcomes; explicit `:qa!` reports them and exits
  unsuccessfully rather than claiming they were resolved or persisted."
- Problem: "graceful global exit", "unresolved outcomes".
- Rewrite: "The record of steps is lost when strop exits or crashes. `:qa`
  refuses to quit while a step's result is unknown. `:qa!` lists those
  steps, quits, and exits with an error status."

### F11. Same section: lock files

- Now: "Removing an otherwise empty directory may retire its validated,
  quiescent protocol locks. Active locks, unknown entries and other
  directory contents cause refusal; partial housekeeping is reported even
  when cancellation prevents removal."
- Problem: "validated, quiescent protocol locks", "partial housekeeping".
  Lock files are not explained anywhere in the docs.
- Rewrite: "strop keeps a small lock file beside each file it has open. A
  directory that holds only leftover lock files counts as empty: removing
  it deletes them too. A lock for a file that is still open, or anything
  else in the directory, stops the removal. If strop deleted some lock
  files and then could not remove the directory, it tells you."
- **ask**: confirm, and give the lock files' name pattern so users
  recognise them.

### F12. The filename draft

- Now (0.61): "`:fs edit` enters a name-only **filename draft**. ...
  Browsing or refreshing the directory retains edited names and source
  provenance. ... Copies need a distinct name; ambiguous joins and
  conflicting targets refuse instead of guessing which file a row
  represents."
- Problem: "name-only draft", "source provenance", "ambiguous joins".
- Rewrite:

  > ## Renaming by editing the list
  >
  > `:fs edit` makes the directory listing editable: change the names as
  > text. Motions, edits, yanking and pasting whole lines, undo and macros
  > all work, and nothing on disk changes yet. `:w` opens the review;
  > `Enter` (or `:fs apply`) does the renames; `q` (or `:fs cancel`) goes
  > back to your edited list. Your edits survive a refresh or a visit to
  > another directory. `:fs discard` throws them away. A pasted line makes
  > a copy and needs a new name. If strop cannot tell which file a line
  > stands for, or two lines end up with the same name, it refuses.

- **ask**: confirm that pasting a line means "copy this file", and what
  "ambiguous joins" (`J` on two rows?) refers to.

### F13. Indentation controls

- Now: "The modeline names the effective input owner and source setting.
  Matching delimiters use the same cancellable source resolver as `%`,
  without moving the view." / "Changing indentation settings never rewrites
  existing bytes."
- Problem: "effective input owner", "cancellable source resolver". The
  section also sits in the wrong file; it is about editing, not files.
- Rewrite: move the section to editor.md under "Indentation". "Changing
  these settings does not change text already in the file. The status line
  shows the indent in use."
- **ask**: the "Matching delimiters ..." sentence. What does the user see:
  the matching bracket highlighted without the view scrolling?

### F14. SSH hosts: lead

- Now: "with the same review, receipts and verification: ... copy a regular
  file (stored bytes or the pinned buffer) and remove. The differences are
  honest limits of SFTP:"
- Problem: "pinned buffer"; "honest limits" is tone.
- Rewrite: "On an SSH host the same commands work, with the same review
  first and the same record afterwards: create files and directories,
  rename, move, copy a file (as it is on the host, or the text in your
  buffer) and remove. What differs, because of how SFTP works:"

### F15. SSH hosts: bullets

- Now: "files are created exclusively" / "**No atomicity across steps** and
  no lock against other programs on the host. A step whose reply was lost
  is reported unconfirmed; `:fs verify` observes the host and never retries
  it."
- Problem: "created exclusively", "atomicity", "observes the host".
- Rewrite: "If the name appears on the host between the review and the
  step, the step fails instead of overwriting." / "**Steps are not
  all-or-nothing.** If step 3 of 5 fails, steps 1 and 2 stay done. Nothing
  stops another program on the host from changing the same files. If the
  connection drops before the host answers, the step is shown as
  unconfirmed. `:fs verify` checks the host to see whether it happened. It
  never runs the step again."

---

## docs/terminal-and-scripting.md

Refs: `origin/main` (the same on every ref).

### T1. The `settle` paragraph

- Now: "`settle [MS]` returns when finite owned work drains ... Pure grammar
  work keeps key, paste, repeat and macro ordering; filesystem and service
  jobs require an explicit settle before a script relies on their result.
  An interactive shell is not an eternally pending job: terminal settle
  covers admission/transport/frame barriers, not arbitrary command
  execution. Script completion explicitly closes and drains its owned
  terminal sessions." Also the table row: "return when finite work drains".
- Problem: "finite owned work", "admission/transport/frame barriers",
  "drains".
- Rewrite:

  > `settle [MS]` waits until background work has finished: file loads,
  > saves, searches, language-server replies. It fails the script if that
  > takes longer than MS milliseconds (30,000 by default). Keys, pastes,
  > repeats and macros always run in order and need no `settle`. Anything
  > that reads a file or asks a language server does: put a `settle` before
  > the script depends on the result. A terminal counts as settled once the
  > shell has started and the screen is drawn. `settle` does not wait for a
  > command you ran in it; use `wait MS` for that. When the script ends,
  > its terminals are closed.

  Table row: "wait until background work is finished; fails after MS
  (default 30000)".

### T2. "Terminal buffers use bounded history ..."

- Now: "Terminal buffers use bounded history, input and immutable snapshots.
  One TERMINAL-mode view controls PTY geometry; mirrors never independently
  resize it. Linux supervision requires pidfds. Source builds require **Zig
  0.16.0** explicitly installed for the pinned static emulator; prebuilt
  users need neither Zig nor a Ghostty installation. See [plan 0090 §4]"
- Problem: "immutable snapshots", "PTY geometry", "mirrors", "supervision",
  "pinned static emulator", and a plan reference.
- Rewrite:

  > Scrollback is limited; the oldest lines are dropped. When one terminal
  > is shown in two panes, the pane you type in sets its size. On Linux the
  > terminal needs kernel 5.3 or newer. The prebuilt strop needs nothing
  > else installed. To build from source you need Zig 0.16.0.

- **ask**: the scrollback limit as a number, and whether "kernel 5.3"
  (pidfd support) is the right way to state the requirement.

### T3. Links into `plans/`

- Now: "See [plan 0090 §4](../plans/0090-one-editor.md)." and "See [tracing
  design](../plans/0029-session-tracing.md)."
- Problem: internal design documents. `../plans/` is outside `docs/`, so
  the links most likely break on the site.
- Rewrite: delete both sentences.

### T4. Isolation paragraph

- Now: "Isolation: child screen/clipboard/window commands cannot control the
  outer terminal; clipboard reads and writes are denied (your own yank is
  separate authority). ... Deliberately detached processes outside the owned
  session can outlive it."
- Problem: "separate authority", "owned session".
- Rewrite: "A program running in the terminal cannot change your real
  terminal's title, window or screen, and cannot read or write your
  clipboard. Your own `y` still copies. `:w!` and `:set noro` do not turn a
  terminal into a file: yank the text into an ordinary buffer to keep it.
  Closing a split does not stop the program in it. A program that put
  itself in the background (`nohup`, `setsid`) can keep running after its
  terminal is closed."

### T5. Two top-level titles on one page

- Now: "# Terminals" and, halfway down, "# Headless scripts and traces"
- Problem: two unrelated pages in one file. Someone looking for how to
  report a bug will not look under "terminal".
- Rewrite: split into `docs/terminal.md` and `docs/scripting.md` (or
  `docs/bug-reports.md`), each with one title and a first sentence that says
  what the page is for. Suggested lead for the second: "Run strop without a
  screen from a script of keys, and record a session to attach to a bug
  report."

### T6. Headless lead and `key` note

- Now: "`strop headless SCRIPT [+LINE] [FILE[:LINE]]` uses the same editor
  and service handlers" / "`key` is an already-normalized semantic editor
  command, not terminal input." / table: "one semantic editor key", "one
  physical key/text/paste event; preserves modifiers and release/repeat"
- Problem: "service handlers", "already-normalized semantic".
- Rewrite: "`strop headless SCRIPT [FILE]` runs the real editor with no
  screen and feeds it the script." / "`keys` is what you would type. `key`
  and `input` are for tests that need one exact key event; most scripts
  never need them."

### T7. `quit-intent`

- Now: "send the GUI close request (not a Ctrl-C editor shortcut)"
- Problem: strop is a terminal editor; "GUI close request" has no meaning to
  the reader.
- **ask: what does the user see?** Guess: "ask strop to quit, as closing the
  terminal window does".

### T8. `:trust`

- Now: "Headless `:trust` uses the same explicit per-project consent and
  `XDG_STATE_HOME` (or `$HOME/.local/state`) store as the TUI. It does not
  restore or automatically persist editor sessions. Project configuration
  never grants itself permission to execute commands."
- Problem: `:trust` is not explained in any doc, so this paragraph is the
  only mention and assumes the reader knows it.
- Rewrite: "A project's own config (`.strop/`) can name commands to run,
  such as a language server. strop runs them only after you allow that
  project with `:trust`. Scripts follow the same rule and use the same
  saved answers. A headless run does not load or save a session."
- **ask**: confirm what `:trust` covers, and add a short `:trust` section
  to editor.md.

### T9. NORMAL mode: stream byte

- Now: "Positions map by stream byte, so a cursor or mark stays on the same
  text when scrollback drops rows."
- Problem: "map by stream byte".
- Rewrite: "When old scrollback lines are dropped, your cursor and marks
  stay on the same text."

### T10. Shell paragraph

- Now: "The shell is `$SHELL` (or `/bin/sh`) in the current directory,
  running in the editor process. ... keeps the endpoint in its name; a host
  that is not connected refuses. **Open local terminal** / `:terminal-local`
  is a deliberate local choice, never a fallback against a remote-looking
  path. ... The displayed launch directory is the one selected at launch and
  does not follow `cd`."
- Problem: "running in the editor process" reads as wrong (the shell is its
  own process); "endpoint"; "fallback against a remote-looking path".
- Rewrite: "The shell is `$SHELL` (or `/bin/sh`), started in the project
  directory. In a file or directory on a connected SSH host, the terminal
  is your login shell on that host, and its name shows the host. If the
  host is not connected, strop says so and does not open a shell on your
  own machine by mistake. `:terminal-local` opens a shell on your machine
  on purpose. The directory in the terminal's name is where it started; it
  does not change when you `cd`."
- **ask**: "in the current directory": the project root, or the directory
  of the current file?

### T11. Bug report: terminal boundary

- Now: "Entering a private terminal boundary records an opaque marker and
  leaves the remaining capture metadata-only; replay refuses the omitted
  history."
- Problem: "private terminal boundary", "opaque marker".
- Rewrite: "What you type and see in a terminal is never recorded by
  `--log-content`. From the moment you first enter a terminal, the log
  keeps only event types, with no text, and can no longer be replayed. To
  record terminal content as well, add `--log-terminal-content`; the status
  line shows **REC** while it is on."

### T12. Bug report: replay sentences

- Now: "Use the recording version of strop for full replay: it requires a
  complete capture and does not repeat native side effects. The input-only
  script is different: it can run commands again and does not reproduce
  external service results."
- Problem: "native side effects", "external service results".
- Rewrite: "`strop replay` shows the session again without touching your
  files or running any command. Use the same strop version that made the
  log, and a log made with `--log-content`. `strop replay --script` is
  different. It gives you the keys as a script. Running that script really
  does run the commands again, and a language server may answer
  differently, so read it first."

### T13. Flag names disagree with cli.md

- Now: examples use "`strop --log-file issue.jsonl`"; cli.md lists only
  "`--log[=PATH]`". This page says "`--script SCRIPT` and `--headless
  SCRIPT` are equivalents"; cli.md lists `--script` only.
- Problem: a reader checking one page against the other finds flags that
  are not in the reference. (`--log-file`, `--headless` and `--script` all
  parse in `crates/strop/src/cli.rs`.)
- Rewrite: pick one spelling for the docs (`--log=PATH`, as `--help`
  prints) and use it in both files, or list the aliases in cli.md.

### T14. Lead

- Now: "Strop's terminal is Neovim's: a real PTY in a real buffer, one
  escape chord, and a NORMAL mode that is just NORMAL mode."
- Problem: a slogan; it does not say what you can do.
- Rewrite: "strop has a built-in terminal that works like Neovim's
  `:terminal`. Run a shell in a pane, leave it with `Ctrl-\ Ctrl-N`, and
  move, search and yank in its output with the usual keys."

### T15. Trace limits

- Now: "Metadata export retains only event categories and sequence numbers,
  not arbitrary payloads; the export is deliberately not replayable."
- Problem: "arbitrary payloads".
- Rewrite: "`strop export` keeps only what kind of event happened and in
  what order. It has no text, paths or keys, so it is safe to share, and it
  cannot be replayed."

---

## docs/remote.md

Refs: `origin/main`; the Git bullet is quoted from `origin/track/0.62-git`.

### R1. Lead

- Now: "Remote files are real buffers with their own identity, never a local
  lookalike."
- Problem: answers a design question the user did not ask.
- Rewrite: "Edit files on another machine over SSH. strop uses the `ssh`
  already on your machine. Nothing is installed on the host."

### R2. Authentication

- Now: "Authentication is noninteractive: host keys must already be trusted
  and a key or agent must answer without a prompt; otherwise the refusal
  carries ssh's own words and a hint."
- Problem: the user needs to know what to do first; "the refusal carries".
- Rewrite: "strop cannot ask you for a password or a passphrase, and
  cannot ask you to accept a new host key. Log in once with plain
  `ssh host` to accept the key, and use a key or an agent. If login fails,
  strop shows ssh's own error and a hint."

### R3. The connection

- Now: "strop runs one OpenSSH master per host (`ControlMaster`, socket in a
  private directory under `$XDG_RUNTIME_DIR`), so every later read, save,
  search or terminal is a channel on it rather than a new login. Masters
  strop started stop when it exits; after a crash they expire on their own
  after ten idle minutes."
- Problem: starts with the mechanism.
- Rewrite: "strop logs in once per host and reuses that connection for
  every read, save, search and terminal, so you are not asked to log in
  again. The connection closes when strop exits. After a crash it closes by
  itself after ten idle minutes. (It is an OpenSSH `ControlMaster`; its
  socket is in a private directory under `$XDG_RUNTIME_DIR`.)"

### R4. "The one consent"

- Now: "**A connected host is editable.** Logging in is the one consent:
  there is no separate step to edit files, run Git, search or open a
  terminal there."
- Problem: "consent" is the design word.
- Rewrite: "**Once connected, you can edit.** There is no second
  confirmation before you save files, search, use Git or open a terminal on
  the host."

### R5. Saving: background

- Now: "Saves run off the input thread; a reply for an older revision never
  clears newer unsaved edits."
- Problem: "input thread", "older revision".
- Rewrite: "You can keep typing while a save is on its way. If you edit
  during the save, the buffer stays marked as modified."

### R6. Directory listings

- Now: "Directory listings are searchable real buffers with kind, POSIX
  permissions, server-reported byte size and native filename columns. ...
  Listings include hidden entries and do not evaluate ignore files. ...
  remote candidates need a live connection or a cached listing. Percent-
  encode reserved path bytes (`%20`, `%23`, `%25`); native Unix filenames
  stay intact."
- Problem: "native filename columns", "evaluate ignore files", "remote
  candidates", "reserved path bytes".
- Rewrite: "A directory listing is an ordinary buffer: move and search in
  it as usual. Each row shows the kind, the permissions, the size and the
  name; `?` stands for something the host did not report. Hidden files are
  shown, and `.gitignore` is not applied. ... Tab completes host names and
  paths without logging in; paths on a host complete only once you are
  connected or have listed that directory before. In an `ssh://` address
  write a space as `%20`, `#` as `%23` and `%` as `%25`."

### R7. File management

- Now: "run on the host through the same Review → Apply → Receipt flow as
  locally ... nothing is ever replaced, directories are not copied
  recursively, and nothing is atomic across steps."
- Problem: same stage names as F2; "atomic".
- Rewrite: "work on the host as they do on your machine: a review first,
  then `Enter` to do it. On a host there is no trash (removal is for good),
  an existing file is never overwritten, a directory with files in it is
  not copied, and if a later step fails the earlier ones stay done."

### R8. Search, Git, language servers

- Now (`origin/track/0.62-git`): "**`Space /`** searches the remote
  workspace with `rg` on the host." / "**Git** signs, log (`Space g l`),
  blame and diffs run `git` there. Status, commit and the branch picker need
  a local repository"
- Problem: "remote workspace", "signs", "need a local repository" (sounds
  like something to install).
- Rewrite: "**`Space /`** searches the project on the host, using the
  host's `rg`." / "**Git**: the change marks in the gutter, the log
  (`Space g l`), blame and diffs use the host's `git`. Status, commit and
  the branch picker work only on your own machine for now."

### R9. Containers section

- Now: "## Containers" / "Strop does not attach to containers."
- Problem: a heading for something strop does not do; it reads as a
  leftover from when it did. The same tip is repeated in
  terminal-and-scripting.md ("For a container, run `docker exec -it
  <container> sh` in a terminal").
- Rewrite: drop the heading. Keep one line at the end of the terminal
  bullet: "To work inside a container, open a terminal and run `docker exec
  -it <container> sh`." Remove the copy in the terminal page.

### R10. Connecting: the chooser

- Now: "choose a known or connected destination" / "directories you choose
  are remembered privately"
- Problem: "destination"; "privately" does not say where.
- Rewrite: "pick a host you have used before" / "strop remembers, on this
  machine only, the directories you opened on each host".
- **ask**: confirm where that list is stored and that `:remote clear`
  empties it. `:remote clear` and `:filter app` are in the code block with
  no explanation.

### R11. Saving: limits

- Now: "Limits, stated plainly: there is no cross-process lock (as in vim, a
  writer racing the final check wins)"
- Problem: "cross-process lock", "racing the final check".
- Rewrite: "What strop cannot protect against: if another program writes
  the file in the instant between strop's last check and its save, the
  later write wins, as in Vim."

---

## docs/cli.md

Ref: `origin/main` (the same on every ref).

### C1. Command table wording

- Now: "run the scripted driver over a file" / "replay a session trace
  (`--script` extracts a driver script)" / "export a trace's metadata
  (privacy-safe, not replayable)" / "run the performance-gate scenarios" /
  "dump the vim-compatibility table"
- Problem: "driver", "trace", "performance-gate" are project terms.
- Rewrite: "run a script of keys against a file, with no screen" / "show a
  recorded session again (`--script` prints its keys as a script)" / "strip
  a recording down to event types, safe to share" / "run the built-in speed
  tests" / "print the list of Vim keys strop supports".
- These strings come from `--help` in `crates/strop/src/main.rs`; change
  them there too.

### C2. Options table

- Now: "`--theme NAME` | session-start palette" / "`--script PATH` |
  headless driver script (same as `headless`)" / "`--log[=PATH]` | record a
  session trace"
- Problem: "session-start palette", "headless driver script".
- Rewrite: "colour theme for this run" / "same as `strop headless PATH`" /
  "record this session to a file, for a bug report".

### C3. Remote pointer

- Now: "A connected host is editable; `-R` opens read-only. ... The full
  remote contract lives in [remote.md](remote.md)."
- Problem: "contract".
- Rewrite: "Once connected you can edit and save; `-R` opens read-only.
  Details are in [remote.md](remote.md)."

### C4. Lead

- Now: "One binary, subcommands for the occasional jobs, flags for
  everything else."
- Problem: mild; it describes the shape, not the use.
- Rewrite: "`strop FILE` opens a file. This page lists the other commands
  and the options."

---

## docs/git.md (new in 0.62)

Ref: `origin/track/0.62-git`. This page is already plain. I checked it
against the 0.62 changelog (`Space g S` gone, blame moved to `Space g B`,
`Space g u` unstages): the page and the 0.62 remote.md agree with it. No
stale statement found.

### G1. "Surface"

- Now: "Each surface is an ordinary read-only buffer"
- Problem: "surface".
- Rewrite: "Each git view is an ordinary read-only buffer".

### G2. "Follows the tree"

- Now: "The buffer follows the tree: it refreshes after every stage, ..."
- Problem: "the tree" is git's word for the working directory.
- Rewrite: "The list keeps itself up to date: it refreshes after every
  stage, ..."

### G3. Blame card

- Now: "blame gutter (a card for one line when the gutter can not show)"
- Problem: does not say when the gutter cannot show.
- **ask: what does the user see?** Guess: "who last changed each line, in
  the gutter; in a window too narrow for the gutter, a card for the current
  line".

### G4. SSH projects

- Now: "Signs, log, blame, history and diffs work on a remote project ...
  Status, commit and the branch picker need a local repository for now; on a
  remote project they say so and do nothing."
- Problem: "signs"; "need a local repository" sounds like a requirement to
  meet.
- Rewrite: "On an SSH host the gutter marks, log, blame, history and diffs
  work. Status, commit and the branch picker do not work there yet; they
  say so and do nothing."

### G5. Lock files

- Now: "The lock files strop keeps beside open files are never listed."
- Problem: first mention of lock files in the user docs (see F11).
- Rewrite: keep, and link to the sentence that explains them once F11 is
  written.

---

## docs/vim-compat.md (generated)

The page is generated from the keymap table, so fix the row descriptions in
the source (for example `crates/strop-engine/src/keymap/bindings/ex.rs`)
and regenerate.

### V1. Stale rows

- Now (`origin/track/0.62-git`): "`:tab-size :indent-style
  :search-options` — source indentation and search visibility controls" and
  "`:apply-change :cancel-change :save-change` — review: apply text or
  filesystem changes, cancel, or save changed text"
- Problem: `:search-options` is removed in 0.60 (that branch's table has
  already dropped it); the `-change` commands are removed in 0.61 (that
  branch's table has dropped the row). 0.62 has both rows back because of
  its older base.
- Rewrite: "`:tab-size :indent-style` — indent width and tabs or spaces
  for this file". Delete the `-change` row. Check both after the merge.

### V2. "namespace-aware"

- Now: "`:fs :browse :filter` — filesystem actions, namespace-aware browsing
  and folder filtering"
- Problem: "namespace-aware".
- Rewrite: "create, rename, move and delete files; browse a directory
  (local or `ssh://`); filter its listing".

### V3. "source", "surface", "dive"

- Now: "collection: open full source at caret" / "reveal source in its
  Directory buffer" / "Search Find: open source; With: prepare review" /
  "close surface (readonly buffers)" / "dive into the line's commit (blame
  gutter)"
- Problem: "source" for a file, "surface", "dive".
- Rewrite: "collection: open the file at this line" / "show the current
  file in its directory" / "Search: open the result; in With: open the
  review" / "close this view" / "open the commit that last changed this
  line (blame)".

### V4. Header line

- Now: "`✓` ships exactly; `(soon)` is a planned slot."
- Problem: "ships exactly", "planned slot".
- Rewrite: "`✓` works as in Vim; `(soon)` is planned."

### V5. `:recover`

- Now: "`:recover` — draft recovery: list, restore N, discard N, consent
  remote|off"
- Problem: "consent remote|off" cannot be understood from the row, and
  draft recovery is not described in any doc page.
- **ask: what does the user see?** Then add a short "Recovering unsaved
  work" section to editor.md and shorten the row to "recover unsaved text
  after a crash: list, restore N, discard N".

---

## docs/nucleo-decision.md

### N1. A design record among the user docs

- Now: "# Nucleo decision record (0022 §2)" / "Date: 2026-09-06. Decision:
  **adopt nucleo-matcher** for the picker's row scoring."
- Problem: it is a benchmark and a library choice for contributors. The
  site publishes it as `docs/nucleo-decision.html`, next to the user pages.
  The title cites a plan section.
- Rewrite: move the file to `plans/` (for example
  `plans/0022-nucleo-decision.md`, or fold it into plan 0022) and delete the
  rendered page from the site. Nothing in it needs rewording for users; it
  should not be a user page.
