const vscode = require('vscode');
const { execSync } = require('child_process');
const path = require('path');

class ClaudeTaskProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.setupFileWatcher();
    }

    refresh() {
        this._onDidChangeTreeData.fire();
    }

    setupFileWatcher() {
        // Watch the tasks directory for changes
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (workspaceRoot) {
            const tasksPattern = new vscode.RelativePattern(workspaceRoot, '.claude/claude-sessions/tasks/*.json');
            
            const watcher = vscode.workspace.createFileSystemWatcher(tasksPattern);
            
            // Refresh on any file changes in the tasks directory
            watcher.onDidCreate(() => this.refresh());
            watcher.onDidChange(() => this.refresh());
            watcher.onDidDelete(() => this.refresh());
            
            console.log('Claude Tasks: File watcher setup for', tasksPattern.pattern);
        }
    }

    getTreeItem(element) {
        return element;
    }

    getChildren(element) {
        if (!element) {
            // Root level - return tasks
            return this.getTasks();
        }
        return [];
    }

    async getTasks() {
        try {
            // Get the workspace root
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                return [new vscode.TreeItem('No workspace open', vscode.TreeItemCollapsibleState.None)];
            }

            // Run the claude tasks list command
            const result = execSync('.claude/ct list', { 
                encoding: 'utf8',
                cwd: workspaceRoot
            });
            
            const data = JSON.parse(result);
            const tasks = data.tasks || [];
            
            if (tasks.length === 0) {
                const item = new vscode.TreeItem('No Claude tasks running', vscode.TreeItemCollapsibleState.None);
                item.iconPath = new vscode.ThemeIcon('info');
                return [item];
            }

            return tasks.map(task => {
                const statusIcon = task.status === 'active' ? 'check' : 'clock';
                const label = `${task.name} (${task.requests}r/${task.responses}r)`;
                
                const item = new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
                item.iconPath = new vscode.ThemeIcon(statusIcon);
                item.contextValue = 'task';
                item.command = {
                    command: 'claudeTasks.showConversation',
                    title: 'Show Conversation',
                    arguments: [task.name]
                };
                
                // Add tooltip with more info
                item.tooltip = `Status: ${task.status}\\nSession ID: ${task.session_id || 'Not set'}\\nRequests: ${task.requests}\\nResponses: ${task.responses}`;
                
                // Add description for status
                if (task.status === 'starting') {
                    item.description = '⏳ Processing...';
                } else if (task.status === 'active') {
                    item.description = '✅ Ready';
                }
                
                return item;
            });
            
        } catch (error) {
            console.error('Error getting Claude tasks:', error);
            const item = new vscode.TreeItem('Error loading tasks', vscode.TreeItemCollapsibleState.None);
            item.iconPath = new vscode.ThemeIcon('error');
            item.tooltip = error.message;
            return [item];
        }
    }
}

function activate(context) {
    console.log('Claude Tasks extension activating...');
    
    const provider = new ClaudeTaskProvider();
    
    // Register the tree data provider
    const treeView = vscode.window.createTreeView('claudeTasksView', {
        treeDataProvider: provider,
        showCollapseAll: false
    });
    
    console.log('Claude Tasks tree view created');

    // Register commands
    const refreshCommand = vscode.commands.registerCommand('claudeTasks.refresh', () => {
        provider.refresh();
        vscode.window.showInformationMessage('Claude tasks refreshed');
    });

    const showConversationCommand = vscode.commands.registerCommand('claudeTasks.showConversation', async (taskName) => {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                vscode.window.showErrorMessage('No workspace open');
                return;
            }

            // Run the conversation command
            const result = execSync(`.claude/ct conversation "${taskName}"`, { 
                encoding: 'utf8',
                cwd: workspaceRoot
            });
            
            // Create and show a new document with the conversation
            const doc = await vscode.workspace.openTextDocument({
                content: result,
                language: 'markdown'
            });
            
            await vscode.window.showTextDocument(doc);
            
        } catch (error) {
            vscode.window.showErrorMessage(`Error showing conversation: ${error.message}`);
        }
    });

    const startTaskCommand = vscode.commands.registerCommand('claudeTasks.startTask', async () => {
        try {
            const taskName = await vscode.window.showInputBox({
                prompt: 'Enter task name',
                placeholder: 'e.g., analyze-code'
            });
            
            if (!taskName) return;
            
            const message = await vscode.window.showInputBox({
                prompt: 'Enter task message/prompt',
                placeholder: 'e.g., Analyze this codebase for security issues'
            });
            
            if (!message) return;
            
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                vscode.window.showErrorMessage('No workspace open');
                return;
            }

            // Start the task
            const result = execSync(`.claude/ct start "${taskName}" "${message}"`, { 
                encoding: 'utf8',
                cwd: workspaceRoot
            });
            
            vscode.window.showInformationMessage(`Started Claude task: ${taskName}`);
            provider.refresh();
            
        } catch (error) {
            vscode.window.showErrorMessage(`Error starting task: ${error.message}`);
        }
    });

    context.subscriptions.push(refreshCommand, showConversationCommand, startTaskCommand);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};