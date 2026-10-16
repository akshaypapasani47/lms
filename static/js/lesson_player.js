/* =========================================================
   C-DAC LMS — LESSON PLAYER CONTROLLER
   ========================================================= */

(function () {
    "use strict";


    function getConfig() {

        const element =
            document.getElementById(
                "lesson-player-config"
            );

        return {

            saveVideoDurationUrl:
                element?.dataset.saveVideoDurationUrl || "",

            saveProgressUrl:
                element?.dataset.saveProgressUrl || "",

            csrfToken:
                element?.dataset.csrfToken || "",
        };
    }


    function setTrackLanguage(
        video,
        language
    ) {

        if (!video?.textTracks) {
            return;
        }

        for (
            let index = 0;
            index < video.textTracks.length;
            index += 1
        ) {

            const track =
                video.textTracks[index];

            track.mode =
                track.language === language
                    ? "showing"
                    : "disabled";
        }
    }


    function updateProgress(
        progressBar,
        progressText,
        value
    ) {

        const percentage =
            Math.max(
                0,
                Math.min(
                    100,
                    Number(value) || 0
                )
            );

        if (progressBar) {

            progressBar.style.width =
                `${percentage}%`;
        }

        if (progressText) {

            progressText.textContent =
                `${percentage}%`;
        }
    }


    function postForm(
        url,
        data,
        csrfToken
    ) {

        if (!url) {

            return Promise.resolve();
        }

        return fetch(
            url,
            {
                method:
                    "POST",

                credentials:
                    "same-origin",

                headers: {

                    "X-CSRFToken":
                        csrfToken,

                    "Content-Type":
                        "application/x-www-form-urlencoded; charset=UTF-8",
                },

                body:
                    new URLSearchParams(
                        data
                    ).toString(),

                keepalive:
                    true,
            }
        ).catch(
            (error) => {

                console.debug(
                    "Lesson request failed.",
                    error
                );
            }
        );
    }


    function initVideoContainer(
        container,
        lessonId,
        savedTime,
        savedPercent,
        config
    ) {

        const video =
            container.querySelector(
                ".video-player"
            );

        if (!video) {
            return;
        }


        /*
         * IMPORTANT:
         * .video-id must remain immediately
         * before .video-container.
         */

        const videoIdElement =
            container.previousElementSibling;

        const videoId =
            videoIdElement?.classList.contains(
                "video-id"
            )
                ? videoIdElement.value
                : "";


        const audio =
            container.querySelector(
                ".dub-audio"
            );

        const languageSelect =
            container.querySelector(
                ".language-select"
            );

        const progressBar =
            container.querySelector(
                ".progressBar"
            );

        const progressText =
            container.querySelector(
                ".progressText"
            );


        let lastSavedSecond = -1;

        let durationSaved = false;


        updateProgress(
            progressBar,
            progressText,
            savedPercent
        );


        /*
         * SAVE VIDEO DURATION
         */

        video.addEventListener(
            "loadedmetadata",
            () => {

                if (
                    durationSaved ||
                    !videoId ||
                    !config.saveVideoDurationUrl ||
                    !Number.isFinite(
                        video.duration
                    )
                ) {
                    return;
                }

                durationSaved = true;


                postForm(
                    config.saveVideoDurationUrl,
                    {
                        video_id:
                            videoId,

                        duration:
                            Math.floor(
                                video.duration
                            ),
                    },
                    config.csrfToken
                );
            }
        );


        /*
         * RESUME VIDEO
         */

        video.addEventListener(
            "canplay",
            () => {

                if (
                    !savedTime ||
                    !Number.isFinite(
                        savedTime
                    )
                ) {
                    return;
                }

                if (
                    video.currentTime > 0
                ) {
                    return;
                }


                try {

                    video.currentTime =
                        Math.min(
                            savedTime,

                            Number.isFinite(
                                video.duration
                            )
                                ? video.duration
                                : savedTime
                        );

                } catch (error) {

                    console.debug(
                        "Resume position could not be restored.",
                        error
                    );
                }

            },
            {
                once: true
            }
        );


        /*
         * LANGUAGE + SUBTITLE SWITCHING
         */

        if (languageSelect) {

            languageSelect.addEventListener(
                "change",
                () => {

                    const language =
                        languageSelect.value;


                    setTrackLanguage(
                        video,
                        language
                    );


                    /*
                     * ENGLISH
                     * Original audio.
                     */

                    if (
                        language === "en"
                    ) {

                        if (audio) {

                            audio.pause();

                            audio.removeAttribute(
                                "src"
                            );

                            audio.load();
                        }

                        video.muted =
                            false;

                        return;
                    }


                    /*
                     * DUBBED AUDIO
                     */

                    const audioSource =
                        container.querySelector(
                            `.audio-source[data-lang="${CSS.escape(language)}"]`
                        );


                    if (
                        !audioSource ||
                        !audio ||
                        !audioSource.value
                    ) {

                        video.muted =
                            false;

                        return;
                    }


                    video.muted =
                        true;


                    audio.pause();

                    audio.src =
                        audioSource.value;

                    audio.load();


                    try {

                        audio.currentTime =
                            video.currentTime;

                    } catch (error) {

                        console.debug(
                            "Dubbed audio seek failed.",
                            error
                        );
                    }


                    if (
                        !video.paused
                    ) {

                        audio
                            .play()
                            .catch(
                                () => {}
                            );
                    }

                }
            );
        }


        /*
         * PLAY
         */

        video.addEventListener(
            "play",
            () => {

                if (
                    languageSelect?.value !== "en" &&
                    audio?.src
                ) {

                    try {

                        audio.currentTime =
                            video.currentTime;

                    } catch (error) {

                        console.debug(
                            "Dubbed audio sync failed.",
                            error
                        );
                    }


                    audio
                        .play()
                        .catch(
                            () => {}
                        );
                }
            }
        );


        /*
         * PAUSE
         */

        video.addEventListener(
            "pause",
            () => {

                audio?.pause();
            }
        );


        /*
         * SEEKING
         */

        video.addEventListener(
            "seeking",
            () => {

                if (!audio?.src) {
                    return;
                }


                try {

                    audio.currentTime =
                        video.currentTime;

                } catch (error) {

                    console.debug(
                        "Dubbed audio seeking failed.",
                        error
                    );
                }

            }
        );


        /*
         * TIME UPDATE
         */

        video.addEventListener(
            "timeupdate",
            () => {

                const current =
                    video.currentTime;

                const duration =
                    video.duration;


                if (
                    !Number.isFinite(
                        duration
                    ) ||
                    duration <= 0
                ) {
                    return;
                }


                /*
                 * Keep dubbed audio aligned.
                 */

                if (
                    languageSelect?.value !== "en" &&
                    audio?.src &&
                    Math.abs(
                        audio.currentTime -
                        current
                    ) > 0.25
                ) {

                    try {

                        audio.currentTime =
                            current;

                    } catch (error) {

                        console.debug(
                            "Dubbed audio resync failed.",
                            error
                        );
                    }
                }


                const percentage =
                    Math.floor(
                        (
                            current /
                            duration
                        ) * 100
                    );


                updateProgress(
                    progressBar,
                    progressText,
                    percentage
                );


                /*
                 * SAVE EVERY 5 SECONDS
                 */

                const currentSecond =
                    Math.floor(
                        current
                    );


                if (
                    currentSecond -
                        lastSavedSecond >= 5
                    ||
                    lastSavedSecond === -1
                ) {

                    lastSavedSecond =
                        currentSecond;

                    saveProgress();
                }

            }
        );


        /*
         * SAVE ON PAUSE / END
         */

        video.addEventListener(
            "pause",
            saveProgress
        );

        video.addEventListener(
            "ended",
            saveProgress
        );


        function saveProgress() {

            const current =
                video.currentTime;

            const duration =
                video.duration;


            if (
                !config.saveProgressUrl ||
                !Number.isFinite(
                    current
                ) ||
                !Number.isFinite(
                    duration
                ) ||
                duration <= 0
            ) {
                return;
            }


            const percentage =
                Math.floor(
                    (
                        current /
                        duration
                    ) * 100
                );


            updateProgress(
                progressBar,
                progressText,
                percentage
            );


            postForm(
                config.saveProgressUrl,
                {
                    lesson_id:
                        lessonId,

                    current_time:
                        current,

                    duration:
                        duration,
                },
                config.csrfToken
            );
        }
    }


    /*
     * CURRICULUM
     */

    function initCurriculum() {

        const sidebar =
            document.querySelector(
                ".course-sidebar"
            );

        if (!sidebar) {
            return;
        }


        const activeLesson =
            sidebar.querySelector(
                ".active-lesson"
            );


        if (activeLesson) {

            window.setTimeout(
                () => {

                    activeLesson.scrollIntoView(
                        {
                            behavior:
                                "smooth",

                            block:
                                "center",
                        }
                    );

                },
                350
            );
        }


        /*
         * Keyboard accessibility
         * for Bootstrap collapse buttons.
         */

        sidebar
            .querySelectorAll(
                "[data-bs-toggle='collapse']"
            )
            .forEach(
                (button) => {

                    button.setAttribute(
                        "aria-label",
                        button.textContent.trim()
                    );


                    button.addEventListener(
                        "keydown",
                        (event) => {

                            if (
                                event.key === "Enter" ||
                                event.key === " "
                            ) {

                                event.preventDefault();

                                button.click();
                            }

                        }
                    );
                }
            );
    }


    /*
     * PAGE REVEAL
     */

    function initReveal() {

        const elements =
            document.querySelectorAll(
                [
                    ".lesson-player-card",
                    ".lesson-info",
                    ".lesson-bottom-grid"
                ].join(",")
            );


        elements.forEach(
            (element, index) => {

                element.style.opacity =
                    "0";

                element.style.transform =
                    "translateY(12px)";

                element.style.transition =
                    [
                        "opacity .45s ease",
                        `${index * 70}ms`,
                        ", transform .45s ease",
                        `${index * 70}ms`
                    ].join(" ");


                requestAnimationFrame(
                    () => {

                        element.style.opacity =
                            "1";

                        element.style.transform =
                            "translateY(0)";
                    }
                );
            }
        );
    }


    /*
     * MAIN INITIALIZATION
     */

    function init() {

        const lessonInput =
            document.getElementById(
                "lesson-id"
            );

        const savedTimeInput =
            document.getElementById(
                "saved-time"
            );

        const savedPercentInput =
            document.getElementById(
                "saved-percent"
            );


        if (!lessonInput) {
            return;
        }


        const lessonId =
            lessonInput.value;


        const savedTime =
            parseFloat(
                savedTimeInput?.value || "0"
            ) || 0;


        const savedPercent =
            parseFloat(
                savedPercentInput?.value || "0"
            ) || 0;


        const config =
            getConfig();


        document
            .querySelectorAll(
                ".video-container"
            )
            .forEach(
                (container) => {

                    initVideoContainer(
                        container,
                        lessonId,
                        savedTime,
                        savedPercent,
                        config
                    );
                }
            );


        initCurriculum();

        initReveal();
    }


    /*
     * PAGE READY
     */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            () => {
                init();
                initSidebarToggle();
            }
        );

    } else {

        init();
        initSidebarToggle();
    }

})();


/* =====================================================
   COURSE CURRICULUM TOGGLE
   ===================================================== */

function initSidebarToggle() {

    const studio =
        document.querySelector(
            ".lesson-studio"
        );

    const topToggle =
        document.getElementById(
            "course-sidebar-toggle"
        );

    const closeButton =
        document.getElementById(
            "course-sidebar-close"
        );

    const sidebar =
        document.getElementById(
            "course-curriculum"
        );


    if (
        !studio ||
        !topToggle ||
        !sidebar
    ) {
        return;
    }


    const storageKey =
        "lms-course-curriculum-open";


    function updateButton(
        isOpen
    ) {

        topToggle.setAttribute(
            "aria-expanded",
            isOpen
                ? "true"
                : "false"
        );


        topToggle.setAttribute(
            "aria-label",
            isOpen
                ? "Hide course content"
                : "Show course content"
        );


        const label =
            topToggle.querySelector(
                "span"
            );


        if (label) {

            label.textContent =
                isOpen
                    ? "HIDE CONTENT"
                    : "COURSE CONTENT";
        }
    }


    function setOpen(
        isOpen,
        persist = true
    ) {

        studio.classList.toggle(
            "sidebar-collapsed",
            !isOpen
        );


        updateButton(
            isOpen
        );


        if (persist) {

            try {

                localStorage.setItem(
                    storageKey,
                    isOpen
                        ? "1"
                        : "0"
                );

            } catch (error) {

                console.debug(
                    "Could not save course sidebar state.",
                    error
                );
            }
        }
    }


    let isOpen = true;


    try {

        const saved =
            localStorage.getItem(
                storageKey
            );

        if (saved === "0") {

            isOpen = false;

        }

    } catch (error) {

        console.debug(
            "Could not read course sidebar state.",
            error
        );
    }


    setOpen(
        isOpen,
        false
    );


    const toggle = () => {

        const currentlyOpen =
            !studio.classList.contains(
                "sidebar-collapsed"
            );


        setOpen(
            !currentlyOpen
        );
    };


    topToggle.addEventListener(
        "click",
        toggle
    );


    closeButton?.addEventListener(
        "click",
        toggle
    );
}