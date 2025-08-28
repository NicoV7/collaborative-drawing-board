#!/usr/bin/env python3
"""
Development setup script for backend.
Creates virtual environment and installs dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Command: {cmd}")
        print(f"  Error: {e.stderr}")
        sys.exit(1)

def main():
    """Set up development environment."""
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check if virtual environment exists
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        run_command("python -m venv venv", "Creating virtual environment")
    
    # Activate virtual environment and install dependencies
    if sys.platform == "win32":
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")
    
    print(f"\n✓ Development environment setup complete!")
    print(f"\nTo activate the virtual environment:")
    if sys.platform == "win32":
        print(f"  venv\\Scripts\\activate")
    else:
        print(f"  source venv/bin/activate")
    
    print(f"\nTo run tests:")
    print(f"  {python_cmd} -m pytest")

if __name__ == "__main__":
    main()