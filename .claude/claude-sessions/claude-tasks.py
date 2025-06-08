#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

CLAUDE_TASKS_DIR = Path(".claude/claude-sessions")  # Keep dir name for now to avoid breaking
TASKS_DIR = CLAUDE_TASKS_DIR / "tasks"

# Safe default tools - allows most operations but restricts dangerous ones
DEFAULT_ALLOWED_TOOLS = "Read Edit MultiEdit Write Glob Grep LS Task Bash(git:status,git:diff,git:log,git:show,git:branch,git:checkout,git:add,git:commit,git:stash,npm:*,python:*,uv:*,pip:*,cargo:*,go:*) TodoRead TodoWrite"

@dataclass
class TaskInfo:
    name: str
    status: str
    session_id: Optional[str]
    requests: int
    responses: int

@dataclass
class TaskList:
    tasks: List[TaskInfo]

@dataclass
class TaskStatus:
    status: str
    task: str
    pid: int

@dataclass
class ErrorResponse:
    error: str

class TaskManager:
    def __init__(self):
        self.init_tasks()
    
    def init_tasks(self):
        """Initialize tasks directory"""
        TASKS_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_task_file(self, name: str) -> Path:
        """Get task file path"""
        return TASKS_DIR / f"{name}.json"
    
    def read_task(self, name: str) -> Optional[Dict[str, Any]]:
        """Read a task file"""
        task_file = self.get_task_file(name)
        try:
            with open(task_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def write_task(self, name: str, task_data: Dict[str, Any]) -> bool:
        """Write task data to file"""
        task_file = self.get_task_file(name)
        try:
            with open(task_file, 'w') as f:
                json.dump(task_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to write task file: {e}", file=sys.stderr)
            return False
    
    def task_exists(self, name: str) -> bool:
        """Check if task exists"""
        return self.get_task_file(name).exists()
    
    def append_message(self, name: str, message: Dict[str, Any]) -> bool:
        """Append a message (request or response) to the task"""
        task_data = self.read_task(name)
        if not task_data:
            return False
        
        task_data['messages'].append(message)
        return self.write_task(name, task_data)
    
    def get_last_session_id(self, name: str) -> Optional[str]:
        """Get session_id from the last result message"""
        task_data = self.read_task(name)
        if not task_data:
            return None
        
        # Find last result message with session_id
        for message in reversed(task_data['messages']):
            if message.get('type') == 'result' and message.get('session_id'):
                return message['session_id']
        return None
    
    def start_task(self, name: str, message: str, project_dir: Optional[str] = None) -> int:
        """Start a new background Claude task"""
        if project_dir is None:
            project_dir = os.getcwd()
        
        # Check if task already exists
        if self.task_exists(name):
            print(f"Task '{name}' already exists")
            return 1
        
        # Create task file immediately
        task_data: Dict[str, Any] = {
            'messages': []
        }
        
        if not self.write_task(name, task_data):
            print(f"Failed to create task file for '{name}'")
            return 1
        
        # Add request message to task
        request_message: Dict[str, Any] = {
            'type': 'request',
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'project_dir': project_dir
        }
        
        if not self.append_message(name, request_message):
            print(f"Failed to add request message to task '{name}'")
            return 1
        
        # Start Claude in background
        output_file = TASKS_DIR / f"{name}_temp_output.json"
        
        try:
            os.chdir(project_dir)
            with open(output_file, 'w') as f:
                process = subprocess.Popen([
                    'claude', '-p', '--output-format', 'json', 
                    '--allowedTools', DEFAULT_ALLOWED_TOOLS,
                    message
                ], stdout=f, stderr=subprocess.STDOUT)
            
            # Start background monitor (detached)
            self._monitor_task(name, process.pid, output_file)
            
            print(json.dumps(asdict(TaskStatus("started", name, process.pid))))
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
        
        return 0
    
    def _monitor_task(self, name: str, pid: int, output_file: Path) -> None:
        """Monitor task completion in background"""
        monitor_script = CLAUDE_TASKS_DIR / "task_monitor.py"
        subprocess.Popen([
            sys.executable, 
            str(monitor_script),
            name,
            str(pid),
            str(output_file),
            "append"  # Signal to append to task file
        ], start_new_session=True)
    
    def continue_task(self, name: str, message: str) -> int:
        """Continue an existing Claude task"""
        task_data = self.read_task(name)
        if not task_data:
            print(f"Task '{name}' not found")
            return 1
        
        session_id = self.get_last_session_id(name)
        if not session_id:
            print(f"Task '{name}' has no session ID set. Cannot continue.")
            return 1
        
        # Get project dir from first message if available
        project_dir = os.getcwd()
        if task_data['messages']:
            for msg in task_data['messages']:
                if msg.get('project_dir'):
                    project_dir = msg['project_dir']
                    break
        
        # Add request message to task
        request_message: Dict[str, Any] = {
            'type': 'request',
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'project_dir': project_dir
        }
        
        if not self.append_message(name, request_message):
            print(f"Failed to add request message to task '{name}'")
            return 1
        
        # Start Claude resume in background
        timestamp = int(time.time())
        output_file = TASKS_DIR / f"{name}_temp_resume_{timestamp}.json"
        
        try:
            os.chdir(project_dir)
            with open(output_file, 'w') as f:
                process = subprocess.Popen([
                    'claude', '-p', '-r', session_id, '--output-format', 'json',
                    '--allowedTools', DEFAULT_ALLOWED_TOOLS,
                    message
                ], stdout=f, stderr=subprocess.STDOUT)
            
            # Start background monitor
            self._monitor_task(name, process.pid, output_file)
            
            print(json.dumps(asdict(TaskStatus("continued", name, process.pid))))
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
        
        return 0
    
    def list_tasks(self) -> None:
        """List all tasks by scanning directory"""
        task_files = list(TASKS_DIR.glob("*.json"))
        tasks = []
        
        for task_file in task_files:
            if task_file.name.startswith('_'):  # Skip temp files
                continue
                
            name = task_file.stem
            task_data = self.read_task(name)
            
            if not task_data:
                continue
                
            messages = task_data.get('messages', [])
            session_id = self.get_last_session_id(name)
            
            # Count message types
            request_count = sum(1 for msg in messages if msg.get('type') == 'request')
            response_count = sum(1 for msg in messages if msg.get('type') == 'result')
            
            tasks.append(TaskInfo(
                name=name,
                status="active" if session_id else "starting",
                session_id=session_id,
                requests=request_count,
                responses=response_count
            ))
        
        print(json.dumps(asdict(TaskList(tasks))))
    
    def show_task(self, name: str) -> int:
        """Show detailed task info"""
        task_data = self.read_task(name)
        if not task_data:
            print(f"Task '{name}' not found")
            return 1
        
        print(json.dumps(task_data))
        return 0
    
    def conversation_task(self, name: str) -> int:
        """Show clean conversation without metadata"""
        task_data = self.read_task(name)
        if not task_data:
            print(f"Task '{name}' not found")
            return 1
        
        messages = task_data.get('messages', [])
        if not messages:
            print(f"No messages yet for task '{name}'")
            return 0
        
        print(f"=== {name} ===")
        for message in messages:
            if message.get('type') == 'request':
                print(f"\n> {message.get('message', 'No message found')}")
            elif message.get('type') == 'result':
                print(f"\n{message.get('result', message.get('error', 'No result found'))}")
        
        return 0

    def output_task(self, name: str) -> int:
        """Show task conversation with metadata"""
        task_data = self.read_task(name)
        if not task_data:
            print(f"Task '{name}' not found")
            return 1
        
        messages = task_data.get('messages', [])
        if not messages:
            print(f"No messages yet for task '{name}'")
            return 0
        
        print(f"=== Task '{name}' Conversation ===")
        for i, message in enumerate(messages, 1):
            if message.get('type') == 'request':
                print(f"\n--- Request {i} ---")
                print(f"User: {message.get('message', 'No message found')}")
            elif message.get('type') == 'result':
                print(f"\n--- Response {i} ---")
                print(f"Claude: {message.get('result', message.get('error', 'No result found'))}")
        
        print(f"\n=== Full Task Data ===")
        print(json.dumps(task_data, indent=2))
        return 0
    
    def remove_task(self, name: str) -> int:
        """Remove a task"""
        task_file = self.get_task_file(name)
        try:
            task_file.unlink()
            print(f"Removed task '{name}'")
        except FileNotFoundError:
            print(f"Task '{name}' not found")
        return 0

def main() -> int:
    if len(sys.argv) < 2:
        print("Claude Task Manager")
        print()
        print("Usage: claude-tasks <command> [args]")
        print()
        print("Commands:")
        print("  start <name> <message> [dir]  Start a new Claude background task")
        print("  continue <name> <message>     Continue an existing Claude task")
        print("  list                          List all Claude tasks")
        print("  conversation <name>           Show clean task conversation")
        print("  show <name>                   Show detailed Claude task info")
        print("  output <name>                 Show Claude task output with metadata")
        print("  remove <name>                 Remove a Claude task from tracking")
        print()
        print("Examples:")
        print('  claude-tasks start backend "Fix the login bug" /path/to/backend')
        print('  claude-tasks continue backend "Continue fixing the login bug"')
        print("  claude-tasks conversation backend")
        print("  claude-tasks list")
        return 0
    
    manager = TaskManager()
    command = sys.argv[1]
    
    if command == 'start':
        if len(sys.argv) < 4:
            print("Usage: claude-tasks start <name> <message> [dir]")
            return 1
        name, message = sys.argv[2], sys.argv[3]
        project_dir = sys.argv[4] if len(sys.argv) > 4 else None
        return manager.start_task(name, message, project_dir)
    
    elif command in ['continue', 'resume']:
        if len(sys.argv) < 4:
            print("Usage: claude-tasks continue <name> <message>")
            return 1
        name, message = sys.argv[2], sys.argv[3]
        return manager.continue_task(name, message)
    
    elif command in ['list', 'ls']:
        manager.list_tasks()
        return 0
    
    elif command in ['conversation', 'chat']:
        if len(sys.argv) < 3:
            print("Usage: claude-tasks conversation <name>")
            return 1
        return manager.conversation_task(sys.argv[2])
    
    elif command == 'show':
        if len(sys.argv) < 3:
            print("Usage: claude-tasks show <name>")
            return 1
        return manager.show_task(sys.argv[2])
    
    elif command == 'output':
        if len(sys.argv) < 3:
            print("Usage: claude-tasks output <name>")
            return 1
        return manager.output_task(sys.argv[2])
    
    elif command in ['remove', 'rm']:
        if len(sys.argv) < 3:
            print("Usage: claude-tasks remove <name>")
            return 1
        return manager.remove_task(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == '__main__':
    sys.exit(main())