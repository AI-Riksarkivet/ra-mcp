# HuggingFace Spaces image.
#
# The Riksarkivet/lance storage bucket is mounted at /data through a Xet FUSE layer.
# Serving LanceDB queries directly off that mount fails under load: os error 5 (EIO) on
# concurrent random reads, os error 95 on Lance's atomic-rename commit. Instead we copy
# each dataset from the mount onto the Space's writable ephemeral disk (/data-local,
# ~50 GB on free CPU-basic) once at boot, then read locally. The bucket stays mounted at
# /data as the source of truth; no HF token or download is involved.
#
# RA_MCP_STAGE_DATASETS=1      enable boot-time staging (see ra_mcp_common.datasets)
# RA_MCP_STAGE_DIR=/data-local writable target on the ephemeral disk
# RA_MCP_STAGE_ONLY=a,b        (optional) only stage these datasets
FROM riksarkivet/ra-mcp:v0.16.3

USER root
RUN mkdir -p /data-local && chown ra-mcp:ra-mcp /data-local
USER ra-mcp

ENV RA_MCP_STAGE_DATASETS="1" \
    RA_MCP_STAGE_DIR="/data-local"

# htr is excluded: htr_transcribe proxies the ZeroGPU HTR demo Space, whose
# anonymous quota is instantly exhausted in production, so every call fails.
CMD ["ra-serve", "--http", "--host", "0.0.0.0", "--port", "7860", "--modules", "search,browse,guide,viewer,pdf,diplomatics,sbl,sjomanshus,filmcensur,rosenberg,court,aktiebolag,faltjagare,suffrage,specialsok,dds,wincars,sj,tora"]
