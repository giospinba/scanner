from pathlib import Path

from scannerpy import SystemScanner


def test_report_contains_expected_checks(tmp_path: Path):
    scanner = SystemScanner(path_to_check=tmp_path)
    report = scanner.run_all_checks()

    names = {c.name for c in report.checks}
    assert "Python version" in names
    assert "Filesystem access" in names
    assert "Disk usage" in names
    assert "Network DNS" in names
    assert "Tooling" in names


def test_disk_threshold_warning(tmp_path: Path):
    scanner = SystemScanner(
        path_to_check=tmp_path,
        disk_warn_threshold=0.0,
        disk_critical_threshold=1.1,
    )
    result = scanner.check_disk_space()
    assert result.status == "warning"


def test_disk_threshold_critical(tmp_path: Path):
    scanner = SystemScanner(
        path_to_check=tmp_path,
        disk_warn_threshold=0.0,
        disk_critical_threshold=0.0,
    )
    result = scanner.check_disk_space()
    assert result.status == "critical"
