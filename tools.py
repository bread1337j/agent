
import json
import subprocess
from datetime import datetime
import os
import re

import copy

import filter
APPS = {"firefox": "firefox", "terminal":"kitty", "calculator": "kcalc"}

def get_time() -> str:
    """Gets the current time using datetime"""
    return datetime.now().strftime("It's %I:%M %p.")

def open_app(name: str, args: list[str] | None = None) -> str:
    """Opens an app with given arguments. Definitely not a security risk."""
    args = [os.path.expanduser(a) for a in (args or [])]
    reason = filter.blocked_reason(name, args)
    print("Trying to run: ", name, args)
    if reason:
        return f"Blocked: {reason}"
    subprocess.Popen([APPS[name]] + args, start_new_session=True)
    return f"Opening {name}."

def get_battery() -> str:
    """Gets the current battery charge by reading the file directly"""
    out = ""
    try:
        with open("/sys/class/power_supply/BAT1/capacity", "r") as f:
            out = f.read()
        return out
    except FileNotFoundError:
        return "The battery file is not available"

def get_schedule() -> str:
    """Runs schedulereader and returns the output"""
    process = subprocess.run(["/home/bread/bin/schedulereader", "/home/bread/schedule.csv"],
                               capture_output=True,
                               text=True)
    output = process.stdout.strip()
    #print(output)
    return output

def cat_file(filename: str) -> str:
    """Reads a file and returns its contents.
    If the file doesn't exist then it returns that fact"""
    filename = os.path.expanduser(filename)
    try:
        out = ""
        with open(filename, "r") as f:
            out = f.read()
            return out
    except FileNotFoundError:
        return f"No such file {filename}"

def write_file(filename: str, content: str) -> str:
    """Writes content to a file
    If the file doesn't exist, returns that fact"""
    filename = os.path.expanduser(filename)
    try:
        safeguard = filter.allowed_file_edits(filename)
        if not safeguard:
            return f"Blocked access to file {filename}, ensure you are using an available file."
        else:
            print(safeguard)
        with open(filename, "w") as f:
            f.write(content)
        return f"Wrote {content} to {filename}"
    except FileNotFoundError:
        return f"Tried opening non-existent file {filename}"

def get_dir() -> str:
    """Runs pwd and returns its output"""
    process = subprocess.run(["pwd"],
                               capture_output=True,
                               text=True)
    output = process.stdout.strip()
    return "Current directory: " + output

def ls() -> str:
    """Runs ls and returns its output"""
    process = subprocess.run(["ls", "-la"],
                               capture_output=True,
                               text=True)
    output = process.stdout.strip()
    return "Current directory's files: " + output

def cd(dirname: str) -> str:
    """Runs cd and returns the new directory"""
    dirname = os.path.expanduser(dirname)
    try:
        os.chdir(dirname)
        return "Changed directory to " + dirname
    except OSError as e:
        return f"Cannot access {dirname}, reason: {e}"


FUNCTIONS = {"get_time": get_time, "open_app": open_app, "get_battery": get_battery,
             "get_schedule": get_schedule, "cat_file": cat_file, "write_file": write_file,
             "get_dir": get_dir, "ls": ls, "cd": cd}


TOOLS = [
        {"type": "function", "function": {
            "name": "get_time",
            "description": "Get the current time.",
            "parameters": {"type": "object", "properties": {}},
            }},
        {"type": "function", "function": {
            "name": "open_app",
            "description": "Open an application. Note that you are heavily restricted from running processes inside these applications. If you want to run a terminal command, write that command to a file and ask the user to run it instead. Otherwise, the terminal may only have --directory as an argument",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "enum": list(APPS)},
                    "args": {"type": "array", "items": {"type": "string"},
                             "description": "Command-line arguments for the program. One item per argument. Omit if none."}
                               },
                "required": ["name"]
                           },
            }},
        {"type": "function", "function": {
            "name": "get_battery",
            "description": "Get the laptop battery's current charge",
            "parameters": {
                "type": "object",
                "properties": {},
                }
            }},
        {"type": "function", "function": {
            "name": "get_schedule",
            "description": """Returns a string that states the current class, time until the class starts/finishes, and the next class. In the mornings, the first class shown might yet not have started. In that case, the string will say 'time until start' as opposed to 'time until end'. If the class hasn't started yet, and the user asks 'what's the next class', assume the user wants to know about the next class that has not yet started. 
            Keep in mind that you do not have access to any further information regarding the classes.""",
            "parameters": {
                "type": "object",
                "properties": {}
                },
            }},
        {"type": "function", "function": {
            "name": "cat_file",
            "description": "Returns the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                    },
                "required": ["filename"],
                },
            }},
        {"type": "function", "function": {
            "name": "write_file",
            "description": "Writes content to a file. Note that the only file you are allowed to edit is output.txt. Any attempt at writing to another file will be blocked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"}
                    },
                "required": ["filename", "content"],
                },
            }},
        {"type": "function", "function": {
            "name": "get_dir",
            "description": "Returns a string with the current working directory",
            "parameters": {
                "type": "object",
                "properties": {},
                }
            }},
        {"type": "function", "function": {
            "name": "ls",
            "description": "Returns a string with the output of `ls -la` in the current directory",
            "parameters": {
                "type": "object",
                "properties": {},
                }
            }},
        {"type": "function", "function": {
            "name": "cd",
            "description": "Change directories to dirname.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirname": {"type": "string"}
                    },
                "required": ["dirname"],
                },
            }},
        ]
