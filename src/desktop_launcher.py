"""
Desktop application launcher for Medical RAG.
Handles Ollama detection, model verification, and application startup.
"""

import os
import platform
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional

import httpx

from src.logger import logger
from src.user_data import get_user_data_manager


class OllamaManager:
    """Manages Ollama installation and model availability."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama manager.

        Args:
            base_url: Ollama API base URL
        """
        self.base_url = base_url
        self.timeout = 5.0

    def is_installed(self) -> bool:
        """
        Check if Ollama is installed on the system.

        Returns:
            True if Ollama is installed, False otherwise
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            # Check common installation paths
            paths = [
                "/usr/local/bin/ollama",
                "/opt/homebrew/bin/ollama",
                Path.home() / ".ollama" / "bin" / "ollama",
            ]
            for path in paths:
                if Path(path).exists():
                    logger.info(f"Found Ollama at: {path}")
                    return True

        elif system == "Windows":
            # Check if ollama.exe is in PATH or common locations
            paths = [
                "ollama.exe",  # In PATH
                Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
                Path(os.getenv("PROGRAMFILES", "")) / "Ollama" / "ollama.exe",
            ]
            for path in paths:
                try:
                    if isinstance(path, str):
                        # Check PATH
                        result = subprocess.run(
                            ["where", path],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if result.returncode == 0:
                            logger.info(f"Found Ollama in PATH")
                            return True
                    elif Path(path).exists():
                        logger.info(f"Found Ollama at: {path}")
                        return True
                except Exception:
                    pass

        elif system == "Linux":
            # Check common Linux paths
            paths = [
                "/usr/bin/ollama",
                "/usr/local/bin/ollama",
                Path.home() / ".local" / "bin" / "ollama",
            ]
            for path in paths:
                if Path(path).exists():
                    logger.info(f"Found Ollama at: {path}")
                    return True

        logger.warning("Ollama not found on system")
        return False

    def is_running(self) -> bool:
        """
        Check if Ollama service is running.

        Returns:
            True if Ollama is responding to API requests, False otherwise
        """
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            if response.status_code == 200:
                logger.info("Ollama service is running")
                return True
        except Exception as e:
            logger.debug(f"Ollama not responding: {e}")

        return False

    def get_installed_models(self) -> list[str]:
        """
        Get list of installed Ollama models.

        Returns:
            List of model names
        """
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                logger.info(f"Found {len(model_names)} installed models")
                return model_names
        except Exception as e:
            logger.error(f"Failed to get installed models: {e}")

        return []

    def has_required_models(self, required_models: list[str]) -> tuple[bool, list[str]]:
        """
        Check if required models are installed.

        Args:
            required_models: List of required model names

        Returns:
            Tuple of (all_present, missing_models)
        """
        installed = self.get_installed_models()
        missing = []

        for model in required_models:
            # Check if model (with or without tag) is installed
            model_base = model.split(":")[0]
            if not any(m.startswith(model_base) for m in installed):
                missing.append(model)

        return len(missing) == 0, missing

    def pull_model(self, model_name: str, callback=None) -> bool:
        """
        Pull/download an Ollama model.

        Args:
            model_name: Name of model to pull
            callback: Optional callback function for progress updates

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Pulling model: {model_name}")
        print(f"\nDownloading model: {model_name}")
        print("This may take a few minutes...")

        try:
            # Use ollama CLI to pull model
            system = platform.system()
            cmd = ["ollama", "pull", model_name]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Stream output
            if process.stdout:
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        print(line)
                        if callback:
                            callback(line)

            process.wait()

            if process.returncode == 0:
                logger.info(f"Successfully pulled model: {model_name}")
                print(f"✓ Model {model_name} downloaded successfully\n")
                return True
            else:
                logger.error(f"Failed to pull model: {model_name}")
                print(f"✗ Failed to download model: {model_name}\n")
                return False

        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            print(f"✗ Error: {e}\n")
            return False

    def start_service(self) -> bool:
        """
        Attempt to start Ollama service.

        Returns:
            True if service started or already running, False otherwise
        """
        if self.is_running():
            return True

        logger.info("Attempting to start Ollama service...")
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                # Try to start Ollama as a background service
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif system == "Windows":
                # On Windows, Ollama usually runs as a service
                # Try to start it
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            elif system == "Linux":
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Wait a few seconds for service to start
            logger.info("Waiting for Ollama service to start...")
            for i in range(10):
                time.sleep(1)
                if self.is_running():
                    logger.info("Ollama service started successfully")
                    return True

            logger.warning("Ollama service did not start in time")
            return False

        except Exception as e:
            logger.error(f"Failed to start Ollama service: {e}")
            return False


class DesktopLauncher:
    """Desktop application launcher."""

    def __init__(self):
        """Initialize desktop launcher."""
        self.user_data = get_user_data_manager()
        self.ollama = OllamaManager()
        self.required_models = ["deepseek-r1:1.5b", "nomic-embed-text"]

    def check_prerequisites(self) -> bool:
        """
        Check if all prerequisites are met.

        Returns:
            True if ready to launch, False otherwise
        """
        print("\n" + "=" * 60)
        print("Medical Research RAG - Desktop Application")
        print("=" * 60 + "\n")

        # Check Ollama installation
        print("Checking prerequisites...")
        print(f"  [1/3] Ollama installation... ", end="")
        if not self.ollama.is_installed():
            print("✗ NOT FOUND")
            self._show_ollama_install_instructions()
            return False
        print("✓ OK")

        # Check Ollama service
        print(f"  [2/3] Ollama service... ", end="")
        if not self.ollama.is_running():
            print("⚠ NOT RUNNING")
            print("         Attempting to start Ollama...")
            if not self.ollama.start_service():
                print("         ✗ Failed to start Ollama")
                print("\n  Please start Ollama manually and try again.")
                return False
            print("         ✓ Ollama started")
        else:
            print("✓ RUNNING")

        # Check required models
        print(f"  [3/3] Required models... ", end="")
        has_models, missing = self.ollama.has_required_models(self.required_models)
        if not has_models:
            print(f"⚠ MISSING: {', '.join(missing)}")
            if not self._download_missing_models(missing):
                return False
            print("         ✓ All models downloaded")
        else:
            print("✓ ALL PRESENT")

        print("\n✓ All prerequisites met!\n")
        return True

    def _show_ollama_install_instructions(self) -> None:
        """Show instructions for installing Ollama."""
        system = platform.system()
        print("\n" + "!" * 60)
        print("OLLAMA NOT FOUND")
        print("!" * 60)
        print("\nOllama is required to run this application.")
        print("\nInstallation instructions:")

        if system == "Darwin":  # macOS
            print("\n  1. Visit: https://ollama.com/download")
            print("  2. Download Ollama for macOS")
            print("  3. Install and restart this application")
            print("\n  Or use Homebrew:")
            print("     brew install ollama")

        elif system == "Windows":
            print("\n  1. Visit: https://ollama.com/download")
            print("  2. Download Ollama for Windows")
            print("  3. Run the installer")
            print("  4. Restart this application")

        elif system == "Linux":
            print("\n  Run in terminal:")
            print("     curl -fsSL https://ollama.com/install.sh | sh")

        print("\n" + "!" * 60 + "\n")

    def _download_missing_models(self, missing_models: list[str]) -> bool:
        """
        Download missing models.

        Args:
            missing_models: List of model names to download

        Returns:
            True if all models downloaded successfully
        """
        print("\n  Downloading missing models...")
        for model in missing_models:
            print(f"\n  Downloading: {model}")
            if not self.ollama.pull_model(model):
                print(f"\n  ✗ Failed to download {model}")
                print("    Please check your internet connection and try again.")
                return False

        return True

    def open_browser(self, url: str = "http://localhost:8000") -> None:
        """
        Open system browser to the application URL.

        Args:
            url: URL to open
        """
        print(f"Opening browser to {url}...")
        try:
            webbrowser.open(url)
            logger.info(f"Opened browser to: {url}")
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            print(f"\nPlease open your browser manually to: {url}")

    def launch(self, open_browser: bool = True) -> bool:
        """
        Launch the desktop application.

        Args:
            open_browser: Whether to auto-open browser

        Returns:
            True if launch successful
        """
        # Check prerequisites
        if not self.check_prerequisites():
            return False

        # Show user data location
        info = self.user_data.get_storage_info()
        print(f"User data directory: {info['base_directory']}")
        print(f"PDFs folder: {info['directories']['pdfs']}")
        print("")

        # Open browser if requested
        if open_browser:
            # Give the server a moment to start
            time.sleep(2)
            self.open_browser()

        return True


def main():
    """Main entry point for desktop launcher."""
    launcher = DesktopLauncher()
    success = launcher.launch(open_browser=False)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
