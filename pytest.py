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


def _resolve_targets(argv: list[str]) -> dict[Path, set[str] | None]:
    root = Path.cwd()
    tests_root = root / "tests"
    all_files = sorted(tests_root.glob("test_*.py"))
    file_map = {path.resolve(): path for path in all_files}
    by_name = {path.name: path for path in all_files}
    selected: dict[Path, set[str] | None] = {}

    if not argv:
        return {path: None for path in all_files}

    def mark(path: Path, test_name: str | None) -> None:
        existing = selected.get(path)
        if existing is None:
            if path not in selected:
                selected[path] = None if test_name is None else {test_name}
            return
        if test_name is None:
            selected[path] = None
        else:
            existing.add(test_name)

    for raw in argv:
        file_part, _, test_part = raw.partition("::")
        candidate = Path(file_part)
        resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        path = None
        if resolved in file_map:
            path = file_map[resolved]
        elif candidate.name in by_name:
            path = by_name[candidate.name]
        else:
            matches = [test_path for test_path in all_files if file_part in str(test_path)]
            if len(matches) == 1:
                path = matches[0]
        if path is None:
            raise SystemExit(f"Unknown test target: {raw}")
        mark(path, test_part or None)

    return selected


def main() -> int:
    targets = _resolve_targets(sys.argv[1:])
    test_files = sorted(targets)
    total = 0
    failures: list[tuple[str, BaseException]] = []

    for path in test_files:
        module = _load_module(path)
        wanted = targets[path]
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            if wanted is not None and name not in wanted:
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
