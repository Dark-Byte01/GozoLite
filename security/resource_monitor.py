from __future__ import annotations
import os, resource, time
from typing import Dict, Any, Optional

def snapshot_rusage() -> Dict[str, Any]:
    # rusage del proceso actual (aprox para tu runner por subprocess)
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "utime_s": ru.ru_utime,
        "stime_s": ru.ru_stime,
        "max_rss_kb": ru.ru_maxrss,  # en Linux KB, en macOS bytes/1024
        "minor_faults": ru.ru_minflt,
        "major_faults": ru.ru_majflt,
        "inblock": ru.ru_inblock,
        "oublock": ru.ru_oublock,
    }

def diff_usage(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in after:
        if isinstance(after[k], (int, float)) and k in before:
            out[k] = after[k] - before[k]
    return out