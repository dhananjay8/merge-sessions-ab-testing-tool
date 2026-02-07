# Merge Sessions A/B Testing Tool

## Overview
This project provides a Python-based utility for merging multiple experiment session transcripts into a single unified session. It is designed for A/B testing workflows where multiple sessions may be generated during experimentation.

## Key Features
- Automatic detection of session JSONL files
- Chronological merging of multiple sessions
- Preservation of metadata (session IDs, timestamps, model lanes)
- Aggregation of metrics such as token usage, message counts, and tool calls
- Cross-platform compatibility (Windows, macOS, Linux)

## Usage

### Merge sessions from an experiment root directory
```bash
python merge_sessions.py .
