#!/usr/bin/env node

/**
 * This script creates the portable EXE after electron-builder fails due to code signing issues
 * It's a workaround for the winCodeSign symlink issue on Windows
 */

const fs = require('fs');
const path = require('path');

const srcFile = path.join(__dirname, '../release/win-unpacked/Jira Automation Assistant.exe');
const destFile = path.join(__dirname, '../release/JiraAutomationAssistant.exe');

try {
  if (!fs.existsSync(srcFile)) {
    console.error(`Source EXE not found: ${srcFile}`);
    process.exit(1);
  }

  fs.copyFileSync(srcFile, destFile);
  const stats = fs.statSync(destFile);
  console.log(`✓ Created portable EXE: ${destFile}`);
  console.log(`  Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
} catch (error) {
  console.error(`Error creating portable EXE: ${error.message}`);
  process.exit(1);
}
