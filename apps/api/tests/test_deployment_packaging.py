"""Step 15 production packaging and safe-exposure contract tests."""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INFRA = PROJECT_ROOT / "infra"


def production_compose() -> dict[str, object]:
    return yaml.safe_load((INFRA / "docker-compose.pi.yml").read_text())


def test_pi_compose_has_only_one_explicit_lan_entry_point() -> None:
    compose = production_compose()
    services = compose["services"]
    assert set(services) == {"db", "migrate", "api", "web"}
    assert "ports" not in services["db"]
    assert "ports" not in services["api"]
    assert services["web"]["ports"] == [
        "${LAN_BIND_ADDRESS:?LAN_BIND_ADDRESS must be the Pi private LAN IP}:"
        "${DASHBOARD_PORT:-8080}:80"
    ]
    assert compose["networks"]["backend"]["internal"] is True
    assert set(services["web"]["networks"]) == {"edge", "backend"}
    assert services["api"]["networks"] == ["backend"]
    assert services["db"]["networks"] == ["backend"]


def test_pi_compose_has_arm64_health_restart_volume_and_log_contracts() -> None:
    compose = production_compose()
    services = compose["services"]
    for name in ("db", "api", "web"):
        service = services[name]
        assert service["platform"] == "${TARGET_PLATFORM:-linux/arm64}"
        assert service["healthcheck"]["test"]
        assert service["restart"] == "unless-stopped"
        assert service["logging"] == {
            "driver": "json-file",
            "options": {"max-size": "10m", "max-file": "3"},
        }
        assert service["security_opt"] == ["no-new-privileges:true"]
        assert service["init"] is True
    assert services["db"]["volumes"] == [
        "postgres_data:/var/lib/postgresql/data"
    ]
    assert "postgres_data" in compose["volumes"]
    assert services["api"]["read_only"] is True
    assert services["web"]["read_only"] is True


def test_production_images_are_multi_stage_and_nginx_serves_the_build() -> None:
    api_dockerfile = (PROJECT_ROOT / "apps/api/Dockerfile").read_text()
    web_dockerfile = (PROJECT_ROOT / "apps/web/Dockerfile").read_text()
    nginx = (INFRA / "nginx.production.conf").read_text()

    assert api_dockerfile.count("FROM ") >= 2
    assert " AS builder" in api_dockerfile
    assert " AS runtime" in api_dockerfile
    assert "USER 10001:10001" in api_dockerfile

    assert web_dockerfile.count("FROM ") >= 4
    assert "FROM --platform=$BUILDPLATFORM ${NODE_IMAGE} AS dependencies" in (
        web_dockerfile
    )
    assert " AS build" in web_dockerfile
    assert "RUN npm run build" in web_dockerfile
    assert " AS production" in web_dockerfile
    assert "COPY --from=build /app/dist /usr/share/nginx/html" in web_dockerfile

    assert "try_files $uri $uri/ /index.html" in nginx
    assert "proxy_pass http://energy_api" in nginx
    assert "proxy_set_header Upgrade $http_upgrade" in nginx
    assert "location = /nginx-health" in nginx


def test_pi_environment_and_runbook_keep_operations_explicit() -> None:
    environment_example = (INFRA / ".env.pi.example").read_text()
    runbook = (PROJECT_ROOT / "docs/operations.md").read_text()
    scripts = {
        path.name: path.read_text()
        for path in (INFRA / "scripts").glob("*.sh")
    }

    assert sum("=CHANGE_ME" in line for line in environment_example.splitlines()) == 4
    assert "LAN_BIND_ADDRESS=CHANGE_ME_PRIVATE_LAN_IP" in environment_example
    assert "TARGET_PLATFORM=linux/arm64" in environment_example
    assert "SIMULATOR_ENABLED=false" in environment_example

    for heading in (
        "initial setup",
        "migrations",
        "administrator",
        "Backup",
        "Restore into a clean volume",
        "Upgrade",
        "Rollback",
        "Reboot verification",
        "physical power-interruption testing",
    ):
        assert heading.lower() in runbook.lower()

    assert set(scripts) == {
        "backup.sh",
        "crash-recovery-drill.sh",
        "integrity-check.sh",
        "pi-preflight.sh",
        "prepare-demo.sh",
        "restore-drill.sh",
    }
    assert "--confirm-abrupt-db-stop" in scripts["crash-recovery-drill.sh"]
    assert "restore-drill" in scripts["restore-drill.sh"]
    assert "Refusing to overwrite" in scripts["backup.sh"]
    assert "docker buildx version" in scripts["pi-preflight.sh"]
    assert "DOCKER_BUILDKIT" in scripts["pi-preflight.sh"]
    assert "Refusing to prepare the demonstration" in scripts["prepare-demo.sh"]
    assert "Scenario.SUDDEN_OVERCONSUMPTION" in scripts["prepare-demo.sh"]


def test_development_compose_selects_non_production_web_target() -> None:
    development = yaml.safe_load((INFRA / "docker-compose.yml").read_text())
    assert development["services"]["api"]["build"]["target"] == "runtime"
    assert development["services"]["web"]["build"]["target"] == "development"
