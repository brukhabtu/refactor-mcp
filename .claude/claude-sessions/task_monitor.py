#!/usr/bin/env python3

import json
import time
import os
import sys
from pathlib import Path

def monitor_session(name: str, pid: int, output_file: str, mode: str) -> None:
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
                response = json.load(f)
            
            # Add metadata and type to response
            response["type"] = "result"
            response["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            response["project_dir"] = os.getcwd()
            
            # Read current task
            task_file = Path(f".claude/claude-sessions/tasks/{name}.json")
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
        print("Usage: session_monitor.py <name> <pid> <output_file> <mode>")
        sys.exit(1)
    
    name, pid_str, output_file, mode = sys.argv[1:5]
    monitor_session(name, int(pid_str), output_file, mode)