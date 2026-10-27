{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.python311 pkgs.uv pkgs.ffmpeg ];
  # manylinux wheels require the C++ runtime; no global NixOS changes are needed.
  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib ]}:''${LD_LIBRARY_PATH:-}"
    export UV_CACHE_DIR="$PWD/.local/uv-cache"
    export GRADIO_ANALYTICS_ENABLED=False
    export HF_HUB_DISABLE_TELEMETRY=1
  '';
}
