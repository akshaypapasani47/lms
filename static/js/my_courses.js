/* =========================================================
   C-DAC LMS — MY COURSES
   SINGLE CARD CAROUSEL
   CIRCULAR NAVIGATION
   ========================================================= */

(function () {

    "use strict";


    function initMyCoursesCarousel() {

        const track =
            document.getElementById("my-learning-track");

        const prevButton =
            document.getElementById("my-learning-prev");

        const nextButton =
            document.getElementById("my-learning-next");

        const dotsContainer =
            document.getElementById("my-learning-dots");


        /*
         * -----------------------------------------------------
         * SAFETY CHECK
         * -----------------------------------------------------
         */

        if (!track) {
            return;
        }


        const cards = Array.from(
            track.querySelectorAll(
                ".my-learning-course-card"
            )
        );


        if (!cards.length) {
            return;
        }


        /*
         * -----------------------------------------------------
         * STATE
         * -----------------------------------------------------
         */

        let currentIndex = 0;

        let isAnimating = false;


        /*
         * -----------------------------------------------------
         * CREATE DOTS
         * -----------------------------------------------------
         */

        let dots = [];


        if (dotsContainer) {

            dotsContainer.innerHTML = "";


            cards.forEach(function (_, index) {

                const dot =
                    document.createElement("button");


                dot.type = "button";


                dot.className =
                    "my-learning-carousel-dot";


                dot.setAttribute(
                    "aria-label",
                    "Go to course " + (index + 1)
                );


                dot.dataset.slide =
                    index;


                dot.addEventListener(
                    "click",
                    function () {

                        if (isAnimating) {
                            return;
                        }


                        goToSlide(
                            index,
                            index > currentIndex
                                ? "next"
                                : "prev"
                        );

                    }
                );


                dotsContainer.appendChild(
                    dot
                );

            });


            dots = Array.from(
                dotsContainer.querySelectorAll(
                    ".my-learning-carousel-dot"
                )
            );

        }


        /*
         * -----------------------------------------------------
         * UPDATE CAROUSEL
         * -----------------------------------------------------
         */

        function updateCarousel(
            direction
        ) {

            const total =
                cards.length;


            const nextIndex =
                (
                    currentIndex + 1
                ) % total;


            const previousIndex =
                (
                    currentIndex - 1 + total
                ) % total;


            /*
             * Remove existing state classes.
             */

            cards.forEach(
                function (card) {

                    card.classList.remove(
                        "is-active",
                        "is-next",
                        "is-prev",
                        "is-hidden"
                    );

                }
            );


            /*
             * ACTIVE
             */

            cards[currentIndex]
                .classList.add(
                    "is-active"
                );


            cards[currentIndex]
                .setAttribute(
                    "aria-hidden",
                    "false"
                );


            /*
             * NEXT
             */

            if (cards.length > 1) {

                cards[nextIndex]
                    .classList.add(
                        "is-next"
                    );


                cards[nextIndex]
                    .setAttribute(
                        "aria-hidden",
                        "true"
                    );

            }


            /*
             * PREVIOUS
             */

            if (cards.length > 1) {

                cards[previousIndex]
                    .classList.add(
                        "is-prev"
                    );


                cards[previousIndex]
                    .setAttribute(
                        "aria-hidden",
                        "true"
                    );

            }


            /*
             * ALL OTHER CARDS
             */

            cards.forEach(
                function (card, index) {

                    if (
                        index !== currentIndex &&
                        index !== nextIndex &&
                        index !== previousIndex
                    ) {

                        card.classList.add(
                            "is-hidden"
                        );


                        card.setAttribute(
                            "aria-hidden",
                            "true"
                        );

                    }

                }
            );


            /*
             * UPDATE DOTS
             */

            dots.forEach(
                function (dot, index) {

                    dot.classList.toggle(
                        "active",
                        index === currentIndex
                    );

                }
            );


            /*
             * Update accessibility.
             */

            cards.forEach(
                function (card, index) {

                    if (
                        index === currentIndex
                    ) {

                        card.setAttribute(
                            "tabindex",
                            "0"
                        );

                    } else {

                        card.setAttribute(
                            "tabindex",
                            "-1"
                        );

                    }

                }
            );


            /*
             * Allow next interaction
             * after the visual transition.
             */

            window.setTimeout(
                function () {

                    isAnimating = false;

                },
                580
            );

        }


        /*
         * -----------------------------------------------------
         * GO TO SLIDE
         * -----------------------------------------------------
         */

        function goToSlide(
            index,
            direction = "next"
        ) {

            if (!cards.length) {
                return;
            }


            if (cards.length === 1) {

                currentIndex = 0;

                updateCarousel(
                    direction
                );

                return;
            }


            /*
             * Normalize index.
             */

            currentIndex =
                (
                    index + cards.length
                ) % cards.length;


            /*
             * Add direction to track.
             */

            track.classList.remove(
                "slide-next",
                "slide-prev"
            );


            track.classList.add(
                direction === "prev"
                    ? "slide-prev"
                    : "slide-next"
            );


            updateCarousel(
                direction
            );

        }


        /*
         * -----------------------------------------------------
         * NEXT
         * -----------------------------------------------------
         *
         * Normal:
         *
         * 1 -> 2
         * 2 -> 3
         *
         * Circular:
         *
         * 3 -> 1
         *
         * -----------------------------------------------------
         */

        function nextSlide() {

            if (isAnimating) {
                return;
            }


            isAnimating = true;


            const lastIndex =
                cards.length - 1;


            /*
             * LAST -> FIRST
             *
             * Reset instantly.
             */

            if (
                currentIndex === lastIndex
            ) {

                track.classList.add(
                    "carousel-no-transition"
                );


                currentIndex = 0;


                updateCarousel(
                    "next"
                );


                /*
                 * Force layout.
                 */

                void track.offsetWidth;


                window.requestAnimationFrame(
                    function () {

                        track.classList.remove(
                            "carousel-no-transition"
                        );

                        isAnimating = false;

                    }
                );


                return;
            }


            /*
             * Normal next.
             */

            goToSlide(
                currentIndex + 1,
                "next"
            );

        }


        /*
         * -----------------------------------------------------
         * PREVIOUS
         * -----------------------------------------------------
         *
         * Normal:
         *
         * 3 -> 2
         * 2 -> 1
         *
         * Circular:
         *
         * 1 -> 3
         *
         * -----------------------------------------------------
         */

        function previousSlide() {

            if (isAnimating) {
                return;
            }


            isAnimating = true;


            /*
             * FIRST -> LAST
             *
             * Reset instantly.
             */

            if (
                currentIndex === 0
            ) {

                track.classList.add(
                    "carousel-no-transition"
                );


                currentIndex =
                    cards.length - 1;


                updateCarousel(
                    "prev"
                );


                void track.offsetWidth;


                window.requestAnimationFrame(
                    function () {

                        track.classList.remove(
                            "carousel-no-transition"
                        );

                        isAnimating = false;

                    }
                );


                return;
            }


            /*
             * Normal previous.
             */

            goToSlide(
                currentIndex - 1,
                "prev"
            );

        }


        /*
         * -----------------------------------------------------
         * NEXT BUTTON
         * -----------------------------------------------------
         */

        if (nextButton) {

            nextButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    nextSlide();

                }
            );

        }


        /*
         * -----------------------------------------------------
         * PREVIOUS BUTTON
         * -----------------------------------------------------
         */

        if (prevButton) {

            prevButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    previousSlide();

                }
            );

        }


        /*
         * -----------------------------------------------------
         * TOUCH SWIPE
         * -----------------------------------------------------
         */

        let touchStartX = 0;

        let touchCurrentX = 0;

        let touchActive = false;


        track.addEventListener(
            "touchstart",
            function (event) {

                if (
                    !event.touches ||
                    !event.touches.length
                ) {

                    return;

                }


                touchStartX =
                    event.touches[0].clientX;


                touchCurrentX =
                    touchStartX;


                touchActive = true;

            },
            {
                passive: true
            }
        );


        track.addEventListener(
            "touchmove",
            function (event) {

                if (
                    !touchActive ||
                    !event.touches ||
                    !event.touches.length
                ) {

                    return;

                }


                touchCurrentX =
                    event.touches[0].clientX;

            },
            {
                passive: true
            }
        );


        track.addEventListener(
            "touchend",
            function () {

                if (!touchActive) {
                    return;
                }


                const difference =
                    touchCurrentX -
                    touchStartX;


                const threshold = 50;


                if (
                    Math.abs(difference) >=
                    threshold
                ) {

                    if (
                        difference < 0
                    ) {

                        nextSlide();

                    } else {

                        previousSlide();

                    }

                }


                touchActive = false;

            }
        );


        /*
         * -----------------------------------------------------
         * KEYBOARD NAVIGATION
         * -----------------------------------------------------
         */

        document.addEventListener(
            "keydown",
            function (event) {

                const activeElement =
                    document.activeElement;


                const tagName =
                    activeElement &&
                    activeElement.tagName
                        ? activeElement.tagName
                            .toLowerCase()
                        : "";


                /*
                 * Don't interfere with form fields.
                 */

                if (
                    tagName === "input" ||
                    tagName === "textarea" ||
                    tagName === "select"
                ) {

                    return;

                }


                if (
                    event.key === "ArrowRight"
                ) {

                    event.preventDefault();

                    nextSlide();

                }


                if (
                    event.key === "ArrowLeft"
                ) {

                    event.preventDefault();

                    previousSlide();

                }

            }
        );


        /*
         * -----------------------------------------------------
         * INITIAL STATE
         * -----------------------------------------------------
         */

        cards.forEach(
            function (card) {

                card.setAttribute(
                    "aria-hidden",
                    "true"
                );

                card.setAttribute(
                    "tabindex",
                    "-1"
                );

            }
        );


        updateCarousel(
            "next"
        );

    }


    /*
     * ========================================================
     * DOM READY
     * ========================================================
     */

    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initMyCoursesCarousel
        );

    } else {

        initMyCoursesCarousel();

    }

})();