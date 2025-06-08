#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');

try {
    // Run the claude tasks list command
    const result = execSync('.claude/ct list', { 
        encoding: 'utf8',
        cwd: process.cwd()
    });
    
    const data = JSON.parse(result);
    const tasks = data.tasks || [];
    
    if (tasks.length === 0) {
        console.log('📝 No Claude tasks running');
        return;
    }
    
    console.log(`🤖 Claude Tasks (${tasks.length}):`);
    console.log('─'.repeat(50));
    
    tasks.forEach(task => {
        const statusIcon = task.status === 'active' ? '✅' : 
                          task.status === 'starting' ? '⏳' : '❓';
        
        const sessionInfo = task.session_id ? 
            ` (${task.session_id.substring(0, 8)}...)` : '';
        
        console.log(`${statusIcon} ${task.name}${sessionInfo}`);
        console.log(`   💬 ${task.requests} requests → ${task.responses} responses`);
        
        if (task.status === 'starting') {
            console.log('   🔄 Task still processing...');
        }
        console.log('');
    });
    
    // Summary
    const active = tasks.filter(t => t.status === 'active').length;
    const starting = tasks.filter(t => t.status === 'starting').length;
    
    if (starting > 0) {
        console.log(`⚡ ${active} active, ${starting} starting`);
    } else {
        console.log(`⚡ ${active} active tasks`);
    }
    
} catch (error) {
    if (error.message.includes('No such file')) {
        console.log('❌ Claude tasks not found. Run from project root.');
    } else if (error.message.includes('No tasks')) {
        console.log('📝 No Claude tasks running');
    } else {
        console.log('❌ Error checking Claude tasks:', error.message);
    }
}