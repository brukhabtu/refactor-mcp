#!/usr/bin/env python3

import json
import time
import os
import sys
from pathlib import Path

def monitor_session(name: str, pid: int, output_file: str, original_cwd: str) -> None:
    """Monitor a Claude session and append response when complete"""
    
    # Wait for PID to finish
    while True:
        try:
            os.kill(pid, 0)
            time.sleep(0.5)
        except ProcessLookupError:
            break
    
    # Read the Claude output
    output_path = Path(output_file)
    if output_path.exists():
        try:
            with open(output_path, "r") as f:
                content = f.read().strip()
                if not content:
                    print("Error processing session output: Empty output file", file=sys.stderr)
                    return
                
                # Handle non-JSON Claude output (errors, etc.)
                try:
                    response = json.loads(content)
                except json.JSONDecodeError:
                    # Create error response for non-JSON output
                    response = {
                        "error": content,
                        "result": f"Claude command failed: {content}"
                    }
            
            # Add metadata and type to response
            response["type"] = "result"
            response["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            response["project_dir"] = os.getcwd()
            
            # Use absolute path to task file based on original working directory
            task_file = Path(original_cwd) / ".claude/claude-sessions/tasks" / f"{name}.json"
            if task_file.exists():
                with open(task_file, "r") as f:
                    task_data = json.load(f)
                
                # Append response message
                task_data['messages'].append(response)
                
                # Write back to task file
                with open(task_file, "w") as f:
                    json.dump(task_data, f, indent=2)
            
            # Clean up temp output file
            output_path.unlink()
            
        except Exception as e:
            print(f"Error processing session output: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: task_monitor.py <name> <pid> <output_file> <original_cwd>")
        sys.exit(1)
    
    name, pid_str, output_file, original_cwd = sys.argv[1:5]
    monitor_session(name, int(pid_str), output_file, original_cwd)