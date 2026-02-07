#!/usr/bin/env python3
"""
Merge multiple session transcripts into one unified session.
Cross-platform support for Windows, macOS, and Linux.
"""

import json
import sys
import os
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple


def parse_timestamp(ts: str) -> datetime:
    if not ts:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        ts = ts.replace('Z', '+00:00')
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def find_session_files(logs_dir: Path) -> Tuple[List[Path], List[Path]]:
    processed_files = []
    raw_files = []

    for f in logs_dir.glob("session_*.jsonl"):
        if "_raw.jsonl" in f.name:
            raw_files.append(f)
        else:
            processed_files.append(f)

    def get_start_time(filepath: Path) -> datetime:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    event = json.loads(line.strip())
                    if event.get('type') == 'session_start':
                        return parse_timestamp(event.get('timestamp', ''))
        except Exception:
            pass
        return datetime.min.replace(tzinfo=timezone.utc)

    processed_files.sort(key=get_start_time)

    processed_ids = [f.stem.replace('session_', '') for f in processed_files]
    raw_files_sorted = []
    for sid in processed_ids:
        raw_path = logs_dir / f"session_{sid}_raw.jsonl"
        if raw_path.exists():
            raw_files_sorted.append(raw_path)

    return processed_files, raw_files_sorted


def read_session_events(filepath: Path) -> List[Dict]:
    events = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Warning: Error reading {filepath}: {e}", file=sys.stderr)
    return events


def extract_session_data(events: List[Dict]) -> Dict:
    data = {
        'session_start': None,
        'session_end': None,
        'session_summary': None,
        'messages': [],
        'other_events': []
    }

    for event in events:
        event_type = event.get('type')
        if event_type == 'session_start':
            data['session_start'] = event
        elif event_type == 'session_end':
            data['session_end'] = event
        elif event_type == 'session_summary':
            data['session_summary'] = event
        elif event_type in ('user', 'assistant', 'assistant_thinking'):
            data['messages'].append(event)
        else:
            data['other_events'].append(event)

    return data


def aggregate_summaries(summaries: List[Dict]) -> Dict:
    totals = {
        'total_duration_seconds': 0,
        'total_messages': 0,
        'assistant_messages': 0,
        'user_prompts': 0,
        'usage_totals': {
            'total_input_tokens': 0,
            'total_output_tokens': 0
        }
    }

    for summary in summaries:
        sd = summary.get('summary_data', {})
        totals['total_duration_seconds'] += sd.get('total_duration_seconds', 0)
        totals['total_messages'] += sd.get('total_messages', 0)
        totals['assistant_messages'] += sd.get('assistant_messages', 0)
        totals['user_prompts'] += sd.get('user_prompts', 0)

        ut = sd.get('usage_totals', {})
        totals['usage_totals']['total_input_tokens'] += ut.get('total_input_tokens', 0)
        totals['usage_totals']['total_output_tokens'] += ut.get('total_output_tokens', 0)

    return totals


def merge_sessions(logs_dir: Path) -> bool:
    processed_files, raw_files = find_session_files(logs_dir)

    if len(processed_files) < 2:
        print(f"Found {len(processed_files)} session file(s). No merge needed.")
        return False

    all_session_data = []
    for pf in processed_files:
        events = read_session_events(pf)
        session_data = extract_session_data(events)
        all_session_data.append(session_data)

    merged_session_id = str(uuid.uuid4())
    output_prefix = f"session_{merged_session_id}"

    all_messages = []
    for sd in all_session_data:
        for msg in sd['messages']:
            msg_copy = msg.copy()
            msg_copy['session_id'] = merged_session_id
            all_messages.append(msg_copy)

    all_messages.sort(key=lambda m: parse_timestamp(m.get('timestamp', '')))

    all_summaries = [sd['session_summary'] for sd in all_session_data if sd.get('session_summary')]
    aggregated_data = aggregate_summaries(all_summaries)

    merged_start = {
        'type': 'session_start',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'session_id': merged_session_id
    }

    merged_summary = {
        'type': 'session_summary',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'session_id': merged_session_id,
        'summary_data': aggregated_data
    }

    merged_end = {
        'type': 'session_end',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'session_id': merged_session_id
    }

    output_processed = logs_dir / f"{output_prefix}.jsonl"
    with open(output_processed, 'w', encoding='utf-8') as f:
        f.write(json.dumps(merged_start) + '\n')
        for msg in all_messages:
            f.write(json.dumps(msg) + '\n')
        f.write(json.dumps(merged_summary) + '\n')
        f.write(json.dumps(merged_end) + '\n')

    print(f"✅ Created merged session file: {output_processed.name}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python merge_sessions.py <path>")
        sys.exit(1)

    target_dir = Path(sys.argv[1]).resolve()
    if not target_dir.exists():
        print("Directory not found.")
        sys.exit(1)

    merge_sessions(target_dir)


if __name__ == "__main__":
    main()

