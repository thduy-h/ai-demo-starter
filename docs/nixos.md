# Native NixOS execution

Native execution was verified on NixOS 26.05 x86_64 with CPython 3.11.16. This includes all three real CPU model pipelines, live Gradio HTTP requests, isolated dependency profiles, and a clean pip wheel installation. No `/etc/nixos` or other system configuration was modified.

```bash
nix-shell
uv sync --locked --all-extras
uv run aidemo list
```

The supplied `shell.nix` provides Python 3.11, uv, FFmpeg, and an LD_LIBRARY_PATH containing the compiler C++ runtime and zlib. Without it, manylinux NumPy/Torch/CTranslate2 imports can fail with `libstdc++.so.6` missing. Enter this shell before invoking Python from `.venv`, including for installed-wheel verification. No `/usr/bin` dependency is assumed by the library.

The shell uses the host's `<nixpkgs>` and is not a pinned Nix flake; the Python dependency graph is locked, but the entire native system environment is not. The tested uv is 0.11.21. Other NixOS releases, architectures, GPU drivers, and Python ABIs remain unverified. If native wheels are incompatible on another host, a Linux container is an alternative; the provided Docker image could not be built/run in this session because no daemon is available.

A restricted agent sandbox may prohibit socket creation and appear to cause DNS failures. That is separate from Nix native library compatibility. In this verification environment the Nix shell execution context had working DNS/TLS and loopback sockets. Do not change host DNS or proxy settings to work around an execution-policy restriction.
