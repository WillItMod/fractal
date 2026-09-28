# syntax=docker/dockerfile:1.7

FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown
ARG BUILD_JOBS=2

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
      -DBUILD_TESTS=ON \
      -DBUILD_BENCH=OFF \
      -DBUILD_FUZZ_BINARY=OFF \
      -DBUILD_GUI=OFF \
      -DENABLE_WALLET=OFF \
      -DBUILD_WALLET_TOOL=OFF \
      -DWITH_ZMQ=ON \
      -DWITH_CCACHE=OFF \
      -DINSTALL_MAN=OFF \
    && cmake --build build --target bitcoind bitcoin-cli bitcoin-tx bitcoin-util test_bitcoin -j"${BUILD_JOBS}" \
    && build/bin/test_bitcoin --run_test=validation_tests --log_level=test_suite \
    && strip build/bin/bitcoind build/bin/bitcoin-cli build/bin/bitcoin-tx build/bin/bitcoin-util

FROM ubuntu:24.04 AS runtime-base

ARG DEBIAN_FRONTEND=noninteractive
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="FracAttack Fractal node" \
      org.opencontainers.image.description="WillItMod FracAttack Fractal Bitcoin node built from WillItMod/fractal" \
      org.opencontainers.image.source="https://github.com/WillItMod/fractal" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="0.4.0" \
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
      libevent-extra-2.1-7t64 \
      libevent-pthreads-2.1-7t64 \
      libzmq5 \
    && mkdir -p /data \
    && chown 1000:1000 /data \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src/build/bin/bitcoind /usr/local/bin/bitcoind
COPY --from=builder /src/build/bin/bitcoin-cli /usr/local/bin/bitcoin-cli
COPY --from=builder /src/build/bin/bitcoin-tx /usr/local/bin/bitcoin-tx
COPY --from=builder /src/build/bin/bitcoin-util /usr/local/bin/bitcoin-util

ENV BITCOIN_VERSION=0.4.0

USER 1000:1000
WORKDIR /data

EXPOSE 28342 28343 28345

CMD ["bitcoind"]

# Test the installed, stripped runtime binaries. Python and the test framework
# stay in this disposable stage rather than the published runtime image.
FROM runtime-base AS consensus-test
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /src/test/functional/test_framework /src/test/functional/test_framework
COPY --from=builder /src/test/functional/feature_fractal_subsidy.py /src/test/functional/feature_fractal_subsidy.py
COPY --from=builder /src/build/test/config.ini /src/test/config.ini
USER 1000:1000
RUN BITCOIND=/usr/local/bin/bitcoind BITCOINCLI=/usr/local/bin/bitcoin-cli BITCOINUTIL=/usr/local/bin/bitcoin-util \
      python3 /src/test/functional/feature_fractal_subsidy.py --cachedir=/tmp/consensus-cache \
    && printf '%s\n' 'daemon=0.4.0' 'passed=validation_tests,feature_fractal_subsidy' > /tmp/consensus-validation.txt

FROM runtime-base AS runtime
COPY --from=consensus-test /tmp/consensus-validation.txt /usr/local/share/fracattack/consensus-validation.txt
