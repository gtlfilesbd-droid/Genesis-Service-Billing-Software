#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _host_from_dev_bind(bind: str) -> str:
    bind = (bind or '0.0.0.0:8000').strip()
    if ':' in bind:
        host, _ = bind.rsplit(':', 1)
        return host or '0.0.0.0'
    return '0.0.0.0'


def _inject_runserver_bind_if_needed():
    """Make runserver reachable on LAN: default 0.0.0.0, and port-only args (e.g. 8001) are not loopback-only."""
    bind_default = os.environ.get('DJANGO_DEV_BIND', '0.0.0.0:8000')
    default_host = _host_from_dev_bind(bind_default)
    rest = sys.argv[2:]
    if not rest:
        sys.argv.append(bind_default)
        return
    for i, token in enumerate(rest):
        if token.startswith('-'):
            continue
        # Django: "8001" alone means 127.0.0.1:8001 — rewrite so LAN IP works.
        if token.isdigit():
            sys.argv[2 + i] = f'{default_host}:{token}'
        return
    sys.argv.insert(2, bind_default)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billing_system.settings')
    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        _inject_runserver_bind_if_needed()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
