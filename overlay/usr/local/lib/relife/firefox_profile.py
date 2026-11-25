#!/usr/bin/python3
"""Small RAM-aware Firefox profile; security/isolation defaults stay enabled."""
import json
import os
from pathlib import Path

def preferences(memory_kib, cores):
    low_memory = memory_kib <= 3 * 1024 * 1024
    low_cpu = cores <= 2
    low = low_memory or low_cpu
    cache_kib = 8192 if memory_kib <= 1536 * 1024 else 16384 if low_memory else 32768
    return {
        "dom.ipc.processCount": 1 if low else min(4, cores),
        "dom.ipc.processCount.webIsolated": 1 if low else 2,
        "browser.cache.disk.enable": False,
        "browser.cache.memory.enable": True,
        "browser.cache.memory.capacity": cache_kib,
        "dom.ipc.processPrelaunch.enabled": not low,
        "network.http.speculative-parallel-limit": 0 if low else 6,
        "browser.sessionstore.interval": 60000 if low_memory else 30000,
        "browser.tabs.unloadOnLowMemory": True,
        "browser.newtab.preload": False,
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
    cores = len(os.sched_getaffinity(0))
    prefs = preferences(memory, cores)
    profile = Path.home() / '.mozilla/firefox/relife'
    profile.mkdir(parents=True, exist_ok=True)
    config = ''.join(f'user_pref({json.dumps(k)}, {json.dumps(v)});\n' for k, v in prefs.items())
    user_js = profile / "user.js"
    if not user_js.is_file() or user_js.read_text() != config:
        user_js.write_text(config)
    (profile / 'relife-hardware.json').write_text(json.dumps({'memory_kib': memory, 'cpus': cores, 'preferences': prefs}, indent=2))
    return str(profile)

if __name__ == '__main__':
    print(prepare())
