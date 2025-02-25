import os
import sys
import shutil
from pathlib import Path
import subprocess

def create_installer():
    print("Creating StageDeck Installer...")
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Clean previous builds
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Create executable using PyInstaller
    print("Creating executable...")
    result = subprocess.run(['pyinstaller', 'stagedeck.spec'], 
                          capture_output=True, 
                          text=True)
    
    if result.returncode != 0:
        print("Error creating executable:")
        print(result.stderr)
        return
    
    # Create output directory structure
    dist_dir = Path('dist')
    output_dir = dist_dir / 'StageDeck'
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    # Copy executable and dependencies
    exe_dir = dist_dir / 'StageDeck'
    if exe_dir.exists():
        print("Copying files to output directory...")
        
        # Create final zip file
        print("Creating zip archive...")
        shutil.make_archive(
            'StageDeck Installer',
            'zip',
            dist_dir
        )
        
        print("\nInstaller creation complete!")
        print(f"Installer package: {os.path.abspath('StageDeck Installer.zip')}")
    else:
        print("Error: Build directory not found!")
        print(f"Expected: {exe_dir}")

if __name__ == '__main__':
    create_installer()
