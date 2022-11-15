FROM python:3.9.13-slim


COPY .git/ /bing-rewards/.git/
COPY /BingRewards /bing-rewards/BingRewards
COPY bing.cron /etc/cron.d/bing.cron
COPY entry.sh script.sh update.sh /bing-rewards/
RUN set -ex \
    && apt-get update --no-install-recommends -y \
    && apt-get install --no-install-recommends -y  \
    chromium \ 
    git \ 
    vim \
    nano \
    tzdata \
    cron \
    && rm -rf /var/lib/apt/lists/* \
    && touch /var/log/cron.log \
    && adduser --system nonroot \
    && chown -R nonroot /bing-rewards \
    && chmod 0777 /etc/cron.d/bing.cron \
    && chmod +x /bing-rewards/entry.sh \
    && chmod +x /bing-rewards/update.sh \
    && chmod u+s /usr/sbin/cron 	
# Set display port as an environment variable
ENV DISPLAY=:99
ENV PATH="/home/nonroot/.local/bin:${PATH}"
ENV UPDATE="0 0 */1 * *"
ENV SCH="0 */8 * * *"
ENV TZ="America/New_York"
SHELL ["/bin/bash", "-ec"]
USER nonroot
WORKDIR /bing-rewards/BingRewards
ENTRYPOINT ["/bin/bash", "/bing-rewards/entry.sh"]

