/* =========================================================
   C-DAC LMS — CORE HOME DASHBOARD
   ========================================================= */

(function () {

    "use strict";


    function updateClock() {

        const clock =
            document.getElementById(
                "lms-live-clock"
            );


        if (!clock) {
            return;
        }


        const now =
            new Date();


        clock.textContent =
            now.toLocaleTimeString(
                [],
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: false
                }
            );
    }


    function init() {

        updateClock();


        window.setInterval(
            updateClock,
            1000
        );
    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            init
        );

    } else {

        init();
    }


})();