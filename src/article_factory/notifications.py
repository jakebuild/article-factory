"""Progress notifications for async pipeline execution."""

import sys


def notify_progress(task_id: str, stage: str, progress_percent: int, message: str = None) -> None:
    """Print progress update to stdout.
    
    Args:
        task_id: The task ID
        stage: Current pipeline stage name
        progress_percent: Progress percentage (0-100)
        message: Optional progress message
    """
    progress_bar = get_progress_bar(progress_percent)
    msg = message or ""
    print(f"[{task_id[:8]}...] {progress_bar} {stage}: {msg} ({progress_percent}%)", flush=True)


def notify_complete(task_id: str, output_dir: str, stages_completed: int = 8) -> None:
    """Print completion message.
    
    Args:
        task_id: The task ID
        output_dir: Output directory path
        stages_completed: Number of stages completed
    """
    print(f"\n[OK] Task {task_id[:8]}... completed successfully!", flush=True)
    print(f"   Output: {output_dir}", flush=True)
    print(f"   Stages: {stages_completed} completed", flush=True)


def notify_error(task_id: str, error: str, stage: str = None) -> None:
    """Print error message.
    
    Args:
        task_id: The task ID
        error: Error message
        stage: Stage where error occurred
    """
    stage_info = f" at {stage}" if stage else ""
    print(f"\n[ERROR] Task {task_id[:8]}... failed{stage_info}:", flush=True)
    print(f"   {error}", flush=True)
    print(f"\n   To retry: article-factory run <topic-id>", flush=True)


def notify_cancelled(task_id: str) -> None:
    """Print cancellation confirmation.
    
    Args:
        task_id: The task ID
    """
    print(f"\n[STOPPED] Task {task_id[:8]}... cancelled", flush=True)


def get_progress_bar(progress_percent: int) -> str:
    """Generate ASCII progress bar.
    
    Args:
        progress_percent: Progress percentage (0-100)
        
    Returns:
        Progress bar string like "[██████░░░░] XX%"
    """
    # Clamp to 0-100
    progress = max(0, min(100, progress_percent))
    
    # 10 blocks for 0-100
    filled = int(progress / 10)
    empty = 10 - filled
    
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {progress:3d}%"
