from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call_test(func) -> None:
    kwargs = {}
    with TemporaryDirectory() as tmp_dir:
        for name in inspect.signature(func).parameters:
            if name == "tmp_path":
                kwargs[name] = Path(tmp_dir)
            else:
                raise TypeError(f"Unsupported fixture: {name}")
        func(**kwargs)


def main() -> int:
    root = Path.cwd() / "tests"
    test_files = sorted(root.glob("test_*.py"))
    total = 0
    failures: list[tuple[str, BaseException]] = []

    for path in test_files:
        module = _load_module(path)
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            total += 1
            try:
                _call_test(func)
            except BaseException as exc:  # pragma: no cover - runner behavior
                failures.append((f"{path.name}::{name}", exc))

    if failures:
        for label, exc in failures:
            print(f"FAILED {label}")
            traceback.print_exception(exc)
        print(f"\n{len(failures)} failed, {total - len(failures)} passed")
        return 1

    print(f"{total} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
