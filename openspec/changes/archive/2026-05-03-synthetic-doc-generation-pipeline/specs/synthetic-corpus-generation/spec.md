## ADDED Requirements

### Requirement: Corpus source

- The system SHALL read document content exclusively from `MinHash/data/articles_100.train`.
- Each non-empty line in the training file SHALL produce exactly one output document.
- The system SHALL parse the leading whitespace-separated token as the document identifier and the remainder as the article body.

#### Scenario: Parse training row
- GIVEN a line `t980 A man was shot dead…`
- WHEN the line is parsed
- THEN `doc_id` = `t980` and `text` = `A man was shot dead…`

### Requirement: Output volume

- The system SHALL produce exactly 100 output files for the 100-row training file — one file per row, no duplicates.

#### Scenario: One file per row
- GIVEN 100 non-empty lines in the training file
- WHEN the script completes
- THEN exactly 100 files exist in `data/input/`

### Requirement: Format distribution

- The system SHALL assign output formats by cycling `.docx → .pdf → .md` across rows in order.
- No single format SHALL exceed 34 files for a 100-row input.

#### Scenario: Format cycle
- GIVEN rows indexed 1–100
- WHEN formats are assigned
- THEN rows 1, 4, 7, … → `.docx`; rows 2, 5, 8, … → `.pdf`; rows 3, 6, 9, … → `.md`

### Requirement: Content-derived filenames

- Each output filename SHALL be derived from the first three distinctive (non-stopword, ≥ 3-char alphabetic) words in the article body, suffixed with the doc-id.
- Filenames SHALL be lowercase and underscore-separated (e.g., `man_shot_dead_t980.docx`).
- The system SHALL guarantee filename uniqueness within the output directory by appending `_2`, `_3`, etc. on collision.

#### Scenario: Unique slug generation
- GIVEN two articles both beginning with `man shot dead`
- WHEN slugs are generated
- THEN the first gets `man_shot_dead_<doc_id>` and the second gets `man_shot_dead_<doc_id_2>`

### Requirement: Document structure

- Every `.docx` file SHALL contain an H1 heading (first sentence ≤ 80 chars) followed by the wrapped article body.
- Every `.pdf` file SHALL contain a Title-styled heading followed by BodyText-styled paragraphs.
- Every `.md` file SHALL begin with a `# ` level-1 heading followed by the article body as plain text.

#### Scenario: docx structure
- GIVEN a row assigned `.docx` format
- WHEN the file is generated
- THEN the document contains an H1 heading matching the first sentence and body paragraphs below it

#### Scenario: md structure
- GIVEN a row assigned `.md` format
- WHEN the file is generated
- THEN the file begins with `# <title>` followed by a blank line and the article body

### Requirement: Logging

- The system SHALL emit one structured JSON log entry per file written.
- The system SHALL emit a completion summary log entry recording total files written and output directory.
- Log output SHALL be written to a timestamped file (`generate_docs_<YYYYMMDD_HHMMSS>.log`) in the script directory.

#### Scenario: Per-file log entry
- GIVEN the script writes `man_shot_dead_t980.docx`
- WHEN the write completes
- THEN a JSON log entry with `event=docx_written` and `path=<full path>` is appended to the log file

### Requirement: Idempotency

- Re-running the script SHALL overwrite existing output files without error.
- The system SHALL NOT accumulate duplicate files on repeated runs.

#### Scenario: Re-run produces same file count
- GIVEN 100 files already exist in `data/input/`
- WHEN the script is run a second time
- THEN `data/input/` still contains exactly 100 files with no duplicates
