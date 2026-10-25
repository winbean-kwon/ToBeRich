Set-Service w32time -StartupType Manual -ErrorAction SilentlyContinue
Start-Service w32time -ErrorAction SilentlyContinue
w32tm /resync /force
w32tm /query /status
