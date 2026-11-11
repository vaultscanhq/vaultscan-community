from vaultscan.secrets import is_ignored, redact, scan_line, scan_path, shannon_entropy

# Fake credentials assembled at runtime so this file never trips a scanner.
AWS_KEY = "AKIA" + "IOSFODNN7QWERTYU"
GH_TOKEN = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"


def rules(findings):
    return {f.rule_id for f in findings}


def test_detects_aws_key_and_redacts_it():
    findings = scan_line(f'aws_access_key_id = "{AWS_KEY}"', "a.tf", 3)
    assert "SEC-001" in rules(findings)
    assert AWS_KEY not in findings[0].detail
    assert findings[0].location == "a.tf:3"


def test_detects_github_token():
    assert "SEC-003" in rules(scan_line(f"export GH={GH_TOKEN}", "a.sh", 1))


def test_database_url_with_password():
    line = "DATABASE_URL=postgres://app:s3cr3tpw@db.internal:5432/app"
    assert "SEC-009" in rules(scan_line(line, ".env", 1))


def test_placeholders_are_not_reported():
    assert scan_line('api_key = "your_api_key_goes_here_1234"', "a.py", 1) == []
    assert scan_line('password: "${DB_PASSWORD_FROM_VAULT}"', "a.yml", 1) == []


def test_inline_ignore_comment():
    assert scan_line(f'key = "{AWS_KEY}"  # vaultscan:ignore', "a.py", 1) == []


def test_entropy_detector_catches_unknown_secret_format():
    line = 'session_secret = "q9Zx7Lm2Vb8Kp4Wd6Rt1Yh3Nc5Jf0Gs"'
    found = rules(scan_line(line, "settings.py", 1))
    assert found & {"SEC-100", "SEC-013"}


def test_entropy_values():
    assert shannon_entropy("aaaaaaaa") == 0
    assert shannon_entropy("q9Zx7Lm2Vb8Kp4Wd6Rt1Yh3Nc5Jf0Gs") > 4.2


def test_redact_keeps_only_edges():
    assert redact("abcdefghijklmnop") == "abcd********op"
    assert redact("short") == "*****"


def test_ignore_patterns():
    assert is_ignored("node_modules/pkg/index.js", ["node_modules/"])
    assert is_ignored("docs/logo.png", ["*.png"])
    assert not is_ignored("src/tests_helper.py", ["tests/"])


def test_scan_path_respects_ignore_file(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "vendor").mkdir()
    (tmp_path / "app" / "config.py").write_text(f'KEY = "{AWS_KEY}"\n')
    (tmp_path / "vendor" / "lib.py").write_text(f'KEY = "{AWS_KEY}"\n')
    (tmp_path / ".vaultscanignore").write_text("vendor/\n")
    findings = scan_path(str(tmp_path))
    assert [f.file.replace("\\", "/") for f in findings] == ["app/config.py"]
