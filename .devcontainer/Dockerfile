FROM registry.access.redhat.com/ubi8/ubi

# Set the working directory to /app
WORKDIR /workspace

RUN dnf install -y sudo python3.11-devel python3.11-pip java-17-openjdk-headless git vim-enhanced iputils -y && \
    dnf install https://dist.neo4j.org/cypher-shell/cypher-shell-5.15.0-1.noarch.rpm -y && \
    dnf clean all && \
    pip3.11 install -U pip setuptools setuptools-rust && \
    pip3.11 install poetry 

RUN useradd user && \
    usermod -a -G wheel user && \
    echo '%wheel  ALL=(ALL)       NOPASSWD: ALL' >> /etc/sudoers.d/wheel-nopass && \
    echo 'export PS1="\[\e[32m\]\u\[\e[m\]\[\e[30m\]:\[\e[m\]\[\e[36m\]\w\[\e[m\]\[\e[30m\]\\$\[\e[m\]\[\e[30m\] \[\e[m\]"' >> /etc/profile.d/prompt.sh 

