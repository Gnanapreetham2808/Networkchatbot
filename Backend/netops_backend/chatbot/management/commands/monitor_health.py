import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, Set, Tuple, Optional
import logging

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.db import transaction

from netmiko import ConnectHandler

from chatbot.models import DeviceHealth, HealthAlert
from netops_backend.Devices.device_resolver import get_devices

logger = logging.getLogger(__name__)


def parse_cpu_output(vendor: str, output: str) -> float | None:
    vendor_l = (vendor or "").lower()
    # Cisco IOS: show processes cpu | include one minute
    # Common patterns: "CPU utilization for five seconds: 5%/0%; one minute: 7%; five minutes: 6%"
    if "cisco" in vendor_l or "ios" in vendor_l:
        m = re.search(r"one minute:\s*(\d+)%", output, re.I)
        if m:
            return float(m.group(1))
        # fallback: first percent
        m = re.search(r"(\d+)%", output)
        if m:
            return float(m.group(1))
        return None
    # Aruba AOS-CX: show system resource-utilization
    # Look for CPU Utilization: 23%
    if "aruba" in vendor_l or "aoscx" in vendor_l:
        m = re.search(r"CPU\s*Utilization\s*:\s*(\d+)%", output, re.I)
        if m:
            return float(m.group(1))
        # alternate tables: "CPU Utilization\s+Current\s+(\d+)%"
        m = re.search(r"CPU\s*Utilization\s+Current\s+(\d+)%", output, re.I)
        if m:
            return float(m.group(1))
        return None
    return None


def load_command_registry() -> Dict[str, Dict[str, str]]:
    """Load per-vendor command registry from JSON/YAML if provided via env.

    Environment variables:
      COMMAND_REGISTRY_PATH -> .json or .yaml/.yml file path
    Fallback to built-in defaults.
    """
    import json
    import pathlib
    import yaml  # type: ignore

    default = {
        "cisco": {
            "cpu": "show processes cpu | include one minute",
            "neighbors": "show cdp neighbors detail",
        },
        "aruba": {
            "cpu": "show system resource-utilization",
            "neighbors": "show lldp neighbors detail",
        },
    }
    p = os.getenv("COMMAND_REGISTRY_PATH")
    if not p:
        return default
    try:
        path = pathlib.Path(p)
        if not path.exists():
            return default
        if path.suffix.lower() == ".json":
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        # shallow merge on top of defaults
        out = default.copy()
        for k, v in (data or {}).items():
            if isinstance(v, dict):
                out[k.lower()] = {**out.get(k.lower(), {}), **{kk.lower(): vv for kk, vv in v.items()}}
        return out
    except Exception:
        return default


def vendor_key(dev: dict) -> str:
    v = (dev.get("vendor") or dev.get("device_type") or "").lower()
    if "cisco" in v or "ios" in v:
        return "cisco"
    if "aruba" in v or "aoscx" in v:
        return "aruba"
    return v or "cisco"


def detect_loops(neighbors_map: Dict[str, Set[str]]) -> list[tuple[str, str, list[str]]]:
    """Very simple undirected cycle detection over neighbor graph.
    Returns list of (start, end, path) for any cycle found.
    """
    seen = set()
    cycles = []

    def dfs(node, parent, path):
        seen.add(node)
        for nxt in neighbors_map.get(node, set()):
            if nxt == parent:
                continue
            if nxt in path:
                # cycle found
                idx = path.index(nxt)
                cycles.append((nxt, node, path[idx:] + [nxt]))
            elif nxt not in seen:
                dfs(nxt, node, path + [nxt])

    for n in neighbors_map.keys():
        if n not in seen:
            dfs(n, None, [n])
    return cycles


def fetch_neighbors_raw(net_conn, cmd: str) -> str:
    try:
        return net_conn.send_command(cmd, read_timeout=5)
    except Exception:
        return ""


def parse_neighbor_names(output: str) -> Set[str]:
    names = set()
    for ln in output.splitlines():
        ln = ln.strip()
        m = re.search(r"Device ID:\s*(\S+)", ln)
        if m:
            names.add(m.group(1))
            continue
        m = re.search(r"System Name:\s*(\S+)", ln)
        if m:
            names.add(m.group(1))
    return names


def map_to_known_aliases(raw_names: Set[str], devices: Dict[str, dict]) -> Set[str]:
    """Map raw neighbor names to known aliases when possible to reduce false cycles."""
    aliases = set(devices.keys())
    name_to_alias = {}
    for a, d in devices.items():
        n = (d.get("name") or a or "").strip()
        if n:
            name_to_alias[n.lower()] = a
        name_to_alias[a.lower()] = a
    mapped = set()
    for nm in raw_names:
        l = nm.lower()
        if l in name_to_alias:
            mapped.add(name_to_alias[l])
            continue
        # fuzzy contains match
        for key, alias in name_to_alias.items():
            if key and key in l:
                mapped.add(alias)
                break
    return mapped


def _now_tzaware() -> datetime:
    return datetime.utcnow()


class Command(BaseCommand):
    help = "Continuously monitor device CPU and loops; send email alerts on spikes."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=int(os.getenv("HEALTH_POLL_INTERVAL_SEC", "60")))
        parser.add_argument("--cpu-threshold", type=float, default=float(os.getenv("CPU_ALERT_THRESHOLD", "80")))
        parser.add_argument("--cpu-clear-threshold", type=float, default=float(os.getenv("CPU_CLEAR_THRESHOLD", "60")))
        parser.add_argument("--cpu-breach-consecutive", type=int, default=int(os.getenv("CPU_BREACH_CONSECUTIVE", "2")))
        parser.add_argument("--cpu-clear-consecutive", type=int, default=int(os.getenv("CPU_CLEAR_CONSECUTIVE", "2")))
        parser.add_argument("--cooldown-minutes", type=int, default=int(os.getenv("ALERT_COOLDOWN_MINUTES", "15")))
        parser.add_argument("--loop-cooldown-minutes", type=int, default=int(os.getenv("LOOP_ALERT_COOLDOWN_MINUTES", "30")))
        parser.add_argument("--max-workers", type=int, default=int(os.getenv("HEALTH_MAX_WORKERS", "4")))
        parser.add_argument("--email-to", type=str, default=os.getenv("ALERT_EMAIL_TO", ""))

    def handle(self, *args, **opts):
        interval = int(opts["interval"])
        cpu_threshold = float(opts["cpu_threshold"])
        cpu_clear_threshold = float(opts["cpu_clear_threshold"])
        breach_consecutive = int(opts["cpu_breach_consecutive"])  # trigger after N consecutive high
        clear_consecutive = int(opts["cpu_clear_consecutive"])    # clear after N consecutive low
        cooldown = timedelta(minutes=int(opts["cooldown_minutes"]))
        loop_cooldown = timedelta(minutes=int(opts["loop_cooldown_minutes"]))
        max_workers = int(opts["max_workers"]) or 4
        email_to = [e.strip() for e in str(opts["email_to"]).split(',') if e.strip()]

        devices = get_devices()
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(devices)} devices"))
        logger.info("Health monitor started", extra={
            'device_count': len(devices),
            'interval_sec': interval,
            'cpu_threshold': cpu_threshold,
            'cpu_clear_threshold': cpu_clear_threshold,
            'max_workers': max_workers
        })

        registry = load_command_registry()

        # State for debounce/hysteresis (in-memory)
        high_counts: Dict[str, int] = defaultdict(int)
        low_counts: Dict[str, int] = defaultdict(int)
        last_cpu_alert_at: Dict[str, datetime] = {}
        last_loop_sig_at: Dict[str, datetime] = {}

        def poll_one(alias: str, dev: dict) -> Tuple[str, float, str, Set[str]]:
            host = dev.get("host")
            if not host:
                return alias, -1.0, "", set()
            d_type = dev.get("device_type") or dev.get("vendor") or "cisco_ios"
            username = dev.get("username") or os.getenv("DEVICE_USERNAME", "admin")
            password = dev.get("password") or os.getenv("DEVICE_PASSWORD", "admin")
            secret = dev.get("secret") or os.getenv("DEVICE_SECRET", "")
            port = int(dev.get("port") or os.getenv("DEVICE_PORT") or 22)
            timeout_val = float(os.getenv("DEVICE_CONN_TIMEOUT", "8"))
            vkey = vendor_key(dev)
            cpu_cmd = (registry.get(vkey, {}) or {}).get("cpu") or registry["cisco"]["cpu"]
            nei_cmd = (registry.get(vkey, {}) or {}).get("neighbors") or registry["cisco"]["neighbors"]

            try:
                conn = ConnectHandler(
                    device_type=d_type,
                    host=host,
                    username=username,
                    password=password,
                    secret=secret,
                    port=port,
                    fast_cli=True,
                    timeout=timeout_val,
                )
                try:
                    out = conn.send_command(cpu_cmd, read_timeout=5)
                    cpu = parse_cpu_output(dev.get("vendor", vkey), out) or 0.0
                    neighbors_raw = fetch_neighbors_raw(conn, nei_cmd)
                    raw_names = parse_neighbor_names(neighbors_raw)
                    return alias, cpu, out[:5000], raw_names
                finally:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass
            except Exception as e:
                logger.error("Device polling failed", extra={
                    'alias': alias,
                    'host': host,
                    'error': str(e)
                }, exc_info=True)
                # return marker with failure
                return alias, -1.0, f"ERR: {e}", set()

        while True:
            # Parallel poll all devices
            futures = []
            neighbors_map: Dict[str, Set[str]] = {}
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                for alias, dev in devices.items():
                    futures.append(ex.submit(poll_one, alias, dev))
                for fut in as_completed(futures):
                    alias, cpu, raw, raw_neis = fut.result()
                    # Persist CPU sample
                    if cpu >= 0.0 or raw:
                        try:
                            with transaction.atomic():
                                DeviceHealth.objects.create(alias=alias, cpu_pct=max(cpu, 0.0), raw=(raw or "")[:5000])
                        except Exception:
                            pass

                    # CPU alerting with debounce/hysteresis
                    try:
                        if cpu < 0:
                            # connection failure -> treat as low to avoid false spikes but do not clear existing
                            low_counts[alias] += 1
                            high_counts[alias] = 0
                        elif cpu >= cpu_threshold:
                            high_counts[alias] += 1
                            low_counts[alias] = 0
                        else:
                            low_counts[alias] += 1
                            high_counts[alias] = 0

                        # Evaluate raise condition
                        if high_counts[alias] >= breach_consecutive and cpu >= cpu_threshold:
                            now = _now_tzaware()
                            last_at = last_cpu_alert_at.get(alias)
                            # Check active alert in DB
                            active = HealthAlert.objects.filter(alias=alias, category="cpu", cleared_at__isnull=True).order_by("-created_at").first()
                            if active is None or (last_at and now - last_at >= cooldown) or (active and now - active.created_at >= cooldown):
                                msg = f"CPU {cpu:.1f}% on {alias} (>= {cpu_threshold:.1f}%)"
                                try:
                                    HealthAlert.objects.create(alias=alias, category="cpu", severity="warn", message=msg)
                                    logger.warning("CPU alert raised", extra={
                                        'alias': alias,
                                        'cpu_pct': cpu,
                                        'threshold': cpu_threshold,
                                        'consecutive_breaches': high_counts[alias]
                                    })
                                finally:
                                    last_cpu_alert_at[alias] = now
                                if email_to:
                                    try:
                                        send_mail(
                                            subject=f"[NetOps] CPU spike on {alias}",
                                            message=msg,
                                            from_email=os.getenv("ALERT_EMAIL_FROM", "alerts@netops.local"),
                                            recipient_list=email_to,
                                            fail_silently=True,
                                        )
                                    except Exception:
                                        pass

                        # Evaluate clear condition
                        if low_counts[alias] >= clear_consecutive and cpu >= 0 and cpu <= cpu_clear_threshold:
                            active = HealthAlert.objects.filter(alias=alias, category="cpu", cleared_at__isnull=True).order_by("-created_at").first()
                            if active:
                                try:
                                    active.cleared_at = _now_tzaware()
                                    active.save(update_fields=["cleared_at"])
                                    logger.info("CPU alert cleared", extra={
                                        'alias': alias,
                                        'cpu_pct': cpu,
                                        'clear_threshold': cpu_clear_threshold,
                                        'consecutive_low': low_counts[alias]
                                    })
                                    if os.getenv("ALERT_EMAIL_ON_CLEAR", "1") == "1" and email_to:
                                        try:
                                            send_mail(
                                                subject=f"[NetOps] CPU cleared on {alias}",
                                                message=f"CPU back to {cpu:.1f}% on {alias} (<= {cpu_clear_threshold:.1f}%)",
                                                from_email=os.getenv("ALERT_EMAIL_FROM", "alerts@netops.local"),
                                                recipient_list=email_to,
                                                fail_silently=True,
                                            )
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    # Neighbors mapping for loop detection
                    try:
                        # map neighbor raw names to known aliases only
                        mapped = map_to_known_aliases(raw_neis, devices)
                        if mapped:
                            neighbors_map[alias] = mapped
                    except Exception:
                        pass

            # Loop detection with cooldown and dedupe
            try:
                if len(neighbors_map) >= 3:
                    cycles = detect_loops(neighbors_map)
                    now = _now_tzaware()
                    seen_any = False
                    for (_s, _e, path) in cycles[:5]:
                        seen_any = True
                        sig = "::".join(sorted(path))  # canonical signature ignoring path direction
                        last_at = last_loop_sig_at.get(sig)
                        if last_at and now - last_at < loop_cooldown:
                            continue
                        msg = f"Potential loop via: {' -> '.join(path)}"
                        try:
                            HealthAlert.objects.create(alias=path[0], category="loop", severity="warn", message=msg, meta=str(path))
                            logger.warning("Loop alert raised", extra={
                                'alias': path[0],
                                'loop_path': path,
                                'signature': sig
                            })
                        finally:
                            last_loop_sig_at[sig] = now
                        if email_to:
                            try:
                                send_mail(
                                    subject=f"[NetOps] Possible loop detected",
                                    message=msg,
                                    from_email=os.getenv("ALERT_EMAIL_FROM", "alerts@netops.local"),
                                    recipient_list=email_to,
                                    fail_silently=True,
                                )
                            except Exception:
                                pass
                    # Auto-clear previous loop alerts if no cycles now
                    if not seen_any:
                        actives = HealthAlert.objects.filter(category="loop", cleared_at__isnull=True).order_by("-created_at")
                        cleared_count = 0
                        for a in actives:
                            try:
                                a.cleared_at = now
                                a.save(update_fields=["cleared_at"])
                                cleared_count += 1
                            except Exception:
                                pass
                        if cleared_count > 0:
                            logger.info("Loop alerts auto-cleared", extra={
                                'cleared_count': cleared_count
                            })
            except Exception as e:
                logger.error("Loop detection failed", extra={'error': str(e)}, exc_info=True)

            time.sleep(interval)
