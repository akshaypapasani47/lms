(function () {

    "use strict";


    /* =====================================================
       SCROLL REVEAL
       ===================================================== */

    function initializeRevealAnimations() {

        const elements = document.querySelectorAll(
            ".landing-page .reveal"
        );

        if (!elements.length) {
            return;
        }

        const observer = new IntersectionObserver(
            function (entries) {

                entries.forEach(function (entry) {

                    if (entry.isIntersecting) {

                        entry.target.classList.add("show");

                        observer.unobserve(entry.target);
                    }

                });

            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -50px 0px"
            }
        );


        elements.forEach(function (element) {

            observer.observe(element);

        });

    }


    /* =====================================================
       PROGRAM CARD 3D TILT
       ===================================================== */

    function initializeProgramTilt() {

        const cards = document.querySelectorAll(
            ".program-card"
        );


        cards.forEach(function (card) {

            card.addEventListener(
                "mousemove",
                function (event) {

                    if (window.innerWidth < 992) {
                        return;
                    }

                    const rect = card.getBoundingClientRect();

                    const x =
                        event.clientX - rect.left;

                    const y =
                        event.clientY - rect.top;


                    const centerX =
                        rect.width / 2;

                    const centerY =
                        rect.height / 2;


                    const rotateX =
                        ((y - centerY) / centerY) * -5;

                    const rotateY =
                        ((x - centerX) / centerX) * 5;


                    card.style.transform =
                        "translateY(-12px) " +
                        "rotateX(" + rotateX + "deg) " +
                        "rotateY(" + rotateY + "deg)";

                }
            );


            card.addEventListener(
                "mouseleave",
                function () {

                    card.style.transform = "";

                }
            );

        });

    }


    /* =====================================================
       ABOUT CARD 3D TILT
       ===================================================== */

    function initializeAboutTilt() {

        const cards = document.querySelectorAll(
            ".about-card"
        );


        cards.forEach(function (card) {

            card.addEventListener(
                "mousemove",
                function (event) {

                    if (window.innerWidth < 992) {
                        return;
                    }

                    const rect =
                        card.getBoundingClientRect();


                    const x =
                        event.clientX - rect.left;

                    const y =
                        event.clientY - rect.top;


                    const rotateX =
                        ((y / rect.height) - 0.5) * -4;

                    const rotateY =
                        ((x / rect.width) - 0.5) * 4;


                    card.style.transform =
                        "translateY(-12px) " +
                        "rotateX(" + rotateX + "deg) " +
                        "rotateY(" + rotateY + "deg)";

                }
            );


            card.addEventListener(
                "mouseleave",
                function () {

                    card.style.transform = "";

                }
            );

        });

    }


    /* =====================================================
       HERO CAROUSEL ANIMATION
       ===================================================== */

    function initializeHeroCarousel() {

        const slider =
            document.getElementById("lmsSlider");


        if (!slider) {
            return;
        }


        slider.addEventListener(
            "slide.bs.carousel",
            function () {

                const heroContent =
                    slider.querySelector(".hero-content");


                if (!heroContent) {
                    return;
                }


                heroContent.classList.remove(
                    "hero-content-refresh"
                );


                void heroContent.offsetWidth;


                heroContent.classList.add(
                    "hero-content-refresh"
                );

            }
        );

    }


    /* =====================================================
       INITIALIZE
       ===================================================== */

    function initializeLandingPage() {

        initializeRevealAnimations();

        initializeProgramTilt();

        initializeAboutTilt();

        initializeHeroCarousel();

    }


    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initializeLandingPage
        );

    } else {

        initializeLandingPage();

    }

})();