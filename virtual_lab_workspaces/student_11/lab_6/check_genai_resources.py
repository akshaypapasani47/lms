
from pathlib import Path
import os
import shutil

print("=== AI/ML RESOURCE CHECK ===")

# Workspace disk space
workspace = Path("/workspace")
usage = shutil.disk_usage(workspace)

print(f"Workspace disk total: {usage.total / (1024**3):.2f} GB")
print(f"Workspace disk free:  {usage.free / (1024**3):.2f} GB")

# Container memory, where exposed by Docker
for filename in [
    "/sys/fs/cgroup/memory.max",
    "/sys/fs/cgroup/memory/memory.limit_in_bytes",
]:
    path = Path(filename)
    if path.exists():
        value = path.read_text().strip()
        if value == "max":
            print("Container memory limit: no explicit cgroup limit reported")
        else:
            try:
                print(f"Container memory limit: {int(value) / (1024**3):.2f} GB")
            except ValueError:
                print(f"Container memory limit: {value}")
        break
else:
    print("Container memory limit: not exposed at standard cgroup paths")

# CPU availability
print(f"CPU cores visible: {os.cpu_count()}")

# Model cache locations
for name in ["HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE"]:
    print(f"{name}: {os.environ.get(name, '(default)')}")

print("\nResource check completed.")
