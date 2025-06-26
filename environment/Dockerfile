# hash:sha256:7cc78a626b486fb64b58da231df955c73bfed15a59b381f16a51eec8657de191
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/mambaforge3:24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U --no-cache-dir \
    aind-data-schema \
    contraqctor \
    -e git+https://github.com/AllenNeuralDynamics/Aind.Behavior.VrForaging.git@feat-add-data-contract#egg=aind-behavior-vr-foraging
