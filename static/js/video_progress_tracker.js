/**
 * Video watch progress: resume playback + periodic save (session auth + CSRF).
 * Expects <video class="js-track-progress"> with data-video-id, data-api-url, data-initial-position.
 */
(function () {
  "use strict";

  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m[2]) : "";
  }

  function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input && input.value) return input.value;
    return getCookie("csrftoken");
  }

  class VideoProgressTracker {
    /**
     * @param {HTMLVideoElement} video
     * @param {{ apiUrl: string, videoId: number, pollMs?: number }} opts
     */
    constructor(video, opts) {
      this.video = video;
      this.apiUrl = opts.apiUrl;
      this.videoId = opts.videoId;
      this.pollMs = opts.pollMs || 5000;
      this._timer = null;
    }

    start() {
      const raw = this.video.dataset.initialPosition || "0";
      const initial = parseFloat(raw);
      if (!Number.isNaN(initial) && initial > 0.5) {
        const applySeek = function () {
          try {
            if (this.video.duration && initial < this.video.duration - 0.25) {
              this.video.currentTime = initial;
            } else if (!this.video.duration) {
              this.video.currentTime = initial;
            }
          } catch (e) {}
        }.bind(this);
        this.video.addEventListener("loadedmetadata", applySeek, { once: true });
      }

      this.video.addEventListener("pause", function () {
        this._flush(false, false);
      }.bind(this));
      this.video.addEventListener("ended", function () {
        this._flush(true, false);
      }.bind(this));
      window.addEventListener("pagehide", function () {
        this._flush(false, true);
      }.bind(this));

      this._timer = window.setInterval(function () {
        this._flush(false, false);
      }.bind(this), this.pollMs);
    }

    _flush(forceEnded, useKeepalive) {
      const token = getCsrfToken();
      if (!token) return;

      const duration = this.video.duration;
      if (!duration || !Number.isFinite(duration) || duration <= 0) return;

      let position = this.video.currentTime;
      if (forceEnded) position = duration;

      const body = JSON.stringify({
        video_id: this.videoId,
        position_seconds: position,
        duration_seconds: duration,
      });

      fetch(this.apiUrl, {
        method: "POST",
        credentials: "same-origin",
        keepalive: !!useKeepalive,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": token,
          Accept: "application/json",
        },
        body: body,
      }).catch(function () {});
    }
  }

  function boot() {
    const el = document.querySelector("video.js-track-progress");
    if (!el) return;
    const apiUrl = el.dataset.apiUrl;
    const videoId = parseInt(el.dataset.videoId, 10);
    if (!apiUrl || !videoId) return;
    new VideoProgressTracker(el, { apiUrl: apiUrl, videoId: videoId }).start();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
