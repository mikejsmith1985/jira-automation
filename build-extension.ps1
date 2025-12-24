# Script to build the complete extension
Write-Host "Building Jira Hygiene Assistant Extension..." -ForegroundColor Cyan

$extDir = "jira-hygiene-extension"
if (Test-Path $extDir) {
    Remove-Item -Recurse -Force $extDir
}
New-Item -ItemType Directory $extDir | Out-Null

# Create manifest.json
$manifest = @'
{
  "manifest_version": 3,
  "name": "Jira Hygiene Assistant",
  "version": "0.0.1",
  "description": "Automate Jira ticket hygiene checks and fixes",
  "permissions": ["activeTab", "storage"],
  "host_permissions": ["http://*/*", "https://*/*"],
  "action": {"default_popup": "popup.html", "default_icon": "icon.png"},
  "content_scripts": [{"matches": ["http://*/*", "https://*/*"], "js": ["content.js"], "run_at": "document_idle"}],
  "icons": {"128": "icon.png"}
}
'@
$manifest | Set-Content "$extDir\manifest.json"

# Create icon (simple blue square with J)
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap(128, 128)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(0, 82, 204))
$font = New-Object System.Drawing.Font("Arial", 48, [System.Drawing.FontStyle]::Bold)
$brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
$g.DrawString("J", $font, $brush, 40, 30)
$bmp.Save("$extDir\icon.png")
$g.Dispose()
$bmp.Dispose()

Write-Host "✓ Created manifest.json and icon.png" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Manually create popup.html, popup.js, content.js, and README.md in $extDir" -ForegroundColor Yellow
Write-Host "See extension source files for content" -ForegroundColor Yellow
