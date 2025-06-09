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

# Default tools for background tasks - provide essential tools for development work
DEFAULT_ALLOWED_TOOLS = "Task,Bash,Glob,Grep,LS,Read,Edit,MultiEdit,Write,NotebookRead,NotebookEdit,TodoRead,TodoWrite"

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
    
    def start_task(self, name: str, message: str, project_dir: Optional[str] = None, use_worktree: bool = False) -> int:
        """Start a new background Claude task"""
        if project_dir is None:
            project_dir = os.getcwd()
        
        # Create worktree if requested
        if use_worktree:
            worktree_path = self._create_worktree(name, project_dir)
            if not worktree_path:
                return 1
            project_dir = worktree_path
        
        # Check if task already exists
        if self.task_exists(name):
            print(f"Task '{name}' already exists")
            return 1
        
        # Create task file immediately  
        task_data: Dict[str, Any] = {
            'messages': [],
            'use_worktree': use_worktree,
            'worktree_path': project_dir if use_worktree else None
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
            # Store current directory for monitor script
            original_cwd = os.getcwd()
            
            cmd = ['claude', '-p', message, '--output-format', 'json']
            if DEFAULT_ALLOWED_TOOLS:
                cmd.extend(['--allowedTools', DEFAULT_ALLOWED_TOOLS])
            
            # Debug: write command to file for troubleshooting
            debug_file = TASKS_DIR / f"{name}_debug_cmd.txt"
            with open(debug_file, 'w') as df:
                df.write(f"Command: {' '.join(cmd)}\n")
            
            # Start Claude process in background (fully detached)
            # Use nohup-style approach to ensure complete detachment
            with open(output_file, 'w') as f, open(os.devnull, 'r') as devnull:
                process = subprocess.Popen(
                    cmd, 
                    stdout=f, 
                    stderr=subprocess.STDOUT,
                    stdin=devnull,
                    cwd=project_dir,  # Set working directory without changing current process
                    start_new_session=True,  # Detach from parent session
                )
            
            # Start background monitor (detached) - pass original directory
            self._monitor_task(name, process.pid, output_file, original_cwd)
            
            print(json.dumps(asdict(TaskStatus("started", name, process.pid))))
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
        
        return 0
    
    def _create_worktree(self, name: str, project_dir: str) -> Optional[str]:
        """Create a git worktree for isolated task execution"""
        worktree_dir = Path(project_dir) / ".claude" / "worktrees" / name
        branch_name = f"task-{name}-{int(time.time())}"
        
        try:
            # Ensure worktrees directory exists
            worktree_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove existing worktree if it exists
            if worktree_dir.exists():
                subprocess.run(['git', 'worktree', 'remove', '--force', str(worktree_dir)], 
                             cwd=project_dir, capture_output=True)
            
            # Create new branch and worktree
            result = subprocess.run([
                'git', 'worktree', 'add', '-b', branch_name, str(worktree_dir), 'HEAD'
            ], cwd=project_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Failed to create worktree: {result.stderr}")
                return None
                
            print(f"Created worktree for task '{name}' at {worktree_dir} on branch {branch_name}")
            return str(worktree_dir)
            
        except Exception as e:
            print(f"Error creating worktree: {e}")
            return None
    
    def _monitor_task(self, name: str, pid: int, output_file: Path, original_cwd: str) -> None:
        """Monitor task completion in background"""
        monitor_script = CLAUDE_TASKS_DIR / "task_monitor.py"
        with open(os.devnull, 'r') as devnull:
            subprocess.Popen([
                sys.executable, 
                str(monitor_script),
                name,
                str(pid),
                str(output_file),
                original_cwd  # Pass original working directory
            ], 
            stdin=devnull,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            )
    
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
            # Store current directory for monitor script
            original_cwd = os.getcwd()
            
            cmd = ['claude', '-p', message, '-r', session_id, '--output-format', 'json']
            if DEFAULT_ALLOWED_TOOLS:
                cmd.extend(['--allowedTools', DEFAULT_ALLOWED_TOOLS])
            
            # Debug: write command to file for troubleshooting
            debug_file = TASKS_DIR / f"{name}_debug_resume_cmd.txt"
            with open(debug_file, 'w') as df:
                df.write(f"Command: {' '.join(cmd)}\n")
            
            # Start Claude process in background (fully detached)
            # Use nohup-style approach to ensure complete detachment
            with open(output_file, 'w') as f, open(os.devnull, 'r') as devnull:
                process = subprocess.Popen(
                    cmd, 
                    stdout=f, 
                    stderr=subprocess.STDOUT,
                    stdin=devnull,
                    cwd=project_dir,  # Set working directory without changing current process
                    start_new_session=True,  # Detach from parent session
                )
            
            # Start background monitor
            self._monitor_task(name, process.pid, output_file, original_cwd)
            
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
            if task_file.name.startswith('_') or '_temp_' in task_file.name or '_debug_' in task_file.name:  # Skip temp/debug files
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
            
            # Determine status based on request/response balance and recent activity
            if response_count == 0:
                status = "starting"
            elif request_count == response_count:
                # Check if last message was recent (within 2 minutes)
                last_msg = messages[-1] if messages else {}
                last_time = last_msg.get('timestamp', '')
                try:
                    from datetime import datetime, timedelta
                    if last_time:
                        last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                        if datetime.now().astimezone() - last_dt < timedelta(minutes=2):
                            status = "completed"
                        else:
                            status = "idle"
                    else:
                        status = "completed"
                except:
                    status = "completed"
            else:
                status = "active"

            
            tasks.append(TaskInfo(
                name=name,
                status=status,
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
    
    def status_task(self, name: str) -> int:
        """Show task status and completion information"""
        task_data = self.read_task(name)
        if not task_data:
            print(f"Task '{name}' not found")
            return 1
        
        messages = task_data.get('messages', [])
        session_id = self.get_last_session_id(name)
        use_worktree = task_data.get('use_worktree', False)
        worktree_path = task_data.get('worktree_path')
        
        request_count = sum(1 for msg in messages if msg.get('type') == 'request')
        response_count = sum(1 for msg in messages if msg.get('type') == 'result')
        
        # Determine completion status
        if response_count == 0:
            status = "🔄 Starting"
        elif request_count == response_count:
            last_msg = messages[-1] if messages else {}
            last_result = last_msg.get('result', '')
            if 'complete' in last_result.lower() or 'success' in last_result.lower():
                status = "✅ Completed"
            else:
                status = "✅ Ready"
        else:
            status = "⏳ Working"
        
        print(f"=== Task '{name}' Status ===")
        print(f"Status: {status}")
        print(f"Requests: {request_count}")
        print(f"Responses: {response_count}")
        print(f"Session ID: {session_id or 'None'}")
        print(f"Uses Worktree: {'Yes' if use_worktree else 'No'}")
        if worktree_path:
            print(f"Worktree Path: {worktree_path}")
        
        if messages:
            last_msg = messages[-1]
            print(f"Last Activity: {last_msg.get('timestamp', 'Unknown')}")
            if last_msg.get('type') == 'result':
                result = last_msg.get('result', '')
                if len(result) > 200:
                    print(f"Last Result: {result[:200]}...")
                else:
                    print(f"Last Result: {result}")
        
        # Check if worktree has changes
        if use_worktree and worktree_path and Path(worktree_path).exists():
            try:
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                      cwd=worktree_path, capture_output=True, text=True)
                if result.stdout.strip():
                    print("📝 Worktree has uncommitted changes")
                    changes = result.stdout.strip().split('\n')[:5]  # Show first 5 changes
                    for change in changes:
                        print(f"   {change}")
                    if len(result.stdout.strip().split('\n')) > 5:
                        print(f"   ... and {len(result.stdout.strip().split('\n')) - 5} more")
                else:
                    print("📄 Worktree is clean")
            except:
                print("❓ Could not check worktree status")
        
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
        """Remove a task and clean up worktree if needed"""
        # Read task data to check for worktree
        task_data = self.read_task(name)
        if task_data and task_data.get('use_worktree') and task_data.get('worktree_path'):
            self._cleanup_worktree(task_data['worktree_path'])
        
        task_file = self.get_task_file(name)
        try:
            task_file.unlink()
            print(f"Removed task '{name}'")
        except FileNotFoundError:
            print(f"Task '{name}' not found")
        return 0
    
    def _cleanup_worktree(self, worktree_path: str) -> None:
        """Clean up a git worktree"""
        try:
            result = subprocess.run(['git', 'worktree', 'remove', '--force', worktree_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Cleaned up worktree: {worktree_path}")
            else:
                print(f"Warning: Failed to remove worktree {worktree_path}: {result.stderr}")
        except Exception as e:
            print(f"Warning: Error cleaning up worktree {worktree_path}: {e}")
    
    def merge_task(self, name: str) -> int:
        """Merge worktree changes back to main branch"""
        task_data = self.read_task(name)
        if not task_data:
            print(f"Task '{name}' not found")
            return 1
        
        if not task_data.get('use_worktree'):
            print(f"Task '{name}' is not using a worktree")
            return 1
        
        worktree_path = task_data.get('worktree_path')
        if not worktree_path or not Path(worktree_path).exists():
            print(f"Worktree for task '{name}' not found")
            return 1
        
        try:
            # Get current directory (main repo)
            main_repo = os.getcwd()
            
            # Check current branch in worktree
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  cwd=worktree_path, capture_output=True, text=True)
            current_branch = result.stdout.strip()
            
            if not current_branch:
                print(f"Worktree '{name}' is in detached HEAD state")
                return 1
            
            # In worktree: add and commit any uncommitted changes
            subprocess.run(['git', 'add', '.'], cwd=worktree_path, check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=worktree_path)
            if result.returncode != 0:
                subprocess.run(['git', 'commit', '-m', f"Task {name}: final changes"], 
                             cwd=worktree_path, check=True)
                print(f"Committed changes in worktree branch '{current_branch}'")
            
            # In main repo: merge the branch into current branch (not main)
            current_main_branch = subprocess.run(['git', 'branch', '--show-current'], 
                                                cwd=main_repo, capture_output=True, text=True, check=True)
            target_branch = current_main_branch.stdout.strip()
            
            subprocess.run(['git', 'merge', current_branch], cwd=main_repo, check=True)
            
            print(f"✅ Successfully merged changes from task '{name}' (branch: {current_branch}) into {target_branch}")
            print(f"💡 You can now remove the task with: .claude/ct remove {name}")
            return 0
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error merging task '{name}': {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error merging task '{name}': {e}")
            return 1

def main() -> int:
    if len(sys.argv) < 2:
        print("Claude Task Manager")
        print()
        print("Usage: claude-tasks <command> [args]")
        print()
        print("Commands:")
        print("  start <name> <message> [dir] [--worktree]  Start a new Claude background task")
        print("  continue <name> <message>                  Continue an existing Claude task")
        print("  merge <name>                               Merge worktree changes back to main")
        print("  list                                       List all Claude tasks")
        print("  conversation <name>                        Show clean task conversation")
        print("  status <name>                              Show task status and completion info")
        print("  show <name>                                Show detailed Claude task info")
        print("  output <name>                              Show Claude task output with metadata")
        print("  remove <name>                              Remove a Claude task from tracking")

        print()
        print("Examples:")
        print('  claude-tasks start backend "Fix the login bug" /path/to/backend')
        print('  claude-tasks start feature "Add new API" --worktree')
        print('  claude-tasks continue backend "Continue fixing the login bug"')
        print("  claude-tasks merge feature  # Merge worktree changes to main")
        print("  claude-tasks conversation backend")
        print("  claude-tasks list")
        return 0
    
    manager = TaskManager()
    command = sys.argv[1]
    
    if command == 'start':
        if len(sys.argv) < 4:
            print("Usage: claude-tasks start <name> <message> [dir] [--worktree]")
            return 1
        name, message = sys.argv[2], sys.argv[3]
        project_dir = None
        use_worktree = False
        
        # Parse remaining arguments
        for arg in sys.argv[4:]:
            if arg == '--worktree':
                use_worktree = True
            elif project_dir is None:
                project_dir = arg
        
        return manager.start_task(name, message, project_dir, use_worktree)
    
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
    
    elif command == 'status':
        if len(sys.argv) < 3:
            print("Usage: claude-tasks status <name>")
            return 1
        return manager.status_task(sys.argv[2])
    
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
    
    elif command == 'merge':
        if len(sys.argv) < 3:
            print("Usage: claude-tasks merge <name>")
            return 1
        return manager.merge_task(sys.argv[2])
    
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