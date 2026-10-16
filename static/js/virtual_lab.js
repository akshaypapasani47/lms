(function () {
    "use strict";

    /*
    ============================================================
    VIRTUAL LAB
    TERMINAL + FILE EXPLORER
    ============================================================
    */


    /* ============================================================
       FILE EXPLORER
       ============================================================ */

    function initWorkspaceExplorer() {

        const tree = document.getElementById("vl-file-tree");

        if (!tree) {
            return;
        }

        const filesUrl = tree.dataset.filesUrl;

        if (!filesUrl) {
            return;
        }


        async function loadDirectory(path = "") {

            tree.innerHTML = `
                <div class="vl-file-loading">
                    <i class="fas fa-circle-notch fa-spin"></i>
                    LOADING WORKSPACE
                </div>
            `;

            try {

                const url = new URL(
                    filesUrl,
                    window.location.origin
                );

                if (path) {
                    url.searchParams.set("path", path);
                }


                const response = await fetch(
                    url.toString(),
                    {
                        method: "GET",
                        headers: {
                            "X-Requested-With": "XMLHttpRequest"
                        }
                    }
                );


                if (!response.ok) {
                    throw new Error(
                        `Unable to load workspace (${response.status})`
                    );
                }


                const data = await response.json();

                renderDirectory(data, path);


            } catch (error) {

                console.error(
                    "WORKSPACE ERROR:",
                    error
                );

                tree.innerHTML = `
                    <div class="vl-file-error">
                        <i class="fas fa-triangle-exclamation"></i>
                        <span>
                            ${escapeHtml(error.message)}
                        </span>
                    </div>
                `;

            }

        }


        function renderDirectory(data, currentPath) {

            tree.innerHTML = "";


            if (
                currentPath &&
                currentPath !== ""
            ) {

                const backRow =
                    document.createElement("div");

                backRow.className =
                    "vl-file-row vl-file-back";

                backRow.innerHTML = `
                    <span class="vl-file-icon">
                        <i class="fas fa-arrow-left"></i>
                    </span>

                    <span class="vl-file-name">
                        ..
                    </span>
                `;


                backRow.addEventListener(
                    "click",
                    function () {

                        const parentPath =
                            getParentPath(currentPath);

                        loadDirectory(parentPath);

                    }
                );


                tree.appendChild(backRow);

            }


            const entries =
                data.files ||
                data.entries ||
                [];


            if (!entries.length) {

                const empty =
                    document.createElement("div");

                empty.className =
                    "vl-file-empty";

                empty.innerHTML = `
                    <i class="fas fa-folder-open"></i>
                    <span>EMPTY DIRECTORY</span>
                `;

                tree.appendChild(empty);

                return;
            }


            entries.forEach(
                function (entry) {

                    const row =
                        document.createElement("div");

                    row.className =
                        "vl-file-row";


                    const icon =
                        document.createElement("span");

                    icon.className =
                        "vl-file-icon";


                    const name =
                        document.createElement("span");

                    name.className =
                        "vl-file-name";


                    const isDirectory =
                        entry.is_directory ||
                        entry.type === "directory" ||
                        entry.type === "folder";


                    if (isDirectory) {

                        row.classList.add(
                            "is-directory"
                        );

                        icon.innerHTML =
                            `<i class="fas fa-folder"></i>`;

                    } else {

                        row.classList.add(
                            "is-file"
                        );

                        icon.innerHTML =
                            `<i class="fas fa-file-code"></i>`;

                    }


                    name.textContent =
                        entry.name ||
                        entry.filename ||
                        entry.path;


                    row.appendChild(icon);
                    row.appendChild(name);

                    tree.appendChild(row);


                    if (isDirectory) {

                        row.addEventListener(
                            "click",
                            function () {

                                loadDirectory(
                                    entry.path
                                );

                            }
                        );

                    } else {

                        row.addEventListener(
                            "click",
                            function () {

                                openFile(
                                    entry.path,
                                    row
                                );

                            }
                        );

                    }

                }
            );

        }


        async function openFile(
            path,
            row
        ) {

            const fileUrl =
                document.getElementById(
                    "vl-editor"
                )?.dataset.fileUrl;


            if (!fileUrl) {
                return;
            }


            try {

                const url = new URL(
                    fileUrl,
                    window.location.origin
                );

                url.searchParams.set(
                    "path",
                    path
                );


                const response =
                    await fetch(
                        url.toString(),
                        {
                            method: "GET",
                            headers: {
                                "X-Requested-With":
                                    "XMLHttpRequest"
                            }
                        }
                    );


                if (!response.ok) {
                    throw new Error(
                        `Unable to open file (${response.status})`
                    );
                }


                const data =
                    await response.json();


                const editor =
                    document.getElementById(
                        "vl-editor"
                    );


                if (editor) {

                    editor.value =
                        data.content || "";

                }


                document.querySelectorAll(
                    ".vl-file-row"
                ).forEach(
                    function (item) {
                        item.classList.remove(
                            "is-selected"
                        );
                    }
                );


                if (row) {

                    row.classList.add(
                        "is-selected"
                    );

                }


                const filename =
                    document.getElementById(
                        "vl-editor-filename"
                    );


                if (filename) {

                    filename.textContent =
                        data.name ||
                        path;

                }


            } catch (error) {

                console.error(
                    "FILE OPEN ERROR:",
                    error
                );

            }

        }


        function getParentPath(path) {

            const parts =
                path
                    .split("/")
                    .filter(Boolean);


            parts.pop();


            return parts.join("/");

        }


        function escapeHtml(value) {

            return String(value)
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");

        }


        loadDirectory();

    }


    /* ============================================================
       TERMINAL
       ============================================================ */

    function initVLTerminal() {

        const terminalElement =
            document.getElementById(
                "vl-terminal"
            );


        if (!terminalElement) {
            return;
        }


        /*
        ------------------------------------------------------------
        CHECK XTERM
        ------------------------------------------------------------
        */

        if (
            typeof Terminal ===
            "undefined"
        ) {

            console.error(
                "xterm.js is not loaded."
            );

            terminalElement.innerHTML = `
                <div class="vl-terminal-error">
                    xterm.js could not be loaded.
                </div>
            `;

            return;
        }


        /*
        ------------------------------------------------------------
        TERMINAL URL
        ------------------------------------------------------------
        */

        const terminalUrl =
            terminalElement.dataset
                .websocketUrl;


        if (!terminalUrl) {

            console.error(
                "Virtual Lab WebSocket URL is missing."
            );

            return;
        }


        /*
        ------------------------------------------------------------
        CREATE XTERM
        ------------------------------------------------------------
        */

        const terminal =
            new Terminal({

                cursorBlink: true,

                cursorStyle: "block",

                fontFamily:
                    "JetBrains Mono, Consolas, monospace",

                fontSize: 14,

                lineHeight: 1.25,

                scrollback: 5000,

                convertEol: true,

                theme: {

                    background: "#050816",

                    foreground: "#d7e7ff",

                    cursor: "#00e5ff",

                    cursorAccent: "#050816",

                    selectionBackground:
                        "rgba(0, 229, 255, 0.25)",

                    black: "#111827",

                    red: "#ff5f56",

                    green: "#27c93f",

                    yellow: "#ffbd2e",

                    blue: "#4da6ff",

                    magenta: "#c084fc",

                    cyan: "#22d3ee",

                    white: "#e5e7eb"

                }

            });


        /*
        ------------------------------------------------------------
        FIT ADDON
        ------------------------------------------------------------
        */

        let fitAddon = null;


        if (
            typeof FitAddon !==
            "undefined" &&
            FitAddon.FitAddon
        ) {

            fitAddon =
                new FitAddon.FitAddon();

            terminal.loadAddon(
                fitAddon
            );

        }


        /*
        ------------------------------------------------------------
        REMOVE OLD TERMINAL CONTENT
        ------------------------------------------------------------
        */

        terminalElement.innerHTML = "";

        terminalElement.classList.add(
            "vl-xterm-container"
        );


        /*
        ------------------------------------------------------------
        OPEN TERMINAL
        ------------------------------------------------------------
        */

        terminal.open(
            terminalElement
        );


        if (fitAddon) {

            setTimeout(
                function () {

                    fitAddon.fit();

                },
                50
            );

        }


        /*
        ------------------------------------------------------------
        WEBSOCKET URL
        ------------------------------------------------------------
        */

        let websocketUrl =
            terminalUrl;


        if (
            websocketUrl.startsWith("/")
        ) {

            const protocol =
                window.location.protocol ===
                "https:"
                    ? "wss:"
                    : "ws:";

            websocketUrl =
                protocol +
                "//" +
                window.location.host +
                websocketUrl;

        }


        /*
        ------------------------------------------------------------
        CONNECTION STATUS
        ------------------------------------------------------------
        */

        const liveDot =
            document.querySelector(
                ".vl-terminal-live-dot"
            );


        const shellStatus =
            document.querySelector(
                ".vl-terminal-shell"
            );


        function setTerminalStatus(
            connected
        ) {

            if (liveDot) {

                liveDot.classList.toggle(
                    "is-offline",
                    !connected
                );

            }


            if (shellStatus) {

                shellStatus.innerHTML =
                    connected
                        ? `
                            <span class="vl-terminal-live-dot"></span>
                            CONTAINER
                          `
                        : `
                            <span class="vl-terminal-live-dot is-offline"></span>
                            DISCONNECTED
                          `;

            }

        }


        /*
        ------------------------------------------------------------
        WEBSOCKET
        ------------------------------------------------------------
        */

        let socket = null;


        function connectTerminal() {

            terminal.write(
                "\r\n\x1b[36mConnecting to Virtual Lab...\x1b[0m\r\n"
            );


            socket =
                new WebSocket(
                    websocketUrl
                );


            socket.binaryType =
                "arraybuffer";


            socket.onopen =
                function () {

                    setTerminalStatus(
                        true
                    );


                    terminal.write(
                        "\x1b[32mConnected.\x1b[0m\r\n"
                    );


                    terminal.focus();


                    sendResize();

                };


            socket.onmessage =
                function (event) {

                    try {

                        const data =
                            JSON.parse(
                                event.data
                            );


                        if (
                            data.type ===
                            "output"
                        ) {

                            terminal.write(
                                data.data || ""
                            );

                        }


                        else if (
                            data.type ===
                            "connected"
                        ) {

                            terminal.write(
                                "\r\n\x1b[36m" +
                                "Environment: " +
                                (data.lab || "Virtual Lab") +
                                "\x1b[0m\r\n"
                            );

                            terminal.write(
                                "\x1b[36m" +
                                "Workspace: " +
                                (data.workspace ||
                                    "/workspace") +
                                "\x1b[0m\r\n\r\n"
                            );

                        }


                        else if (
                            data.type ===
                            "error"
                        ) {

                            terminal.write(
                                "\r\n\x1b[31m" +
                                data.message +
                                "\x1b[0m\r\n"
                            );

                        }

                    } catch (error) {

                        /*
                        Raw fallback
                        */

                        terminal.write(
                            event.data
                        );

                    }

                };


            socket.onclose =
                function () {

                    setTerminalStatus(
                        false
                    );


                    terminal.write(
                        "\r\n\x1b[31m" +
                        "Terminal connection closed." +
                        "\x1b[0m\r\n"
                    );

                };


            socket.onerror =
                function (error) {

                    console.error(
                        "VIRTUAL LAB WEBSOCKET ERROR:",
                        error
                    );


                    setTerminalStatus(
                        false
                    );


                    terminal.write(
                        "\r\n\x1b[31m" +
                        "WebSocket connection error." +
                        "\x1b[0m\r\n"
                    );

                };

        }


        /*
        ------------------------------------------------------------
        SEND TERMINAL INPUT
        ------------------------------------------------------------
        */

        terminal.onData(
            function (data) {

                if (
                    socket &&
                    socket.readyState ===
                    WebSocket.OPEN
                ) {

                    socket.send(
                        JSON.stringify({

                            type: "input",

                            data: data

                        })
                    );

                }

            }
        );


        /*
        ------------------------------------------------------------
        SEND RESIZE
        ------------------------------------------------------------
        */

        function sendResize() {

            if (
                !socket ||
                socket.readyState !==
                    WebSocket.OPEN
            ) {

                return;
            }


            const dimensions =
                getTerminalDimensions();


            if (!dimensions) {
                return;
            }


            socket.send(
                JSON.stringify({

                    type: "resize",

                    cols:
                        dimensions.cols,

                    rows:
                        dimensions.rows

                })
            );

        }


        function getTerminalDimensions() {

            if (
                !terminalElement
            ) {

                return null;

            }


            const cols =
                terminal.cols ||
                120;


            const rows =
                terminal.rows ||
                30;


            return {
                cols: cols,
                rows: rows
            };

        }


        /*
        ------------------------------------------------------------
        RESIZE OBSERVER
        ------------------------------------------------------------
        */

        if (
            fitAddon &&
            typeof ResizeObserver !==
                "undefined"
        ) {

            const resizeObserver =
                new ResizeObserver(
                    function () {

                        try {

                            fitAddon.fit();

                            sendResize();

                        } catch (error) {

                            console.error(
                                "TERMINAL RESIZE ERROR:",
                                error
                            );

                        }

                    }
                );


            resizeObserver.observe(
                terminalElement
            );

        }


        /*
        ------------------------------------------------------------
        WINDOW RESIZE
        ------------------------------------------------------------
        */

        window.addEventListener(
            "resize",
            function () {

                if (fitAddon) {

                    try {

                        fitAddon.fit();

                    } catch (error) {

                        console.error(
                            "XTERM FIT ERROR:",
                            error
                        );

                    }

                }


                sendResize();

            }
        );


        /*
        ------------------------------------------------------------
        CLEAR TERMINAL
        ------------------------------------------------------------
        */

        const clearButton =
            document.getElementById(
                "vl-terminal-clear"
            );


        if (clearButton) {

            clearButton.addEventListener(
                "click",
                function () {

                    terminal.clear();

                    terminal.focus();

                }
            );

        }


        /*
        ------------------------------------------------------------
        EXPAND TERMINAL
        ------------------------------------------------------------
        */

        const expandButton =
            document.getElementById(
                "vl-terminal-expand"
            );


        if (expandButton) {

            expandButton.addEventListener(
                "click",
                function () {

                    const panel =
                        document.querySelector(
                            ".vl-terminal-panel"
                        );


                    if (!panel) {
                        return;
                    }


                    panel.classList.toggle(
                        "is-expanded"
                    );


                    const icon =
                        expandButton.querySelector(
                            "i"
                        );


                    if (icon) {

                        icon.className =
                            panel.classList.contains(
                                "is-expanded"
                            )
                                ? "fas fa-compress"
                                : "fas fa-expand";

                    }


                    setTimeout(
                        function () {

                            if (fitAddon) {

                                fitAddon.fit();

                            }

                            sendResize();

                            terminal.focus();

                        },
                        100
                    );

                }
            );

        }


        /*
        ------------------------------------------------------------
        CLICK TERMINAL = FOCUS
        ------------------------------------------------------------
        */

        terminalElement.addEventListener(
            "click",
            function () {

                terminal.focus();

            }
        );


        /*
        ------------------------------------------------------------
        CONNECT
        ------------------------------------------------------------
        */

        connectTerminal();

    }


    /* ============================================================
       TERMINAL RESIZE HANDLE
       ============================================================ */

    function initTerminalResize() {

        const workspace =
            document.querySelector(
                ".vl-workspace"
            );


        const handle =
            document.getElementById(
                "vl-terminal-resize-handle"
            );


        if (
            !workspace ||
            !handle
        ) {

            return;

        }


        let isDragging =
            false;


        let startY = 0;

        let startHeight = 0;


        handle.addEventListener(
            "pointerdown",
            function (event) {

                event.preventDefault();


                isDragging =
                    true;


                startY =
                    event.clientY;


                const terminalPanel =
                    document.querySelector(
                        ".vl-terminal-panel"
                    );


                if (
                    terminalPanel
                ) {

                    startHeight =
                        terminalPanel
                            .getBoundingClientRect()
                            .height;

                }


                handle.setPointerCapture(
                    event.pointerId
                );


                handle.classList.add(
                    "is-dragging"
                );


                document.body.classList.add(
                    "vl-terminal-resizing"
                );

            }
        );


        handle.addEventListener(
            "pointermove",
            function (event) {

                if (!isDragging) {
                    return;
                }


                const terminalPanel =
                    document.querySelector(
                        ".vl-terminal-panel"
                    );


                if (
                    !terminalPanel
                ) {

                    return;

                }


                const delta =
                    startY -
                    event.clientY;


                const newHeight =
                    Math.max(
                        180,
                        Math.min(
                            650,
                            startHeight +
                            delta
                        )
                    );


                terminalPanel.style.height =
                    `${newHeight}px`;

            }
        );


        handle.addEventListener(
            "pointerup",
            function () {

                isDragging =
                    false;


                handle.classList.remove(
                    "is-dragging"
                );


                document.body.classList.remove(
                    "vl-terminal-resizing"
                );

            }
        );


        handle.addEventListener(
            "pointercancel",
            function () {

                isDragging =
                    false;


                handle.classList.remove(
                    "is-dragging"
                );


                document.body.classList.remove(
                    "vl-terminal-resizing"
                );

            }
        );

    }


    /* ============================================================
       INITIALIZE
       ============================================================ */

    function initializeVirtualLab() {

    // Show Hero section
    const hero = document.querySelector(".vl-compute-hero");

    if (hero) {
        requestAnimationFrame(function () {
            hero.classList.add("vl-hero-visible");
        });
    }

    initWorkspaceExplorer();

    initVLTerminal();

    initTerminalResize();

}

})();