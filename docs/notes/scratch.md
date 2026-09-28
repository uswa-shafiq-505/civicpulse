# Day 2 scratch
- Broke: `&&` chains pasted into PowerShell; "token '&&' is not a valid statement separator."
- Believed: Node was not installed (winget said it was). Real cause: C:\Program Files\nodejs not on User PATH.
- Fixed: SetEnvironmentVariable PATH + reopened terminal; used --legacy-peer-deps for openapi-typescript@7 vs TypeScript 6.
