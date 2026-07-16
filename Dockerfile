FROM python:3.10-slim

ARG INCLUDE_VDR=false

# Install Node 18
RUN apt-get update && apt-get install -y curl gnupg
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

ARG LOADDIR="/load-agent"
ENV TZ=America/Denver

# Timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# System dependencies
RUN apt-get update -y && apt-get install -y \
    curl gcc g++ make git libssl-dev pkg-config \
    libsodium-dev libzmq3-dev python3-pip tmux htop

RUN corepack enable
RUN corepack prepare yarn@stable --activate

# Rust / Indy setup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Python / Locust
RUN pip3 install --upgrade pip
RUN pip3 install pdm

# Copy Python dependency files to root
WORKDIR /
COPY pyproject.toml ./
COPY pdm.lock ./
RUN pdm sync --no-self

# JS agent dependencies (cached separately)
WORKDIR ${LOADDIR}
COPY ./load-agent/package.json ./load-agent/yarn.lock ./load-agent/.yarnrc.yml ./
RUN yarn install

# App code (only source, not yarn.lock/package.json which are already installed)
COPY ./load-agent/agent.ts ./load-agent/tsconfig.json ./load-agent/config.js \
     ./load-agent/constants.py ./load-agent/locustClient.py \
     ./load-agent/portmanager.py ./load-agent/settings.py ./
COPY ./load-agent/agents ./agents/
COPY ./load-agent/locust-files ./locust-files/
COPY ./load-agent/models ./models/
COPY ./load-agent/networks ./networks/
COPY ./load-agent/tests ./tests/

# Conditionally copy vdr proxy code
COPY ./load-vdr-proxy /tmp/load-vdr-proxy
RUN if [ "$INCLUDE_VDR" = "true" ]; then \
        mkdir -p /load-vdr-proxy; \
        cp -r /tmp/load-vdr-proxy/* /load-vdr-proxy/; \
    fi

# Build JS agent
RUN yarn tsc

# Default command
CMD ["locust"]
