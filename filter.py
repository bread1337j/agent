"""All credit for this goes to claude
(I'm not writing all this manually man)"""


# Keys are written without leading dashes: "--config", "-config" and "config" all match "config".
SUSPICIOUS_ARGS = {
    # Checked for every app. Shells, interpreters and system tools: if one of these
    # shows up as an argument, something is trying to run a command.
    "any": {
        "bash": "shell", "sh": "shell", "zsh": "shell", "fish": "shell", "dash": "shell",
        "python": "interpreter", "python3": "interpreter", "perl": "interpreter",
        "ruby": "interpreter", "node": "interpreter", "lua": "interpreter",
        "sudo": "runs as root", "su": "switches user", "pkexec": "runs as root", "doas": "runs as root",
        "rm": "deletes files", "dd": "overwrites disks/files", "mkfs": "formats disks",
        "shred": "destroys files", "chmod": "changes permissions", "chown": "changes ownership",
        "curl": "network transfer", "wget": "network transfer", "nc": "network connection",
        "ssh": "remote login", "scp": "remote copy", "eval": "runs a string as code",
        "exec": "runs a command", "e": "runs a command (-e in most terminals)",
    },
    # kitty
    "terminal": {
        "c": "loads a config file, which can set the shell or startup programs",
        "config": "loads a config file, which can set the shell or startup programs",
        "o": "overrides config options, e.g. shell=... or remote control",
        "override": "overrides config options, e.g. shell=... or remote control",
        "session": "session files launch programs",
        "watcher": "runs a Python file inside kitty",
        "listen-on": "opens a socket other programs can control kitty through",
        "replay-commands": "replays terminal commands from a file",
        "dump-bytes": "writes a file",
        "detached-log": "writes a file",
    },
    "firefox": {
        "profile": "starts with a different profile", "P": "starts with a different profile",
        "ProfileManager": "opens the profile manager",
        "headless": "runs invisibly",
        "screenshot": "writes a file",
        "marionette": "starts a remote-control server",
        "remote-debugging-port": "starts a remote-control server",
        "start-debugger-server": "starts a remote-control server",
        "remote-allow-hosts": "configures remote control",
        "jsconsole": "developer tools", "devtools": "developer tools",
        "jsdebugger": "developer tools", "wait-for-jsdebugger": "developer tools",
        "setDefaultBrowser": "changes system settings",
        "first-startup": "runs post-install actions",
        "allow-downgrade": "can damage your profile",
        "MOZ_LOG": "writes log files", "MOZ_LOG_FILE": "writes log files",
        "dbus-service": "runs as a system service",
        "data": "opens a data: URL, which can contain a whole page or script",
        "kiosk": "locks the screen in fullscreen",
    },
    "calculator": {},
}

# URLs that open local files, run scripts, or reach browser internals.
BLOCKED_URL_PREFIXES = ("file:", "data:", "javascript:", "about:", "chrome:", "view-source:")


def blocked_reason(app, args):
    """Return why args are blocked, or None if they look fine."""
    flagged = {**SUSPICIOUS_ARGS["any"], **SUSPICIOUS_ARGS.get(app, {})}
    for arg in args:
        key = arg.split("=", 1)[0].lstrip("-")
        if key in flagged:
            return f"{arg!r}: {flagged[key]}"
        if arg.lower().startswith(BLOCKED_URL_PREFIXES):
            return f"{arg!r}: blocked URL type"
    # kitty runs any non-option argument as a program, so only allow --directory <path>.
    if app == "terminal":
        i = 0
        while i < len(args):
            if args[i] in ("--directory", "-d", "--working-directory"):
                i += 2
            elif args[i].startswith(("--directory=", "--working-directory=")):
                i += 1
            else:
                return f"{args[i]!r}: kitty only allows --directory"
    return None


"""This part was made by me, 
you can tell because it's significantly worse"""

from pathlib import Path

Allowed_Files = {
        "output.txt": "General output area"
        }
def allowed_file_edits(filename: str):
    loc = Path(filename).name
    if loc in Allowed_Files:
        return f"Allowed access to {loc}: {Allowed_Files[loc]}"
    return None

