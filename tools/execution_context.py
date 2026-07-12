"""Immutable execution context provided to tools at invocation time.

Carries runtime environment information (workspace root, timeouts, limits)
that tools may need without coupling them to global state or hard-coded paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable snapshot of the execution environment.

    Tools receive this context when invoked by :class:`~tools.invoker.ToolInvoker`
    and can use it to resolve paths, locate resources, or access shared settings.

    Attributes
    ----------
    workspace_root:
        Absolute path to the project / workspace root directory.
        Filesystem tools resolve relative ``path`` arguments against
        this root when the supplied path is not absolute.

        This field is **required** — every invocation of a filesystem
        tool must know what directory it operates within.
    shell_timeout_seconds:
        Maximum wall-clock time (in seconds) that a shell command is
        allowed to run before being forcibly terminated.  Defaults to 30.
    grep_max_results:
        Maximum number of matches returned by the grep tool before
        results are truncated.  Defaults to 100.
    """

    workspace_root: Path
    shell_timeout_seconds: int = 30
    grep_max_results: int = 100

    def __post_init__(self) -> None:
        """Enforce that *workspace_root* is an absolute path."""
        if not self.workspace_root.is_absolute():
            raise ValueError(
                f"workspace_root must be absolute, got: {self.workspace_root}"
            )
