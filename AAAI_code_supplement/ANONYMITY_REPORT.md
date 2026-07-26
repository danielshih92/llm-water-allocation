# Anonymity Verification Report

Verification time: 2026-07-26T13:37:14Z

Scope: every file and directory in this supplement.

Checks completed:

- identity, contact, affiliation, and repository-provenance patterns;
- user-specific absolute paths and repository-host links;
- secret tokens, private-key material, and literal credential assignments;
- recursive inspection of all JSON, JSONL, and CSV string fields;
- byte-level pattern inspection of every file;
- forbidden private data, reasoning records, response previews, caches, hidden
  files, repository metadata, and license artifacts;
- symbolic links and generated binary/cache artifacts;
- exact matching against identity and provenance values present in the private
  working repository.

Result: zero unapproved identifying or secret-bearing findings.

Scientific identifiers intentionally retained are model names, SDK/provider
names, and API endpoints needed to reproduce the experiments. Alex, Bob,
Cindy, David, and Eric are fictional benchmark role labels.
