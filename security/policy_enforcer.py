from __future__ import annotations
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

# Límites “duros” a nivel payload.
DEF_MAX_TIMEOUT = int(os.getenv("SEC_MAX_TIMEOUT", "15"))    # s
DEF_MAX_MEM_MB  = int(os.getenv("SEC_MAX_MEMORY_MB", "512")) # MB
MIN_TIMEOUT     = 1
MIN_MEM_MB      = 32

@dataclass
class Policy:
    timeout: int
    memory_mb: int
    network: str            # "none"|"egress"|"allow"
    read_only_fs: bool
    drop_caps_all: bool
    no_new_privs: bool
    pids_limit: int
    files_limit: int

def clamp(val: int, lo: int, hi: int) -> int:
    return max(lo, min(val, hi))

def build_policy(request_timeout: Optional[int], request_mem_mb: Optional[int]) -> Policy:
    t  = int(request_timeout or DEF_MAX_TIMEOUT)
    mb = int(request_mem_mb or DEF_MAX_MEM_MB)
    return Policy(
        timeout   = clamp(t, MIN_TIMEOUT, DEF_MAX_TIMEOUT),
        memory_mb = clamp(mb, MIN_MEM_MB, DEF_MAX_MEM_MB),
        network   = "none",
        read_only_fs = True,
        drop_caps_all = True,
        no_new_privs  = True,
        pids_limit    = 128,
        files_limit   = 2048,
    )

def policy_dict(p: Policy) -> Dict[str, Any]:
    return asdict(p)