#!/usr/bin/python3
"""Small RAM-aware Firefox profile; security/isolation defaults stay enabled."""
import json
import os
from pathlib import Path

def preferences(memory_kib, cores):
    low = memory_kib <= 3 * 1024 * 1024 or cores <= 2
    return {
        "dom.ipc.processCount": 2 if low else min(4, cores),
        "dom.ipc.processCount.webIsolated": 1 if low else 2,
        "browser.cache.disk.enable": False,
        "browser.cache.memory.enable": True,
        "browser.cache.memory.capacity": 16384 if low else 32768,
        "browser.sessionstore.interval": 60000,
        "browser.sessionstore.restore_on_demand": True,
        "browser.tabs.warnOnClose": True,
        "browser.newtabpage.enabled": False,
        "browser.startup.homepage": "file:///usr/share/relife/start.html",
        "browser.startup.page": 1,
        "browser.shell.checkDefaultBrowser": False,
        "general.smoothScroll": False,
        "ui.prefersReducedMotion": 1,
        "media.autoplay.default": 5,
        "network.prefetch-next": False,
        "network.dns.disablePrefetch": True,
        "network.predictor.enabled": False,
    }

def prepare():
    memory = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal:')))
    prefs = preferences(memory, os.cpu_count() or 1)
    profile = Path.home() / '.mozilla/firefox/relife'
    profile.mkdir(parents=True, exist_ok=True)
    (profile / 'user.js').write_text(''.join(f'user_pref({json.dumps(k)}, {json.dumps(v)});\n' for k, v in prefs.items()))
    (profile / 'relife-hardware.json').write_text(json.dumps({'memory_kib': memory, 'cpus': os.cpu_count(), 'preferences': prefs}, indent=2))
    return str(profile)

if __name__ == '__main__':
    print(prepare())
