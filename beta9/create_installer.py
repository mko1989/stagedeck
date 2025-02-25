import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_installer():
    print("Creating StageDeck Installer...")

    # Clean up previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")
    output_dir = Path("StageDeck")
    installer_zip = Path("StageDeck Installer.zip")

    if dist_dir.exists():
        print("Cleaning dist...")
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        print("Cleaning build...")
        shutil.rmtree(build_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if installer_zip.exists():
        os.remove(installer_zip)

    # Create executable using PyInstaller
    print("Creating executable...")
    result = subprocess.run(['C:\\Python313\\python.exe', '-m', 'PyInstaller', 'stagedeck.spec'], 
                          capture_output=True, 
                          text=True)

    if result.returncode != 0:
        print("Error creating executable:")
        print(result.stderr)
        sys.exit(1)

    # Copy files to output directory
    dist_dir = Path("dist/StageDeck")
    if dist_dir.exists():
        print("Copying files to output directory...")
        
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        
        # Copy all files from dist
        for item in dist_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, output_dir)
            else:
                dest = output_dir / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
        
        # Create final zip file
        print("Creating zip archive...")
        shutil.make_archive("StageDeck Installer", "zip", ".", "StageDeck")
        
        print("\nInstaller creation complete!")
        print(f"Installer package: {os.path.abspath(installer_zip)}")
    else:
        print("Error: Build directory not found")

if __name__ == '__main__':
    create_installer()
