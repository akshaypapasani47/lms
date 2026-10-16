(function () {

    "use strict";


    /* =====================================================
       HERO MOUSE INTERACTION
       ===================================================== */

    const hero =
        document.querySelector(".hpc-hero");


    if (hero) {

        const visual =
            hero.querySelector(".hpc-visual");


        if (visual && window.innerWidth > 991) {

            hero.addEventListener(
                "mousemove",
                function (event) {

                    const rect =
                        hero.getBoundingClientRect();


                    const mouseX =
                        (event.clientX - rect.left)
                        / rect.width;


                    const mouseY =
                        (event.clientY - rect.top)
                        / rect.height;


                    const moveX =
                        (mouseX - 0.5) * 18;


                    const moveY =
                        (mouseY - 0.5) * 18;


                    visual.style.transform =
                        "translate(" +
                        moveX +
                        "px, " +
                        moveY +
                        "px) scale(0.95)";

                }
            );


            hero.addEventListener(
                "mouseleave",
                function () {

                    visual.style.transform =
                        "translate(0, 0) scale(0.95)";

                }
            );

        }

    }


    /* =====================================================
       PLATFORM CORE
       ===================================================== */

    const platform =
        document.querySelector(
            ".platform-core-section"
        );


    /*
     * If the page does not contain Platform Core,
     * simply stop here.
     */

    if (!platform) {
        return;
    }


    const modules =
        platform.querySelectorAll(
            ".platform-module"
        );


    const core =
        platform.querySelector(
            ".platform-core-node"
        );


    const connections =
        platform.querySelectorAll(
            ".platform-connection"
        );


    /* =====================================================
       PLATFORM REVEAL
       ===================================================== */

    let platformRevealed = false;


    function revealPlatform() {

        /*
         * Prevent the animation from running twice.
         */

        if (platformRevealed) {
            return;
        }


        platformRevealed = true;


        platform.classList.add(
            "platform-visible"
        );


        /*
         * Reveal the four modules one by one.
         */

        modules.forEach(
            function (module, index) {

                setTimeout(
                    function () {

                        module.classList.add(
                            "is-visible"
                        );

                    },
                    150 + (index * 180)
                );

            }
        );


        /*
         * Reveal the connection lines
         * after the modules begin appearing.
         */

        connections.forEach(
            function (connection, index) {

                setTimeout(
                    function () {

                        connection.classList.add(
                            "connection-visible"
                        );

                    },
                    850 + (index * 180)
                );

            }
        );

    }


    /* =====================================================
       INTERSECTION OBSERVER
       ===================================================== */

    if (
        "IntersectionObserver"
        in window
    ) {

        const observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(
                        function (entry) {

                            if (
                                entry.isIntersecting
                            ) {

                                revealPlatform();

                                observer.disconnect();

                            }

                        }
                    );

                },
                {
                    threshold: 0.15
                }
            );


        observer.observe(platform);

    } else {

        /*
         * Browser fallback.
         */

        revealPlatform();

    }


    /* =====================================================
       MODULE HOVER EFFECT
       ===================================================== */

    modules.forEach(
        function (module) {


            module.addEventListener(
                "mousemove",
                function (event) {

                    /*
                     * Disable 3D effect on smaller screens.
                     */

                    if (
                        window.innerWidth < 992
                    ) {
                        return;
                    }


                    const rect =
                        module.getBoundingClientRect();


                    const x =
                        event.clientX -
                        rect.left;


                    const y =
                        event.clientY -
                        rect.top;


                    const centerX =
                        rect.width / 2;


                    const centerY =
                        rect.height / 2;


                    const rotateX =
                        ((y - centerY)
                            / centerY) * -2;


                    const rotateY =
                        ((x - centerX)
                            / centerX) * 2;


                    module.style.transform =
                        "translateY(-6px) " +
                        "perspective(700px) " +
                        "rotateX(" +
                        rotateX +
                        "deg) " +
                        "rotateY(" +
                        rotateY +
                        "deg)";

                }
            );


            module.addEventListener(
                "mouseleave",
                function () {

                    module.style.transform =
                        "translateY(0)";

                }
            );

        }
    );


    /* =====================================================
       CENTRAL CORE INTERACTION
       ===================================================== */

    if (core) {

        platform.addEventListener(
            "mousemove",
            function (event) {

                if (
                    window.innerWidth < 992
                ) {
                    return;
                }


                const rect =
                    platform.getBoundingClientRect();


                const x =
                    (
                        event.clientX -
                        rect.left
                    ) / rect.width;


                const y =
                    (
                        event.clientY -
                        rect.top
                    ) / rect.height;


                const moveX =
                    (x - 0.5) * 10;


                const moveY =
                    (y - 0.5) * 10;


                core.style.marginLeft =
                    moveX + "px";


                core.style.marginTop =
                    moveY + "px";

            }
        );


        platform.addEventListener(
            "mouseleave",
            function () {

                core.style.marginLeft =
                    "0px";


                core.style.marginTop =
                    "0px";

            }
        );

    }


})();



/* =========================================================
   VIRTUAL COMPUTE ENVIRONMENT
   ========================================================= */

(function () {
    "use strict";

    const computeSection =
        document.querySelector(".virtual-compute-section");

    if (!computeSection) {
        return;
    }


    /* =====================================================
       RESOURCE BAR ANIMATION
       ===================================================== */

    const resourceBars =
        computeSection.querySelectorAll(".resource-fill");

    let resourcesAnimated = false;

    function animateResourceBars() {

        if (resourcesAnimated) {
            return;
        }

        resourcesAnimated = true;

        resourceBars.forEach(function (bar) {

            const value = bar.getAttribute("data-value");

            if (!value) {
                return;
            }

            bar.style.width = "0%";

            requestAnimationFrame(function () {

                requestAnimationFrame(function () {

                    bar.style.width = value + "%";

                });

            });

        });
    }


    /* =====================================================
       WORKLOAD PROGRESS ANIMATION
       ===================================================== */

    const jobProgressBar =
        computeSection.querySelector(".job-progress-bar span");

    let jobAnimated = false;

    function animateJobProgress() {

        if (jobAnimated || !jobProgressBar) {
            return;
        }

        jobAnimated = true;

        jobProgressBar.style.width = "0%";

        requestAnimationFrame(function () {

            requestAnimationFrame(function () {

                jobProgressBar.style.width = "82%";

            });

        });
    }


    /* =====================================================
       INTERSECTION OBSERVER
       ===================================================== */

    if ("IntersectionObserver" in window) {

        const observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(function (entry) {

                        if (entry.isIntersecting) {

                            animateResourceBars();
                            animateJobProgress();

                            observer.unobserve(
                                computeSection
                            );
                        }

                    });

                },
                {
                    threshold: 0.25
                }
            );

        observer.observe(computeSection);

    } else {

        // Fallback for older browsers
        animateResourceBars();
        animateJobProgress();

    }


    /* =====================================================
       TERMINAL ACTIVITY
       ===================================================== */

    const terminalRunning =
        computeSection.querySelector(".terminal-running");

    if (terminalRunning) {

        const runningText =
            terminalRunning.lastChild;

        if (runningText) {

            let dots = 0;

            setInterval(function () {

                dots = (dots + 1) % 4;

                const text =
                    "Executing workload" +
                    ".".repeat(dots);

                if (
                    runningText.nodeType ===
                    Node.TEXT_NODE
                ) {

                    runningText.textContent =
                        text;

                }

            }, 650);

        }

    }


    /* =====================================================
       TERMINAL CURSOR
       ===================================================== */

    const terminalCursor =
        computeSection.querySelector(".terminal-cursor");

    if (terminalCursor) {

        terminalCursor.classList.add(
            "compute-terminal-active"
        );

    }


    /* =====================================================
       RESOURCE VALUE MICRO EFFECT
       ===================================================== */

    resourceBars.forEach(function (bar) {

        const block =
            bar.closest(".resource-block");

        if (!block) {
            return;
        }

        block.addEventListener(
            "mouseenter",
            function () {

                bar.style.filter =
                    "brightness(1.25)";

            }
        );

        block.addEventListener(
            "mouseleave",
            function () {

                bar.style.filter =
                    "brightness(1)";

            }
        );

    });


    /* =====================================================
       COMPUTE NODE STATUS
       ===================================================== */

    const nodeStatus =
        computeSection.querySelector(".node-status");

    if (nodeStatus) {

        setInterval(function () {

            nodeStatus.classList.toggle(
                "compute-status-pulse"
            );

        }, 2200);

    }


})();


/* =========================================================
   LEARNING PIPELINE
   ========================================================= */

(function () {
    "use strict";

    const pipeline =
        document.querySelector(".learning-pipeline-section");

    if (!pipeline) {
        return;
    }


    /* =====================================================
       PIPELINE NODES
       ===================================================== */

    const nodes =
        pipeline.querySelectorAll(".pipeline-node");

    if (!nodes.length) {
        return;
    }


    /* =====================================================
       ACTIVE NODE SEQUENCE
       ===================================================== */

    let currentNode = 0;
    let pipelineStarted = false;
    let pipelineTimer = null;


    function activateNode(index) {

        nodes.forEach(function (node, nodeIndex) {

            if (nodeIndex === index) {
                node.classList.add("pipeline-node-live");
            } else {
                node.classList.remove("pipeline-node-live");
            }

        });

    }


    function startPipeline() {

        if (pipelineStarted) {
            return;
        }

        pipelineStarted = true;

        activateNode(0);

        pipelineTimer = setInterval(function () {

            currentNode++;

            if (currentNode >= nodes.length) {
                currentNode = 0;
            }

            activateNode(currentNode);

        }, 1800);

    }


    /* =====================================================
       STOP PIPELINE WHEN NOT VISIBLE
       ===================================================== */

    function stopPipeline() {

        if (!pipelineStarted) {
            return;
        }

        clearInterval(pipelineTimer);

        pipelineTimer = null;
        pipelineStarted = false;
    }


    /* =====================================================
       INTERSECTION OBSERVER
       ===================================================== */

    if ("IntersectionObserver" in window) {

        const observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(function (entry) {

                        if (entry.isIntersecting) {

                            startPipeline();

                        } else {

                            stopPipeline();

                        }

                    });

                },
                {
                    threshold: 0.25
                }
            );

        observer.observe(pipeline);

    } else {

        startPipeline();

    }


    /* =====================================================
       NODE HOVER
       ===================================================== */

    nodes.forEach(function (node) {

        node.addEventListener(
            "mouseenter",
            function () {

                nodes.forEach(function (item) {
                    item.classList.remove(
                        "pipeline-node-hover"
                    );
                });

                node.classList.add(
                    "pipeline-node-hover"
                );

            }
        );

        node.addEventListener(
            "mouseleave",
            function () {

                node.classList.remove(
                    "pipeline-node-hover"
                );

            }
        );

    });


    /* =====================================================
       CLEANUP
       ===================================================== */

    window.addEventListener(
        "beforeunload",
        function () {

            clearInterval(pipelineTimer);

        }
    );

})();



/* =========================================================
   CODE EXECUTION ENGINE ANIMATION
   ========================================================= */

(function () {
    "use strict";

    const engine =
        document.querySelector(".code-engine-section");

    if (!engine) {
        return;
    }


    const codeLines =
        engine.querySelectorAll(".code-line");

    const outputLines =
        engine.querySelectorAll(".output-line");

    const outputResult =
        engine.querySelector(".output-result");

    const outputComplete =
        engine.querySelector(".output-complete");

    const runButton =
        engine.querySelector(".execution-run-button");

    const stateText =
        engine.querySelector(".execution-state-text");

    const stateDot =
        engine.querySelector(".execution-state-dot");

    const runtimeValue =
        engine.querySelector(
            ".execution-metrics strong"
        );

    if (!codeLines.length || !runButton) {
        return;
    }


    let executionTimer = null;
    let executionRunning = false;
    let hasStarted = false;


    /* =====================================================
       RESET EXECUTION
       ===================================================== */

    function resetExecution() {

        clearTimeout(executionTimer);

        executionRunning = false;

        codeLines.forEach(function (line) {

            line.classList.remove(
                "code-line-executing",
                "code-line-complete"
            );

        });


        outputLines.forEach(function (line) {

            line.classList.remove(
                "output-line-visible"
            );

        });


        if (outputResult) {

            outputResult.classList.remove(
                "output-result-visible"
            );

        }


        if (outputComplete) {

            outputComplete.classList.remove(
                "output-complete-visible"
            );

        }


        if (stateText) {

            stateText.textContent =
                "READY TO EXECUTE";

        }


        if (stateDot) {

            stateDot.classList.remove(
                "execution-running"
            );

        }


        if (runtimeValue) {

            runtimeValue.textContent =
                "0.82s";

        }

    }


    /* =====================================================
       EXECUTE CODE LINES
       ===================================================== */

    function executeCode() {

        if (executionRunning) {
            return;
        }

        executionRunning = true;

        hasStarted = true;


        if (stateText) {

            stateText.textContent =
                "EXECUTING WORKLOAD";

        }


        if (stateDot) {

            stateDot.classList.add(
                "execution-running"
            );

        }


        let index = 0;


        function nextLine() {

            if (index >= codeLines.length) {

                showOutput();

                return;
            }


            const line =
                codeLines[index];


            line.classList.add(
                "code-line-executing"
            );


            executionTimer =
                setTimeout(function () {

                    line.classList.remove(
                        "code-line-executing"
                    );

                    line.classList.add(
                        "code-line-complete"
                    );

                    index++;

                    executionTimer =
                        setTimeout(
                            nextLine,
                            280
                        );

                }, 620);

        }


        nextLine();

    }


    /* =====================================================
       OUTPUT STREAM
       ===================================================== */

    function showOutput() {

        let outputIndex = 0;


        function nextOutput() {

            if (
                outputIndex >=
                outputLines.length
            ) {

                showResult();

                return;
            }


            const line =
                outputLines[outputIndex];


            line.classList.add(
                "output-line-visible"
            );


            outputIndex++;


            executionTimer =
                setTimeout(
                    nextOutput,
                    500
                );

        }


        nextOutput();

    }


    /* =====================================================
       RESULT
       ===================================================== */

    function showResult() {

        if (outputResult) {

            outputResult.classList.add(
                "output-result-visible"
            );

        }


        executionTimer =
            setTimeout(function () {

                if (outputComplete) {

                    outputComplete.classList.add(
                        "output-complete-visible"
                    );

                }


                if (stateText) {

                    stateText.textContent =
                        "EXECUTION COMPLETE";

                }


                if (stateDot) {

                    stateDot.classList.remove(
                        "execution-running"
                    );

                    stateDot.classList.add(
                        "execution-complete"
                    );

                }


                executionRunning = false;

            }, 700);

    }


    /* =====================================================
       RUN BUTTON
       ===================================================== */

    runButton.addEventListener(
        "click",
        function () {

            if (executionRunning) {
                return;
            }

            resetExecution();

            setTimeout(
                executeCode,
                150
            );

        }
    );


    /* =====================================================
       AUTO EXECUTION WHEN SECTION
       ENTERS VIEW
       ===================================================== */

    if ("IntersectionObserver" in window) {

        const observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(
                        function (entry) {

                            if (
                                entry.isIntersecting &&
                                !hasStarted
                            ) {

                                hasStarted = true;

                                setTimeout(
                                    executeCode,
                                    700
                                );

                                observer.unobserve(
                                    engine
                                );

                            }

                        }
                    );

                },
                {
                    threshold: 0.3
                }
            );


        observer.observe(engine);

    }


    /* =====================================================
       RESET AFTER COMPLETION
       ===================================================== */

    engine.addEventListener(
        "mouseleave",
        function () {

            if (!executionRunning) {

                clearTimeout(
                    executionTimer
                );

            }

        }
    );


})();


/* =========================================================
   ASSESSMENT INTELLIGENCE ANIMATION
   ========================================================= */

(function () {
    "use strict";

    const section = document.querySelector(
        "#assessment-intelligence"
    );

    if (!section) {
        return;
    }


    /* -----------------------------------------------------
       ELEMENTS
       ----------------------------------------------------- */

    const questionTypes = section.querySelectorAll(
        ".assessment-question-type"
    );

    const flowOne = section.querySelector(
        ".assessment-flow-one"
    );

    const flowTwo = section.querySelector(
        ".assessment-flow-two"
    );

    const evaluationPaths = section.querySelectorAll(
        ".evaluation-path"
    );

    const testBlocks = section.querySelectorAll(
        ".test-block"
    );

    const resultQuestions = section.querySelectorAll(
        ".result-question"
    );

    const hardcodeDetection = section.querySelector(
        ".hardcode-detection"
    );

    const evaluationCore = section.querySelector(
        ".evaluation-core"
    );

    const resultPanel = section.querySelector(
        ".assessment-result-panel"
    );

    const runButton = section.querySelector(
        ".assessment-run-button"
    );


    /* -----------------------------------------------------
       ANIMATION STATE
       ----------------------------------------------------- */

    let animationStarted = false;
    let animationTimers = [];


    /* -----------------------------------------------------
       HELPER
       ----------------------------------------------------- */

    function schedule(callback, delay) {

        const timer = setTimeout(
            callback,
            delay
        );

        animationTimers.push(timer);
    }


    function clearAnimationTimers() {

        animationTimers.forEach(
            function (timer) {
                clearTimeout(timer);
            }
        );

        animationTimers = [];
    }


    /* -----------------------------------------------------
       RESET
       ----------------------------------------------------- */

    function resetAssessmentAnimation() {

        clearAnimationTimers();

        questionTypes.forEach(
            function (item) {
                item.classList.remove(
                    "assessment-question-active"
                );
            }
        );

        evaluationPaths.forEach(
            function (item) {
                item.classList.remove(
                    "evaluation-path-active"
                );
            }
        );

        testBlocks.forEach(
            function (item) {
                item.classList.remove(
                    "test-block-active"
                );
            }
        );

        resultQuestions.forEach(
            function (item) {
                item.classList.remove(
                    "result-question-active"
                );
            }
        );

        if (flowOne) {
            flowOne.classList.remove(
                "assessment-flow-active"
            );
        }

        if (flowTwo) {
            flowTwo.classList.remove(
                "assessment-flow-active"
            );
        }

        if (hardcodeDetection) {
            hardcodeDetection.classList.remove(
                "hardcode-detection-active"
            );
        }

        if (evaluationCore) {
            evaluationCore.classList.remove(
                "evaluation-core-active"
            );
        }

        if (resultPanel) {
            resultPanel.classList.remove(
                "assessment-result-active"
            );
        }

        animationStarted = false;
    }


    /* -----------------------------------------------------
       START PIPELINE
       ----------------------------------------------------- */

    function startAssessmentAnimation() {

        if (animationStarted) {
            return;
        }

        animationStarted = true;

        resetAssessmentAnimation();

        animationStarted = true;


        /* ================================================
           1. QUESTION TYPES
           ================================================ */

        questionTypes.forEach(
            function (item, index) {

                schedule(
                    function () {

                        questionTypes.forEach(
                            function (question) {
                                question.classList.remove(
                                    "assessment-question-active"
                                );
                            }
                        );

                        item.classList.add(
                            "assessment-question-active"
                        );

                    },
                    350 + (index * 650)
                );

            }
        );


        /* ================================================
           2. MOVE TO SUBMISSION
           ================================================ */

        schedule(
            function () {

                if (flowOne) {
                    flowOne.classList.add(
                        "assessment-flow-active"
                    );
                }

            },
            3000
        );


        /* ================================================
           3. EVALUATION CORE
           ================================================ */

        schedule(
            function () {

                if (evaluationCore) {
                    evaluationCore.classList.add(
                        "evaluation-core-active"
                    );
                }

            },
            3900
        );


        /* ================================================
           4. EVALUATION PATHS
           ================================================ */

        evaluationPaths.forEach(
            function (item, index) {

                schedule(
                    function () {

                        item.classList.add(
                            "evaluation-path-active"
                        );

                    },
                    4400 + (index * 750)
                );

            }
        );


        /* ================================================
           5. SUBMISSION → TEST ENGINE
           ================================================ */

        schedule(
            function () {

                if (flowTwo) {
                    flowTwo.classList.add(
                        "assessment-flow-active"
                    );
                }

            },
            6900
        );


        /* ================================================
           6. TEST CASES
           ================================================ */

        testBlocks.forEach(
            function (item, index) {

                schedule(
                    function () {

                        item.classList.add(
                            "test-block-active"
                        );

                    },
                    7600 + (index * 900)
                );

            }
        );


        /* ================================================
           7. HARD-CODE DETECTION
           ================================================ */

        schedule(
            function () {

                if (hardcodeDetection) {
                    hardcodeDetection.classList.add(
                        "hardcode-detection-active"
                    );
                }

            },
            10500
        );


        /* ================================================
           8. RESULTS
           ================================================ */

        schedule(
            function () {

                if (resultPanel) {
                    resultPanel.classList.add(
                        "assessment-result-active"
                    );
                }

            },
            11400
        );


        /* ================================================
           9. QUESTION-WISE RESULTS
           ================================================ */

        resultQuestions.forEach(
            function (item, index) {

                schedule(
                    function () {

                        item.classList.add(
                            "result-question-active"
                        );

                    },
                    11900 + (index * 550)
                );

            }
        );


        /* ================================================
           10. LOOP
           ================================================ */

        schedule(
            function () {

                animationStarted = false;

                startAssessmentAnimation();

            },
            14500
        );
    }


    /* -----------------------------------------------------
       INTERSECTION OBSERVER
       ----------------------------------------------------- */

    const observer = new IntersectionObserver(
        function (entries) {

            entries.forEach(
                function (entry) {

                    if (entry.isIntersecting) {

                        startAssessmentAnimation();

                    } else {

                        clearAnimationTimers();

                        animationStarted = false;

                        resetAssessmentAnimation();

                    }

                }
            );

        },
        {
            threshold: 0.18
        }
    );


    observer.observe(section);


    /* -----------------------------------------------------
       RUN / TEST BUTTON
       ----------------------------------------------------- */

    if (runButton) {

        runButton.addEventListener(
            "click",
            function () {

                resetAssessmentAnimation();

                startAssessmentAnimation();

            }
        );

    }

})();

/* =========================================================
   MULTILINGUAL CONTENT LAYER
========================================================= */

(function () {
    "use strict";

    const section = document.querySelector(".multilingual-section");

    if (!section) {
        return;
    }

    const engine = section.querySelector(".language-engine-core");
    const flowParticle = section.querySelector(".language-flow-particle");
    const languageItems = section.querySelectorAll(".language-item");
    const processSteps = section.querySelectorAll(".language-process-step");

    let animationTimer = null;
    let isRunning = false;
    let currentLanguage = 0;
    let currentProcess = 0;


    function resetAnimation() {

        clearInterval(animationTimer);

        isRunning = false;
        currentLanguage = 0;
        currentProcess = 0;

        languageItems.forEach(function (item) {
            item.classList.remove("language-item-processing");
            item.classList.remove("language-item-complete");
        });

        processSteps.forEach(function (step) {
            step.classList.remove("language-process-active");
            step.classList.remove("language-process-complete");
        });

        if (engine) {
            engine.classList.remove("language-engine-processing");
        }

        if (flowParticle) {
            flowParticle.classList.remove("language-particle-active");
        }
    }


    function activateLanguage() {

        if (languageItems.length === 0) {
            return;
        }

        languageItems.forEach(function (item) {
            item.classList.remove("language-item-processing");
        });

        const item = languageItems[currentLanguage];

        if (item) {
            item.classList.add("language-item-processing");

            setTimeout(function () {
                item.classList.remove("language-item-processing");
                item.classList.add("language-item-complete");
            }, 900);
        }

        currentLanguage++;

        if (currentLanguage >= languageItems.length) {
            currentLanguage = 0;
        }
    }


    function activateProcess() {

        if (processSteps.length === 0) {
            return;
        }

        processSteps.forEach(function (step) {
            step.classList.remove("language-process-active");
        });

        const step = processSteps[currentProcess];

        if (step) {
            step.classList.add("language-process-active");

            setTimeout(function () {
                step.classList.remove("language-process-active");
                step.classList.add("language-process-complete");
            }, 1100);
        }

        currentProcess++;

        if (currentProcess >= processSteps.length) {
            currentProcess = 0;
        }
    }


    function startAnimation() {

        if (isRunning) {
            return;
        }

        isRunning = true;

        if (engine) {
            engine.classList.add("language-engine-processing");
        }

        if (flowParticle) {
            flowParticle.classList.add("language-particle-active");
        }

        activateLanguage();
        activateProcess();

        animationTimer = setInterval(function () {

            activateLanguage();
            activateProcess();

        }, 1600);
    }


    function stopAnimation() {
        resetAnimation();
    }


    const observer = new IntersectionObserver(
        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {
                    startAnimation();
                } else {
                    stopAnimation();
                }

            });

        },
        {
            threshold: 0.25
        }
    );


    observer.observe(section);

})();
/* =========================================================
   FINAL CTA ANIMATION
========================================================= */

(function () {
    "use strict";

    const section = document.querySelector(".final-cta-section");

    if (!section) {
        return;
    }

    const field = section.querySelector(".final-cta-field");
    const fieldNodes = section.querySelectorAll(".final-cta-field span");
    const container = section.querySelector(".final-cta-container");

    let animationStarted = false;


    function startFinalCTA() {

        if (animationStarted) {
            return;
        }

        animationStarted = true;

        section.classList.add("final-cta-visible");

        if (field) {
            field.classList.add("final-cta-field-active");
        }

        fieldNodes.forEach(function (node, index) {

            setTimeout(function () {
                node.classList.add("final-cta-node-active");
            }, index * 140);

        });

    }


    const observer = new IntersectionObserver(
        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {
                    startFinalCTA();
                }

            });

        },
        {
            threshold: 0.25
        }
    );


    observer.observe(section);

})();