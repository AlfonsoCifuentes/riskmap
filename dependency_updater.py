import subprocess
import sys
import pkg_resources

def run_command(command, shell=False):
    """Runs a command and prints its output, raising an exception on error."""
    print(f"Executing: {' '.join(command)}")
    try:
        # Using shell=True for Windows compatibility with pip commands
        result = subprocess.run(command, check=True, capture_output=True, text=True, shell=shell)
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}", file=sys.stderr)
        print(f"Return code: {e.returncode}", file=sys.stderr)
        print(f"Output: {e.stdout}", file=sys.stderr)
        print(f"Error Output: {e.stderr}", file=sys.stderr)
        raise

def get_package_version(package_name):
    """Gets the version of an installed package."""
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return None

def main():
    """
    Verifies Python version, uninstalls/installs/updates packages,
    and reports the final state.
    """
    print("--- Starting Dependency Update Script ---")
    pip_executable = [sys.executable, "-m", "pip"]

    # 1. Verify Python Version
    print("\n1. Verifying Python version...")
    if not (sys.version_info.major == 3 and sys.version_info.minor == 11):
        print(f"WARNING: Python version is {sys.version_info.major}.{sys.version_info.minor}, but 3.11 is recommended.")
    else:
        print("✅ Python 3.11 confirmed.")

    try:
        # 2. Manage NumPy
        print("\n2. Managing NumPy version...")
        current_numpy_version = get_package_version("numpy")
        if current_numpy_version and current_numpy_version < "1.26":
            print(f"NumPy version {current_numpy_version} is older than 1.26. Uninstalling.")
            run_command(pip_executable + ["uninstall", "-y", "numpy"], shell=True)
        
        print("Installing NumPy 1.26.4...")
        run_command(pip_executable + ["install", "numpy==1.26.4"], shell=True)

        # 3. Update Core Libraries
        print("\n3. Updating core data science libraries...")
        packages_to_update = [
            "pandas",
            "scipy",
            "matplotlib",
            "scikit-learn",
            "torch"
        ]
        run_command(pip_executable + ["install", "--upgrade"] + packages_to_update, shell=True)

        # 4. Install from requirements file
        print("\n4. Installing dependencies from requirements_enhanced_historical_fixed.txt...")
        run_command(pip_executable + ["install", "-r", "requirements_enhanced_historical_fixed.txt"], shell=True)

        # 5. Report final versions
        print("\n5. Reporting final installed versions...")
        packages_to_report = [
            "numpy", "pandas", "scipy", "matplotlib", 
            "scikit-learn", "torch", "tensorflow", "keras", "groq"
        ]
        for pkg in packages_to_report:
            version = get_package_version(pkg)
            status = f"✅ {pkg} version: {version}" if version else f"❌ {pkg} is not installed."
            print(status)

    except (subprocess.CalledProcessError, Exception) as e:
        print(f"\n--- An error occurred: {e} ---", file=sys.stderr)
        print("--- Dependency Update Failed ---", file=sys.stderr)
        sys.exit(1)

    print("\n--- Dependency Update Finished Successfully ---")

if __name__ == "__main__":
    main()
