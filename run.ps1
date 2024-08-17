# Get the first argument as $CMD
$CMD = $args[0]
# Shift the arguments (not directly supported in PowerShell 1.0)
$CMD_args = $args[1..($args.Length - 1)]

if ($CMD -eq "install") {
    # Create a virtual environment
    # ONLY use python3 here! After \activate, only call 'python'!
    python3 -m venv venv
    # Activate the virtual environment
    & .\venv\Scripts\activate
    if (! ($?)) { 
        Write-Output "Could not activate venv"
        exit 1
    } 
    # Upgrade pip
    python -m ensurepip --upgrade
    if (! ($?)) { 
        Write-Output "Could not run pip"
        exit 1
    }
    # Upgrade setuptools
    pip install --upgrade setuptools
    # Install requirements
    pip install --upgrade -r requirements.txt
    exit 0
}

# Activate the virtual environment (if not already done)
& .\venv\Scripts\activate
if (! ($?)) { 
    Write-Output "Could not activate venv"
    exit 1 
} 

if ($CMD -eq "server") {
    flask run --host=0.0.0.0 --port=5000 $CMD_args
}
elseif ($CMD -eq "dcf") {
    python .\dcf.py $CMD_args
}
elseif ($CMD -eq "lint") {
    mypy (Get-ChildItem -Filter *.py)
    flake8
    # Check formatting with yapf (PowerShell 1.0 has no output redirection)
    yapf -d (Get-ChildItem -Filter *.py)
    if (! ($?)) { 
        "Format not happy, do ./run format!" 
        exit 1 
    }
}
elseif ($CMD -eq "format") {
    yapf -i (Get-ChildItem -Filter *.py) $CMD_args
}
elseif ($CMD -eq "test") {
    # Lint and run tests
    .\run lint
    if ($?) {
        # Not working right now...
        python -m pytest -v -q tests\ $CMD_args
    }
}
else {
    # Execute the command directly if it's not one of the above
    & $CMD $CMD_args
}
