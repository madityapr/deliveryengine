import asyncio
import json
import os
import sys
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from pathlib import Path
import yaml

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from antigravity.models import GravityWell, EscapeVelocityTarget, VelocityMetric, OrbitalState
from antigravity.field_mapper.mapper import FieldMapper
from antigravity.thrust_engine.engine import ThrustEngine
from antigravity.thrust_engine.registry import ThrusterRegistry
from antigravity.telemetry.db import TelemetryStore
from antigravity.telemetry.audit import AuditLogger
from antigravity.telemetry.metrics import MetricsService
from antigravity.sensors.mock import MockSensor
from antigravity.metrics import compute_escape_velocity_ratio, compute_orbital_status, compute_fix_at_k

app = typer.Typer(help="Antigravity: Friction-elimination and delivery-velocity optimization engine.")
field_app = typer.Typer(help="Inspect and rank gravitational fields and drag wells.")
thruster_app = typer.Typer(help="Manage, enable, disable, and configure thrusters.")
metrics_app = typer.Typer(help="Recompute and inspect delivery metrics.")
plugins_app = typer.Typer(help="List and inspect plugins.")
audit_app = typer.Typer(help="Inspect the immutable thrust audit log.")

app.add_typer(field_app, name="field")
app.add_typer(thruster_app, name="thruster")
app.add_typer(metrics_app, name="metrics")
app.add_typer(plugins_app, name="plugins")
app.add_typer(audit_app, name="audit")

console = Console(legacy_windows=False)
store = TelemetryStore()
audit_logger = AuditLogger(store)
registry = ThrusterRegistry()
field_mapper = FieldMapper()
metrics_service = MetricsService()


@app.command()
def bootstrap(
    profile: str = typer.Option("dev", "--profile", "-p", help="Profile to bootstrap: dev, staging, or prod"),
    scope: str = typer.Option("repo", "--scope", help="Field scope"),
    target: Optional[str] = typer.Option(None, "--target", help="Target repository or pipeline"),
):
    """Initializes default gravity field and thruster configuration."""
    console.print(f"[bold cyan]Bootstrapping Antigravity with profile:[/bold cyan] [green]{profile}[/green]")
    profile_path = Path(f"profiles/{profile}.yaml")
    
    if profile_path.exists():
        with open(profile_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        console.print(f"[dim]Loaded configuration from {profile_path}[/dim]")
        thrusters_cfg = cfg.get("thrusters", {})
        for name, tcfg in thrusters_cfg.items():
            if tcfg.get("enabled", True):
                registry.enable(name, config=tcfg)
                console.print(f"  [green]+[/green] Enabled thruster: [bold]{name}[/bold]")
    else:
        console.print(f"[yellow]Profile {profile_path} not found, applying built-in defaults.[/yellow]")
        registry.enable("test_quarantine")
        registry.enable("cache_warmer")

    # Seed mock events if store is empty
    events = store.get_raw_events(limit=10)
    if not events:
        console.print("[dim]Seeding baseline pipeline events...[/dim]")
        mock = MockSensor()
        generated = asyncio.run(mock.collect())
        for e in generated:
            store.record_raw_event(e)
        field = field_mapper.process_events(generated, scope=scope, target=target)
        store.save_wells(field.wells)
        console.print(f"[bold green]Initialized field with {len(field.wells)} gravity wells.[/bold green]")

    console.print(f"[bold green]Bootstrap completed successfully for scope '{scope}'.[/bold green]")


@field_app.command("rank")
def field_rank(
    scope: str = typer.Option("repo", "--scope", help="Field scope: repo, org, or pipeline"),
    target: Optional[str] = typer.Option("your-org/service-a", "--target", help="Target repository"),
    window: str = typer.Option("30d", "--window", help="Time window"),
    limit: int = typer.Option(10, "--limit", help="Maximum wells to show"),
):
    """Lists and ranks gravity wells by drag coefficient matching Section 5.1."""
    events = store.get_raw_events(limit=500)
    if not events:
        # Seed on demand
        mock = MockSensor()
        events = asyncio.run(mock.collect())
        for e in events:
            store.record_raw_event(e)

    field = field_mapper.process_events(events, scope=scope, target=target)
    store.save_wells(field.wells)

    table = Table(title=f"Gravity Field Ranking (Scope: {scope}, Target: {target or 'all'})", show_lines=True)
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("GravityWell", style="bold white")
    table.add_column("Drag(min/unit)", justify="right")
    table.add_column("Cd", justify="right", style="magenta")
    table.add_column("P_fail", justify="right")
    table.add_column("Trend", justify="center")

    for idx, well in enumerate(field.wells[:limit], 1):
        trend_color = "red" if "▲" in well.trend else ("green" if "▼" in well.trend else "white")
        table.add_row(
            str(idx),
            well.id,
            f"{well.drag_magnitude:.1f}",
            f"{well.drag_coefficient:.2f}",
            f"{well.p_fail:.2f}",
            f"[{trend_color}]{well.trend}[/{trend_color}]",
        )

    console.print(table)


@thruster_app.command("enable")
def thruster_enable(
    name: str = typer.Argument(..., help="Name of thruster to enable"),
    scope: str = typer.Option("repo", "--scope"),
    target: Optional[str] = typer.Option(None, "--target"),
):
    """Enables a thruster module."""
    if registry.enable(name):
        console.print(f"[bold green][+] Thruster '{name}' enabled successfully for {scope}.[/bold green]")
    else:
        console.print(f"[bold red][-] Thruster '{name}' not found.[/bold red]")


@thruster_app.command("disable")
def thruster_disable(name: str = typer.Argument(..., help="Name of thruster to disable")):
    """Disables a thruster module."""
    if registry.disable(name):
        console.print(f"[bold yellow][+] Thruster '{name}' disabled.[/bold yellow]")
    else:
        console.print(f"[bold red][-] Thruster '{name}' not found.[/bold red]")


@thruster_app.command("configure")
def thruster_configure(
    name: str = typer.Argument(..., help="Name of thruster"),
    flake_threshold: Optional[float] = typer.Option(None, "--flake-threshold"),
    window_runs: Optional[int] = typer.Option(None, "--window-runs"),
    max_queue_depth: Optional[int] = typer.Option(None, "--max-queue-depth"),
):
    """Updates thruster parameters."""
    cfg = {}
    if flake_threshold is not None:
        cfg["flake_threshold"] = flake_threshold
    if window_runs is not None:
        cfg["window_runs"] = window_runs
    if max_queue_depth is not None:
        cfg["max_queue_depth"] = max_queue_depth

    if registry.enable(name, config=cfg):
        console.print(f"[bold green][+] Thruster '{name}' configured with:[/bold green] {cfg}")
    else:
        console.print(f"[bold red][-] Thruster '{name}' not found.[/bold red]")


@app.command("orbital-state")
def orbital_state(
    scope: str = typer.Option("org", "--scope", help="org, repo, or pipeline"),
    target: Optional[str] = typer.Option(None, "--target"),
    output_format: str = typer.Option("table", "--format", help="table or json"),
):
    """Displays current delivery velocity and escape velocity ratio."""
    target_deploys = float(os.getenv("EVT_DEFAULT_DEPLOYS_PER_DAY", "3.0"))
    target_lead_time = float(os.getenv("EVT_DEFAULT_LEAD_TIME_HOURS", "4.0"))
    cur_deploys = 2.1
    cur_lead_time = 6.4

    evr = compute_escape_velocity_ratio(cur_deploys, target_deploys)
    status = compute_orbital_status(evr)

    saved_wells = store.get_saved_wells(limit=5)
    top_drag = [w.id for w in saved_wells[:2]] if saved_wells else ["ci.integration-tests", "review.approval-queue"]

    state = {
        "scope": scope,
        "current_velocity": {
            "deploys_per_day": cur_deploys,
            "lead_time_hours": cur_lead_time,
        },
        "escape_velocity_target": {
            "deploys_per_day": target_deploys,
            "lead_time_hours": target_lead_time,
        },
        "escape_velocity_ratio": evr,
        "status": status.value,
        "top_drag_contributors": top_drag,
    }

    if output_format.lower() == "json":
        console.print_json(json.dumps(state))
    else:
        table = Table(title=f"Orbital State ({scope})", show_header=False, show_lines=True)
        table.add_column("Property", style="bold cyan")
        table.add_column("Value")

        status_color = "green" if status == "ESCAPE" else ("yellow" if status == "APPROACHING" else "red")

        table.add_row("Status", f"[{status_color}]{status.value}[/{status_color}]")
        table.add_row("Escape Velocity Ratio (EVR)", f"[bold]{evr:.2f}[/bold] (target ≥ 1.0)")
        table.add_row(
            "Current Velocity",
            f"{cur_deploys} deploys/day, {cur_lead_time}h lead time",
        )
        table.add_row(
            "Target Velocity",
            f"{target_deploys} deploys/day, {target_lead_time}h lead time",
        )
        table.add_row("Top Drag Contributors", ", ".join(top_drag))
        console.print(table)


@metrics_app.command("recompute")
def metrics_recompute(
    metric: str = typer.Option("fix_at_k", "--metric", "-m", help="Metric to recompute: fix_at_k or osi"),
    n: int = typer.Option(200, "-n", help="Total trials"),
    c: int = typer.Option(150, "-c", help="Successful trials"),
):
    """Recomputes a batch metric (e.g. Fix@k) using unbiased estimators."""
    res = metrics_service.recompute_metric(metric, n=n, c=c)
    console.print(f"[bold cyan]Recomputed metric: {metric}[/bold cyan]")
    console.print_json(json.dumps(res))


@plugins_app.command("list")
def plugins_list():
    """Lists discovered sensor and thruster plugins."""
    table = Table(title="Installed Antigravity Plugins", show_lines=True)
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="bold white")
    table.add_column("Status / Scope", style="green")

    table.add_row("Sensor", "mock", "Built-in (synthetic collector)")
    table.add_row("Sensor", "github", "Built-in (GitHub Actions)")
    
    for t in registry.list_all():
        status = "[green]Enabled[/green]" if t.enabled else "[red]Disabled[/red]"
        table.add_row("Thruster", t.name, f"{status} (write_scope: {t.write_scope})")

    console.print(table)


@audit_app.command("log")
def audit_log(
    limit: int = typer.Option(20, "--limit", help="Number of records to show"),
    since: Optional[str] = typer.Option(None, "--since", help="Timestamp filter"),
):
    """Displays records from the immutable thrust audit log."""
    logs = audit_logger.get_logs(limit=limit, since=since)
    if not logs:
        console.print("[dim]Audit log is currently empty.[/dim]")
        return

    table = Table(title="Immutable Thrust Audit Log", show_lines=True)
    table.add_column("Timestamp", style="dim")
    table.add_column("Thruster", style="bold cyan")
    table.add_column("Well ID")
    table.add_column("Action", style="green")
    table.add_column("Δv", justify="right", style="magenta")
    table.add_column("Status")

    for r in logs:
        table.add_row(
            r["timestamp"][:19],
            r["thruster"],
            r["well_id"],
            r["action"],
            f"+{r['delta_v']:.1f}",
            r["status"],
        )

    console.print(table)


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="API Host"),
    port: int = typer.Option(8000, "--port", help="API Port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Starts the FastAPI web server locally."""
    import uvicorn
    console.print(f"[bold green]Starting Antigravity API server on http://{host}:{port}[/bold green]")
    console.print(f"[dim]Web Dashboard available at http://{host}:{port}/dashboard[/dim]")
    uvicorn.run("antigravity.api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
