"""Authentication handling for NotebookLM via article-factory CLI."""

import json
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

AUTH_STORAGE_PATH = Path.home() / ".article-factory" / "storage_state.json"
BROWSER_PROFILE_PATH = Path.home() / ".article-factory" / "browser_profile"


def ensure_auth_dirs():
    """Create authentication directories with proper permissions."""
    AUTH_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    BROWSER_PROFILE_PATH.mkdir(parents=True, exist_ok=True, mode=0o700)


def login():
    """Log in to NotebookLM via browser.

    Opens a browser window for Google login. After logging in,
    press ENTER in the terminal to save authentication.

    The authentication is saved to ~/.article-factory/storage_state.json
    and article-factory will automatically use it for all commands.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("[red]Error: Playwright not installed.[/red]")
        print("Run: pip install \"notebooklm-py[browser]\"")
        print("     playwright install chromium")
        return False

    if os.environ.get("NOTEBOOKLM_AUTH_JSON"):
        print("[red]Error: Cannot run login when NOTEBOOKLM_AUTH_JSON is set.[/red]")
        print("Either unset NOTEBOOKLM_AUTH_JSON or use inline authentication.")
        return False

    ensure_auth_dirs()

    print("[yellow]Opening browser for Google login...[/yellow]")
    print(f"[dim]Using storage: {AUTH_STORAGE_PATH}[/dim]")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE_PATH),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--password-store=basic",
            ],
            ignore_default_args=["--enable-automation"],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://notebooklm.google.com/")

        print("\n[bold green]Instructions:[/bold green]")
        print("1. Complete the Google login in the browser window")
        print("2. Wait until you see the NotebookLM homepage")
        print("3. Press [bold]ENTER[/bold] here to save and close\n")

        input("[Press ENTER when logged in] ")

        current_url = page.url
        if "notebooklm.google.com" not in current_url:
            print(f"[yellow]Warning: Current URL is {current_url}[/yellow]")
            if not input("Save authentication anyway? (y/n): ").lower().startswith("y"):
                context.close()
                return False

        context.storage_state(path=str(AUTH_STORAGE_PATH))
        AUTH_STORAGE_PATH.chmod(0o600)
        context.close()

    print(f"\n[green]Authentication saved to:[/green] {AUTH_STORAGE_PATH}")
    return True


def get_auth_path() -> Path:
    """Get the path to the authentication storage file."""
    ensure_auth_dirs()
    return AUTH_STORAGE_PATH


def check_auth_status():
    """Check if authentication is configured."""
    if os.environ.get("NOTEBOOKLM_AUTH_JSON"):
        return {"status": "inline", "source": "NOTEBOOKLM_AUTH_JSON env var"}

    if AUTH_STORAGE_PATH.exists():
        return {"status": "configured", "path": str(AUTH_STORAGE_PATH)}

    return {"status": "not_configured"}


def export_auth_json() -> str:
    """Export authentication JSON for use in NOTEBOOKLM_AUTH_JSON."""
    if os.environ.get("NOTEBOOKLM_AUTH_JSON"):
        return os.environ.get("NOTEBOOKLM_AUTH_JSON")

    if AUTH_STORAGE_PATH.exists():
        return AUTH_STORAGE_PATH.read_text()

    return ""


def configure_env_var():
    """Print export command for NOTEBOOKLM_AUTH_JSON."""
    auth_json = export_auth_json()
    if auth_json:
        print(f"\n# Add to your shell profile (.zshrc, .bashrc, etc.):")
        print(f'export NOTEBOOKLM_AUTH_JSON=\'{auth_json}\'')
    else:
        print("\nNo authentication found. Run 'article-factory login' first.")
