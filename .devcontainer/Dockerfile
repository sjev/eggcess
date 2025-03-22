
FROM python:3.11
ARG USERNAME=dev
ARG UID=1000
ARG GID=1000
ARG PROJECT=eggcess


# Create the user
RUN groupadd --gid $GID $USERNAME \
    && useradd --uid $UID --gid $GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# dialout group
RUN usermod -a -G dialout $USERNAME

# install packages
RUN apt-get install -y \
    locales \
    mc \
    tree \
    git \
    make \
    wget \
    libusb-1.0-0 \
    net-tools \
    iproute2 \
    iputils-ping

# cleanup
RUN rm -rf /var/lib/apt/lists/*

# set locale
RUN export LC_ALL=en_US.UTF-8
RUN export LANG=en_US.UTF-8
RUN locale-gen en_US.UTF-8

RUN pip install --upgrade pip

# install user packages
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt && rm requirements.txt


USER ${USERNAME}
RUN echo 'export PS1="🐳  \[\033[1;36m\]'"${PROJECT}"' \[\e[33m\]\W\[\e[m\] \[\033[1;36m\]# \[\033[0m\]"' >> ~/.bashrc

ENV PATH="${PATH}:/home/${USERNAME}/.local/bin"

WORKDIR /home/${USERNAME}


# setup folders for saving vscode extensions
# https://code.visualstudio.com/remote/advancedcontainers/avoid-extension-reinstalls
RUN mkdir -p /home/$USERNAME/.vscode-server/extensions \
    && chown -R $USERNAME \
    /home/$USERNAME/.vscode-server


# build timestamp
USER root
RUN echo ${PROJECT} >> /build_date.txt && \
    date >> /build_date.txt

USER ${USERNAME}
WORKDIR /home/${USERNAME}


# get adafruit libraries
RUN circup show
