# syntax=docker/dockerfile:1.7

FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      ccache \
      cmake \
      git \
      libboost-dev \
      libevent-dev \
      libzmq3-dev \
      pkgconf \
      python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .

ENV BITCOIN_GENBUILD_NO_GIT=1

RUN cmake -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_FLAGS_RELEASE="-O2 -g0" \
      -DBUILD_DAEMON=ON \
      -DBUILD_CLI=ON \
      -DBUILD_TX=ON \
      -DBUILD_UTIL=ON \
      -DBUILD_TESTS=OFF \
      -DBUILD_BENCH=OFF \
      -DBUILD_FUZZ_BINARY=OFF \
      -DBUILD_GUI=OFF \
      -DENABLE_WALLET=OFF \
      -DBUILD_WALLET_TOOL=OFF \
      -DWITH_ZMQ=ON \
      -DWITH_CCACHE=OFF \
      -DINSTALL_MAN=OFF \
    && cmake --build build --target bitcoind bitcoin-cli bitcoin-tx bitcoin-util -j"$(nproc)" \
    && strip build/bin/bitcoind build/bin/bitcoin-cli build/bin/bitcoin-tx build/bin/bitcoin-util

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="FracAttack Fractal node" \
      org.opencontainers.image.description="WillItMod FracAttack Fractal Bitcoin node built from WillItMod/fractal" \
      org.opencontainers.image.source="https://github.com/WillItMod/fractal" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      libboost-chrono1.83.0 \
      libboost-filesystem1.83.0 \
      libboost-program-options1.83.0 \
      libboost-thread1.83.0 \
      libevent-2.1-7t64 \
      libevent-pthreads-2.1-7t64 \
      libzmq5 \
    && groupadd -g 1000 -r bitcoin \
    && useradd -u 1000 -r -m -g bitcoin bitcoin \
    && mkdir -p /data \
    && chown bitcoin:bitcoin /data \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src/build/bin/bitcoind /usr/local/bin/bitcoind
COPY --from=builder /src/build/bin/bitcoin-cli /usr/local/bin/bitcoin-cli
COPY --from=builder /src/build/bin/bitcoin-tx /usr/local/bin/bitcoin-tx
COPY --from=builder /src/build/bin/bitcoin-util /usr/local/bin/bitcoin-util

ENV BITCOIN_VERSION=0.3.0

USER bitcoin:bitcoin
WORKDIR /data

EXPOSE 8332 8333 18332 18333

CMD ["bitcoind"]

