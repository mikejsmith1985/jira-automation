#!/usr/bin/env node

/**
 * Copy the packaged EXE from electron-packager output to the release directory
 */

const fs = require('fs');
const path = require('path');

const srcFile = path.join(__dirname, '../release/Jira Automation Assistant-win32-x64/Jira Automation Assistant.exe');
const destFile = path.join(__dirname, '../release/JiraAutomationAssistant.exe');

try {
  if (!fs.existsSync(srcFile)) {
    console.error(`Source EXE not found: ${srcFile}`);
    process.exit(1);
  }

  fs.copyFileSync(srcFile, destFile);
  const stats = fs.statSync(destFile);
  console.log(`✓ Copied EXE to: ${destFile}`);
  console.log(`  Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
} catch (error) {
  console.error(`Error copying EXE: ${error.message}`);
  process.exit(1);
}
