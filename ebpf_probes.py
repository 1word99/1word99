# eBPF Probes for Chronos Debugger


def attach_probe(process_id):
    print(f"Attaching eBPF probe to process: {process_id}")
    return True


def capture_syscalls():
    print("Capturing syscalls via eBPF...")
    return ["syscall_read", "syscall_write", "syscall_open"]
