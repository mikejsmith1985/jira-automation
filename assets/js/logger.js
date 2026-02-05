/**
 * Automatic JavaScript Logger for Waypoint
 * Captures all console logs and sends to backend for automatic feedback attachment
 */

(function() {
    const LOG_BUFFER_SIZE = 500; // Keep last 500 log entries
    const logBuffer = [];
    const LOG_ENDPOINT = '/log_frontend';
    
    // Track if we've already sent logs recently to avoid spam
    let lastSendTime = 0;
    const BATCH_INTERVAL = 2000; // Send logs every 2 seconds max
    let pendingLogs = [];
    
    /**
     * Format log entry with timestamp and level
     */
    function formatLogEntry(level, args) {
        const timestamp = new Date().toISOString();
        const message = Array.from(args).map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg, null, 2);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');
        
        return {
            timestamp,
            level,
            message
        };
    }
    
    /**
     * Send logs to backend in batches
     */
    function sendLogsToBackend() {
        if (pendingLogs.length === 0) return;
        
        const now = Date.now();
        if (now - lastSendTime < BATCH_INTERVAL) {
            return; // Too soon, will send in next batch
        }
        
        const logsToSend = [...pendingLogs];
        pendingLogs = [];
        lastSendTime = now;
        
        fetch(LOG_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ logs: logsToSend })
        }).catch(err => {
            // Silent fail - don't create infinite loop
        });
    }
    
    /**
     * Add log to buffer and queue for sending
     */
    function captureLog(level, args) {
        const entry = formatLogEntry(level, args);
        
        // Add to in-memory buffer (for immediate access)
        logBuffer.push(entry);
        if (logBuffer.length > LOG_BUFFER_SIZE) {
            logBuffer.shift();
        }
        
        // Queue for backend storage
        pendingLogs.push(entry);
        
        // Debounced send
        setTimeout(sendLogsToBackend, BATCH_INTERVAL);
    }
    
    // Intercept console methods
    const originalConsole = {
        log: console.log,
        info: console.info,
        warn: console.warn,
        error: console.error,
        debug: console.debug
    };
    
    console.log = function(...args) {
        captureLog('INFO', args);
        originalConsole.log.apply(console, args);
    };
    
    console.info = function(...args) {
        captureLog('INFO', args);
        originalConsole.info.apply(console, args);
    };
    
    console.warn = function(...args) {
        captureLog('WARN', args);
        originalConsole.warn.apply(console, args);
    };
    
    console.error = function(...args) {
        captureLog('ERROR', args);
        originalConsole.error.apply(console, args);
    };
    
    console.debug = function(...args) {
        captureLog('DEBUG', args);
        originalConsole.debug.apply(console, args);
    };
    
    // Capture unhandled errors
    window.addEventListener('error', function(event) {
        captureLog('ERROR', [
            'Uncaught error:',
            event.message,
            'at', event.filename + ':' + event.lineno + ':' + event.colno,
            event.error ? event.error.stack : ''
        ]);
    });
    
    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        captureLog('ERROR', [
            'Unhandled promise rejection:',
            event.reason
        ]);
    });
    
    // Export for manual access if needed
    window.WaypointLogger = {
        getLogs: () => [...logBuffer],
        clearLogs: () => { logBuffer.length = 0; },
        getLogCount: () => logBuffer.length
    };
    
    console.log('[Waypoint Logger] Automatic logging initialized - all logs will be captured for feedback system');
})();
