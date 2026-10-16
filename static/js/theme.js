(function () {

    const THEME_KEY = "lms-theme";


    /* =========================================================
       GET CURRENT THEME
       ========================================================= */

    function getCurrentTheme() {

        return document.documentElement.getAttribute("data-theme")
            || localStorage.getItem(THEME_KEY)
            || "light";

    }


    /* =========================================================
       UPDATE THEME BUTTON
       ========================================================= */

    function updateThemeButton(theme) {

        const button = document.getElementById("theme-toggle");

        if (!button) {
            return;
        }

        const icon = button.querySelector(".theme-icon");

        if (!icon) {
            return;
        }


        /* Remove old animation styles */
        icon.style.transition =
            "transform 0.35s ease, opacity 0.25s ease";


        if (theme === "dark") {

            /* =============================================
               DARK MODE
               Show SUN
               ============================================= */

            icon.className = "fas fa-sun theme-icon";

            button.setAttribute(
                "aria-label",
                "Switch to light theme"
            );

            button.setAttribute(
                "title",
                "Switch to light theme"
            );


        } else {

            /* =============================================
               LIGHT MODE
               Show MOON
               ============================================= */

            icon.className = "fas fa-moon theme-icon";

            button.setAttribute(
                "aria-label",
                "Switch to dark theme"
            );

            button.setAttribute(
                "title",
                "Switch to dark theme"
            );

        }

    }


    /* =========================================================
       APPLY THEME
       ========================================================= */

    function applyTheme(theme) {

        /* Update actual HTML theme */
        document.documentElement.setAttribute(
            "data-theme",
            theme
        );

        /* Save theme */
        localStorage.setItem(
            THEME_KEY,
            theme
        );

        /* IMPORTANT:
           Synchronize button with actual theme */
        updateThemeButton(theme);

    }


    /* =========================================================
       TOGGLE THEME
       ========================================================= */

    function toggleTheme() {

        /*
         * IMPORTANT:
         * Read the ACTUAL current theme from <html>
         */

        const currentTheme =
            document.documentElement.getAttribute("data-theme")
            || "light";


        const newTheme =
            currentTheme === "dark"
                ? "light"
                : "dark";


        const button =
            document.getElementById("theme-toggle");

        const icon =
            button
                ? button.querySelector(".theme-icon")
                : null;


        /* =============================================
           ICON OUT ANIMATION
           ============================================= */

        if (icon) {

            icon.style.transition =
                "transform 0.2s ease, opacity 0.2s ease";

            icon.style.transform =
                "scale(0.3) rotate(180deg)";

            icon.style.opacity = "0";

        }


        /* =============================================
           CHANGE THEME
           ============================================= */

        setTimeout(function () {

            applyTheme(newTheme);


            /* =============================================
               NEW ICON
               ============================================= */

            if (icon) {

                icon.style.transition = "none";

                icon.style.transform =
                    "scale(0.3) rotate(-180deg)";

                icon.style.opacity = "0";


                /* Force browser reflow */
                void icon.offsetWidth;


                /* =========================================
                   ICON IN ANIMATION
                   ========================================= */

                icon.style.transition =
                    "transform 0.35s ease, opacity 0.25s ease";

                icon.style.transform =
                    "scale(1) rotate(0deg)";

                icon.style.opacity = "1";

            }

        }, 180);

    }


    /* =========================================================
       INITIALIZE THEME
       ========================================================= */

    function initializeTheme() {

        /*
         * Get saved theme
         */

        const savedTheme =
            localStorage.getItem(THEME_KEY) || "light";


        /*
         * Apply theme to HTML
         */

        document.documentElement.setAttribute(
            "data-theme",
            savedTheme
        );


        /*
         * IMPORTANT:
         * Synchronize button with saved theme
         */

        updateThemeButton(savedTheme);

    }


    /* =========================================================
       MAKE FUNCTIONS GLOBAL
       ========================================================= */

    window.toggleTheme = toggleTheme;

    window.applyTheme = applyTheme;


    /* =========================================================
       PAGE LOAD
       ========================================================= */

    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initializeTheme
        );

    } else {

        initializeTheme();

    }

})();