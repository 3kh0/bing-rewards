FROM python:3.9.13-slim


COPY bing.cron /etc/cron.d/bing.cron
COPY entry.sh /
RUN set -ex \
    && apt-get update --no-install-recommends -y \
    && apt-get install --no-install-recommends -y  \
       chromium \
       chromium-driver \ 
       git \ 
	   vim \
       nano \
       cron \
    && rm -rf /var/lib/apt/lists/* \
    && touch /var/log/cron.log \
    && adduser --system nonroot \
    && mkdir /bing-rewards \
	   /config \
	   /bing \
    && chown -R nonroot /bing-rewards \
	   /config \
	   /bing \
    && chmod 0644 /etc/cron.d/bing.cron \
    && chmod +x /entry.sh \
    && chmod u+s /usr/sbin/cron 
	
# Set display port as an environment variable
ENV DISPLAY=:99
ENV PATH="/home/nonroot/.local/bin:${PATH}"
USER nonroot
WORKDIR /bing-rewards
ENTRYPOINT ["/entry.sh"]

