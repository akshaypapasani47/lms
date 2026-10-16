/* =========================================================
   C-DAC LMS — COURSE CATALOG
   ========================================================= */

(function () {

    "use strict";


    function initCourseCatalog() {

        const searchInput =
            document.getElementById(
                "course-search"
            );

        const semesterFilter =
            document.getElementById(
                "course-semester-filter"
            );

        const typeFilter =
            document.getElementById(
                "course-type-filter"
            );

        const cards =
            Array.from(
                document.querySelectorAll(
                    "[data-course-card]"
                )
            );

        const count =
            document.getElementById(
                "visible-course-count"
            );

        const emptyResults =
            document.getElementById(
                "catalog-empty-results"
            );


        if (!cards.length) {
            return;
        }


        function filterCourses() {

            const search =
                (
                    searchInput?.value ||
                    ""
                )
                .trim()
                .toLowerCase();


            const semester =
                semesterFilter?.value ||
                "all";


            const type =
                typeFilter?.value ||
                "all";


            let visibleCount = 0;


            cards.forEach(
                (card) => {

                    const title =
                        card.dataset.title ||
                        "";

                    const code =
                        card.dataset.code ||
                        "";

                    const cardSemester =
                        card.dataset.semester ||
                        "";

                    const cardType =
                        card.dataset.type ||
                        "";


                    const matchesSearch =
                        !search ||
                        title.includes(search) ||
                        code.includes(search);


                    const matchesSemester =
                        semester === "all" ||
                        cardSemester === semester;


                    const matchesType =
                        type === "all" ||
                        cardType === type;


                    const visible =
                        matchesSearch &&
                        matchesSemester &&
                        matchesType;


                    card.style.display =
                        visible
                            ? ""
                            : "none";


                    if (visible) {

                        visibleCount += 1;
                    }

                }
            );


            if (count) {

                count.textContent =
                    visibleCount;
            }


            if (emptyResults) {

                emptyResults.hidden =
                    visibleCount !== 0;
            }
        }


        searchInput?.addEventListener(
            "input",
            filterCourses
        );


        semesterFilter?.addEventListener(
            "change",
            filterCourses
        );


        typeFilter?.addEventListener(
            "change",
            filterCourses
        );


        filterCourses();
    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initCourseCatalog
        );

    } else {

        initCourseCatalog();
    }

})();

/* =========================================================
   ENROLLED COURSE STATE
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {
    const registry = document.getElementById("enrolled-course-registry");

    if (!registry) {
        return;
    }

    const enrolledCourses = new Set();

    registry.querySelectorAll(".enrolled-course-item").forEach(function (item) {
        const slug = item.dataset.courseSlug;

        if (slug) {
            enrolledCourses.add(slug);
        }
    });

    document.querySelectorAll("[data-course-card]").forEach(function (card) {
        const slug = card.dataset.courseSlug;

        if (!slug) {
            return;
        }

        const enrollState = card.querySelector(".course-enroll-state");
        const enrolledState = card.querySelector(".course-enrolled-state");

        if (!enrollState || !enrolledState) {
            return;
        }

        if (enrolledCourses.has(slug)) {
            enrollState.hidden = true;
            enrolledState.hidden = false;
            card.classList.add("is-enrolled");
        } else {
            enrollState.hidden = false;
            enrolledState.hidden = true;
            card.classList.remove("is-enrolled");
        }
    });
});