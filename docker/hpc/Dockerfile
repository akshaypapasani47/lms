FROM lms-virtual-lab:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    util-linux \
    nano \
    vim-tiny \
    less \
    file \
    findutils \
    grep \
    sed \
    gawk \
    tar \
    gzip \
    zip \
    unzip \
    wget \
    curl \
    git \
    ca-certificates \
    build-essential \
    gcc \
    g++ \
    gfortran \
    make \
    cmake \
    pkg-config \
    openmpi-bin \
    libopenmpi-dev \
    time \
    procps \
    htop \
    iproute2 \
    dnsutils \
    man-db \
    manpages \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["/bin/bash"]
