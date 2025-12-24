# 🚀 Jira Hygiene Assistant

A browser extension that helps you find and fix Jira ticket hygiene issues using the Jira REST API.

---

## ✨ Features

- ✅ **Find stale tickets** - Identify tickets with no updates in 7+ days
- ✅ **Find missing descriptions** - Locate tickets without descriptions
- ✅ **Find missing due dates** - Discover tickets lacking due dates
- ✅ **Custom JQL queries** - Run your own Jira Query Language searches
- ✅ **Bulk actions** - Add comments to multiple tickets at once
- ✅ **Works everywhere** - Compatible with Jira Server and Cloud (REST API v2)

---

## 📦 Installation

### For Chrome/Edge:

1. Open your browser and navigate to:
   - **Chrome:** `chrome://extensions`
   - **Edge:** `edge://extensions`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `jira-hygiene-extension` folder from this repository

### Building the Extension:

If you want to create a packaged `.zip` file:

```powershell
.\build-extension.ps1
```

Output: `jira-hygiene-extension.zip`

---

## 🛠️ Usage

1. **Configure Jira URL:**
   - Click the extension icon in your browser toolbar
   - Enter your Jira base URL (e.g., `https://company.atlassian.net`)
   - Click **Save Settings**

2. **Navigate to Jira:**
   - Open any Jira page in your browser
   - The extension will automatically detect Jira pages

3. **Run Queries:**
   - Click the extension icon
   - Choose a pre-built query or enter custom JQL
   - Click **Find Tickets** to see results

4. **Take Action:**
   - Review the list of found tickets
   - Use bulk actions (e.g., add comments) as needed

---

## 🏗️ Architecture

The extension consists of two main components:

```
┌──────────────────────────────────────────────┐
│  POPUP UI (popup.html / popup.js)            │
│  ─────────────────────────────────────────   │
│  • Settings configuration (Jira URL)         │
│  • Pre-built query buttons                   │
│  • Custom JQL input                          │
│  • Bulk action controls                      │
│  • Stores results in chrome.storage          │
│  • Sends messages to content script          │
└─────────────────┬────────────────────────────┘
                  │ 
                  │ chrome.tabs.sendMessage()
                  ↓
┌──────────────────────────────────────────────┐
│  CONTENT SCRIPT (content.js)                 │
│  ─────────────────────────────────────────   │
│  • Injected into all Jira pages              │
│  • Receives messages from popup              │
│  • Makes Jira REST API calls                 │
│  • Returns ticket data to popup              │
│  • Adds comments via API                     │
│  • Uses your browser's Jira session          │
└──────────────────────────────────────────────┘
```

**How it works:**
1. User clicks extension icon → opens popup
2. User selects a query → popup sends message to content script
3. Content script calls Jira REST API `/rest/api/2/search`
4. Results sent back to popup
5. Popup stores results and opens Jira tab with JQL query
6. User can bulk add comments → content script posts to `/rest/api/2/issue/{key}/comment`

---

## 📂 Project Structure

```
jira-automation/
│
├── jira-hygiene-extension/      # Extension source files
│   ├── manifest.json            # Extension configuration
│   ├── popup.html               # Extension popup UI
│   ├── popup.js                 # Popup logic
│   ├── content.js               # Content script (Jira integration)
│   ├── icon.png                 # Extension icon
│   └── README.md                # Extension-specific docs
│
├── build-extension.ps1          # Build script for packaging
├── package.json                 # Project metadata
└── README.md                    # This file
```

---

## 🔧 Configuration

### Settings Storage:

The extension stores your Jira URL using Chrome's storage API. Settings persist across browser sessions.

### Supported Jira Versions:

- ✅ Jira Cloud (REST API v2)
- ✅ Jira Server 7.x+ (REST API v2)
- ✅ Jira Data Center

### Pre-built Queries:

1. **Stale Tickets:** `updated < -7d ORDER BY updated ASC`
2. **Missing Descriptions:** `description is EMPTY ORDER BY created DESC`
3. **Missing Due Dates:** `duedate is EMPTY ORDER BY created DESC`

---

## 🚨 Troubleshooting

### Extension not appearing:

**Problem:** Extension icon doesn't show in toolbar
```
Solution: Pin the extension from the extensions menu (puzzle icon)
```

### API errors:

**Problem:** "Failed to fetch" or CORS errors
- **Cause:** Incorrect Jira URL or authentication issues
- **Solution:** 
  1. Verify Jira URL is correct
  2. Ensure you're logged into Jira in the same browser
  3. Check browser console (F12) for detailed errors

### No results returned:

**Problem:** Query runs but shows no tickets
- **Cause:** JQL query syntax error or no matching tickets
- **Solution:** Test your JQL query directly in Jira's issue search

---

## 🔐 Security & Permissions

### Required Permissions:

- **activeTab:** Access the current Jira tab
- **storage:** Save your Jira URL setting
- **host_permissions:** Make API calls to Jira domains

### Privacy Notes:

✅ **No external servers** - All data stays between your browser and Jira
✅ **No credential storage** - Uses your existing browser session
✅ **Local only** - No analytics or tracking
✅ **Open source** - All code is reviewable

---

## 🤝 Contributing

### Adding New Features:

1. Edit the appropriate file:
   - UI changes: `popup.html`, `popup.js`
   - Jira integration: `content.js`
   - Permissions: `manifest.json`

2. Test your changes:
   - Reload the extension in `chrome://extensions`
   - Test on a real Jira instance

3. Package for distribution:
   ```powershell
   .\build-extension.ps1
   ```

### Code Style:

- ✅ Use vanilla JavaScript (no build process required)
- ✅ Add comments explaining complex logic
- ✅ Follow existing code structure
- ✅ Test with both Jira Cloud and Server

---

## 📝 Changelog

### Version 0.0.1 (Current)

- ✅ Basic extension structure
- ✅ Jira REST API integration
- ✅ Pre-built hygiene queries
- ✅ Bulk comment functionality
- ✅ Settings persistence

### Planned Features:

- [ ] Additional bulk actions (assign, transition, update fields)
- [ ] Export results to CSV
- [ ] Scheduled checks with notifications
- [ ] Custom query templates
- [ ] Multi-project support
- [ ] Dashboard view

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🆘 Support

### Getting Help:

1. Check the browser console (F12) for error messages
2. Verify your Jira URL and authentication
3. Test JQL queries directly in Jira first
4. Review the Troubleshooting section above

### Useful Resources:

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v2/)
- [JQL Query Syntax](https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/)
- [Chrome Extension Development](https://developer.chrome.com/docs/extensions/)

---

## 🎯 Quick Start Checklist

- [ ] Install the extension in Chrome/Edge
- [ ] Click the extension icon and set your Jira URL
- [ ] Navigate to any Jira page
- [ ] Click the extension icon
- [ ] Select a query (e.g., "Find stale tickets")
- [ ] Click "Find Tickets" and review results!

---

**Built with ❤️ for teams who want cleaner Jira hygiene**
