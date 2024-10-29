# winget install Microsoft.PowerShell
# Version 7 runs in the VSCode Powershell extension
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
# scoop bucket add extras
# scoop install miniconda3
# conda init powershell
# conda create --prefix conda

# conda activate .\conda

# conda config --add channels conda-forge
# conda config --set channel_priority strict
# conda install python=3.10 numpy=1.24 python-dotenv absl-py elasticsearch-dsl pip setuptools yapf ipython pytest pyparsing cython
# conda install rasterio gdal
# conda update --all --yes

# https://github.com/bycloudai/InstallVSBuildToolsWindows

# Get the first argument as $CMD
$CMD = $args[0]
# Shift the arguments (not directly supported in PowerShell 1.0)
$CMD_args = $args[1..($args.Length - 1)]

if ($CMD -eq "install") {
    # Create a virtual environment
    # ONLY use python3 here! After \activate, only call 'python'!
    # python3 -m venv venv
    # Activate the virtual environment
    # & .\venv\Scripts\activate
    if (! ($?)) { 
        Write-Output "Could not activate venv"
        exit 1
    } 
    # Upgrade pip
    # python -m ensurepip --upgrade
    # python -m pip install --upgrade pip
    if (! ($?)) { 
        Write-Output "Could not run pip"
        exit 1
    }
    # Upgrade setuptools
    # python -m pip install --upgrade setuptools
    # Install requirements
    pip install --upgrade -r requirements.txt
    exit 0
}

# Activate the virtual environment (if not already done)
# & .\venv\Scripts\activate
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
elseif ($CMD -eq "alti") {
    python .\cy\setup.py build_ext --inplace && python .\alti.py $CMD_args
}
elseif ($CMD -eq "cy") {
    python .\cy\setup.py build_ext --inplace
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
