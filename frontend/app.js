// ============================================================
// RESEARCH AI FRONTEND
// ============================================================

// ============================================================
// DOM ELEMENTS
// ============================================================

const button =
    document.getElementById("researchBtn");

const question =
    document.getElementById("question");

const result =
    document.getElementById("result");

const summary =
    document.getElementById("summary");

const sourceCount =
    document.getElementById("sourceCount");

const language =
    document.getElementById("language");


// ============================================================
// RENDER BACKEND
// ============================================================

// IMPORTANT:
// Do NOT use:
// http://127.0.0.1:5000/research
//
// Production backend:
const API_BASE =
    "https://researchai-v0f0.onrender.com";

const RESEARCH_API =
    `${API_BASE}/research`;

const HEALTH_API =
    `${API_BASE}/api/health`;


// ============================================================
// CONFIG
// ============================================================

const REQUEST_TIMEOUT =
    120000; // 120 seconds


// ============================================================
// CHECK DOM
// ============================================================

if (!button) {

    console.error(
        "❌ researchBtn not found"
    );

}

if (!question) {

    console.error(
        "❌ question input not found"
    );

}

if (!summary) {

    console.error(
        "❌ summary element not found"
    );

}


// ============================================================
// RESEARCH BUTTON
// ============================================================

if (button) {

    button.addEventListener(
        "click",
        startResearch
    );

}


// ============================================================
// ENTER KEY
// ============================================================

if (question) {

    question.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                startResearch();

            }

        }
    );

}


// ============================================================
// MAIN RESEARCH FUNCTION
// ============================================================

async function startResearch() {

    const text =
        question
            ? question.value.trim()
            : "";


    // ========================================================
    // EMPTY QUESTION
    // ========================================================

    if (!text) {

        alert(
            "Please enter a question."
        );

        return;

    }


    // ========================================================
    // SHOW RESULT
    // ========================================================

    if (result) {

        result.classList.remove(
            "hidden"
        );

    }


    // ========================================================
    // LOADING
    // ========================================================

    if (button) {

        button.disabled = true;

        button.textContent =
            "Researching...";

    }


    if (sourceCount) {

        sourceCount.textContent =
            "Searching...";

    }


    if (summary) {

        summary.innerHTML = `

            <div class="loading">

                <p>
                    🔎 ইন্টারনেটে খোঁজা হচ্ছে...
                </p>

                <br>

                <p>
                    📖 বিভিন্ন source পড়া হচ্ছে...
                </p>

                <br>

                <p>
                    🧠 তথ্য বিশ্লেষণ করা হচ্ছে...
                </p>

                <br>

                <p>
                    ✍️ Research result তৈরি হচ্ছে...
                </p>

            </div>

        `;

    }


    try {

        // ====================================================
        // LANGUAGE
        // ====================================================

        const selectedLanguage =
            language
                ? language.value
                : "auto";


        console.log(
            "========================================"
        );

        console.log(
            "🚀 RESEARCH REQUEST"
        );

        console.log(
            "Question:",
            text
        );

        console.log(
            "Language:",
            selectedLanguage
        );

        console.log(
            "Backend:",
            RESEARCH_API
        );

        console.log(
            "========================================"
        );


        // ====================================================
        // ABORT CONTROLLER
        // ====================================================

        const controller =
            new AbortController();


        const timeout =
            setTimeout(
                function () {

                    controller.abort();

                },
                REQUEST_TIMEOUT
            );


        // ====================================================
        // SEND REQUEST
        // ====================================================

        let response;


        try {

            response =
                await fetch(
                    RESEARCH_API,
                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                question:
                                    text,

                                language:
                                    selectedLanguage

                            }),

                        signal:
                            controller.signal

                    }
                );

        }

        finally {

            clearTimeout(
                timeout
            );

        }


        // ====================================================
        // READ RESPONSE AS TEXT
        // ====================================================
        //
        // Important:
        // Render 502 often returns HTML.
        //
        // response.json() would crash.
        //
        // So first read text.
        // ====================================================

        const rawResponse =
            await response.text();


        console.log(
            "HTTP Status:",
            response.status
        );

        console.log(
            "Raw response:",
            rawResponse
        );


        // ====================================================
        // PARSE JSON
        // ====================================================

        let data = null;


        if (rawResponse) {

            try {

                data =
                    JSON.parse(
                        rawResponse
                    );

            }

            catch (jsonError) {

                // Server returned HTML
                // or invalid JSON

                let preview =
                    rawResponse
                        .replace(
                            /<[^>]*>/g,
                            " "
                        )
                        .replace(
                            /\s+/g,
                            " "
                        )
                        .trim()
                        .substring(
                            0,
                            500
                        );


                if (
                    response.status === 502
                ) {

                    throw new Error(

                        "Render backend returned HTTP 502. " +
                        "The backend may have crashed, timed out, " +
                        "or the Render service may be unavailable.\n\n" +
                        preview

                    );

                }


                throw new Error(

                    `Server returned HTTP ${response.status} ` +
                    `instead of JSON.\n\n` +
                    preview

                );

            }

        }


        // ====================================================
        // HTTP ERROR
        // ====================================================

        if (!response.ok) {

            const backendError =
                data &&
                (
                    data.details ||
                    data.error ||
                    data.message
                );


            throw new Error(

                backendError ||

                `Backend returned HTTP ${response.status}`

            );

        }


        // ====================================================
        // EMPTY RESPONSE
        // ====================================================

        if (!data) {

            throw new Error(
                "Backend returned an empty response."
            );

        }


        // ====================================================
        // BACKEND SUCCESS CHECK
        // ====================================================

        if (
            data.success === false
        ) {

            throw new Error(

                data.details ||
                data.error ||
                "Research failed on backend."

            );

        }


        console.log(
            "✅ Backend response:",
            data
        );


        // ====================================================
        // LANGUAGE INFORMATION
        // ====================================================

        let languageText = "";


        if (
            data.answer_language
        ) {

            languageText = `

                <div class="language-info">

                    🌐 Answer language:

                    <strong>
                        ${escapeHTML(
                            data.answer_language
                        )}
                    </strong>

                </div>

            `;

        }


        // ====================================================
        // SOURCE COUNT
        // ====================================================

        const totalSources =
            Number(
                data.source_count || 0
            );


        if (sourceCount) {

            sourceCount.textContent =
                `${totalSources} Sources`;

        }


        // ====================================================
        // NO SOURCES
        // ====================================================

        if (
            !Array.isArray(
                data.sources
            ) ||
            data.sources.length === 0
        ) {

            if (summary) {

                summary.innerHTML = `

                    ${languageText}

                    <div class="error-box">

                        <h3>
                            ⚠️ No readable sources
                        </h3>

                        <p>
                            Search completed,
                            but no webpage could
                            be read.
                        </p>

                        <br>

                        <p>

                            🔎 Search query:

                            <strong>
                                ${escapeHTML(
                                    data.search_query ||
                                    text
                                )}
                            </strong>

                        </p>

                        <br>

                        <p>

                            💡 Backend:

                            <code>
                                ${escapeHTML(
                                    RESEARCH_API
                                )}
                            </code>

                        </p>

                    </div>

                `;

            }

            return;

        }


        // ====================================================
        // MAIN HTML
        // ====================================================

        let html = "";


        // ====================================================
        // LANGUAGE
        // ====================================================

        html +=
            languageText;


        // ====================================================
        // AI SUMMARY
        // ====================================================

        if (
            data.summary &&
            String(
                data.summary
            ).trim()
        ) {

            html += `

                <div class="ai-summary">

                    <div class="summary-title">

                        🧠 AI Summary

                    </div>

                    <div class="summary-content">

                        ${formatText(
                            data.summary
                        )}

                    </div>

                </div>

            `;

        }


        // ====================================================
        // RESEARCH INFORMATION
        // ====================================================

        html += `

            <div class="research-intro">

                <h2>
                    📚 Research Result
                </h2>

                <p>

                    মোট

                    <strong>
                        ${totalSources}
                    </strong>

                    টি readable source পাওয়া গেছে।

                </p>

                ${
                    data.processing_time
                    ?
                    `
                        <p>

                            ⏱️ Processing time:

                            <strong>
                                ${escapeHTML(
                                    data.processing_time
                                )}s
                            </strong>

                        </p>
                    `
                    :
                    ""
                }

            </div>

        `;


        // ====================================================
        // SOURCES TITLE
        // ====================================================

        html += `

            <div class="sources-title">

                🔗 Sources

            </div>

        `;


        // ====================================================
        // SOURCES
        // ====================================================

        data.sources.forEach(

            function (
                source,
                index
            ) {

                const title =
                    source &&
                    source.title
                    ?
                    source.title
                    :
                    "Untitled source";


                const url =
                    source &&
                    source.url
                    ?
                    source.url
                    :
                    "#";


                const sourceText =
                    source &&
                    source.text
                    ?
                    source.text
                    :
                    "No readable text found.";


                html += `

                    <div class="source">

                        <h3>

                            ${index + 1}.
                            ${escapeHTML(
                                title
                            )}

                        </h3>


                        <p>

                            ${escapeHTML(
                                sourceText
                            )}

                        </p>


                        <a

                            href="${escapeAttribute(
                                url
                            )}"

                            target="_blank"

                            rel="noopener noreferrer"

                        >

                            Open source →

                        </a>

                    </div>

                `;

            }

        );


        // ====================================================
        // SHOW RESULT
        // ====================================================

        if (summary) {

            summary.innerHTML =
                html;

        }


        console.log(
            "========================================"
        );

        console.log(
            "✅ RESEARCH COMPLETED"
        );

        console.log(
            "Sources:",
            totalSources
        );

        console.log(
            "========================================"
        );

    }


    catch (error) {

        console.error(
            "❌ RESEARCH ERROR:",
            error
        );


        if (sourceCount) {

            sourceCount.textContent =
                "Error";

        }


        // ====================================================
        // ERROR MESSAGE
        // ====================================================

        let errorMessage =
            error &&
            error.message
            ?
            error.message
            :
            "Unknown error";


        // ====================================================
        // CONNECTION ERROR
        // ====================================================

        if (
            error.name ===
            "TypeError"
        ) {

            errorMessage =
                "Backend-এর সাথে connection করা যাচ্ছে না। " +
                "Render backend online আছে কিনা check করুন.";

        }


        // ====================================================
        // TIMEOUT
        // ====================================================

        if (
            error.name ===
            "AbortError"
        ) {

            errorMessage =
                "Research request timeout হয়েছে। " +
                "Render backend অনেক সময় নিচ্ছে বা request process করতে পারছে না.";

        }


        if (summary) {

            summary.innerHTML = `

                <div class="error-box">

                    <h3>
                        ❌ Research failed
                    </h3>

                    <p>

                        ${formatText(
                            errorMessage
                        )}

                    </p>

                    <br>

                    <p>

                        🔗 Backend:

                    </p>

                    <code>

                        ${escapeHTML(
                            RESEARCH_API
                        )}

                    </code>

                    <br><br>

                    <p>

                        🩺 Health check:

                    </p>

                    <a
                        href="${escapeAttribute(
                            HEALTH_API
                        )}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >

                        Check Backend Health →

                    </a>

                </div>

            `;

        }

    }


    finally {

        if (button) {

            button.disabled =
                false;

            button.textContent =
                "Research →";

        }

    }

}


// ============================================================
// BACKEND HEALTH CHECK
// ============================================================

async function checkBackendHealth() {

    try {

        const response =
            await fetch(
                HEALTH_API,
                {
                    method:
                        "GET",
                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        const raw =
            await response.text();


        let data;


        try {

            data =
                JSON.parse(
                    raw
                );

        }

        catch {

            console.error(
                "Health endpoint did not return JSON:",
                raw
            );

            return false;

        }


        console.log(
            "🏥 Backend Health:",
            data
        );


        return (
            response.ok &&
            data.status ===
                "online"
        );

    }

    catch (error) {

        console.error(
            "❌ Health check failed:",
            error
        );

        return false;

    }

}


// ============================================================
// FORMAT TEXT
// ============================================================

function formatText(text) {

    if (!text) {

        return "";

    }


    let safeText =
        escapeHTML(
            String(text)
        );


    safeText =
        safeText.replace(
            /\r\n/g,
            "\n"
        );


    safeText =
        safeText.replace(
            /\n\n+/g,
            "<br><br>"
        );


    safeText =
        safeText.replace(
            /\n/g,
            "<br>"
        );


    return safeText;

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHTML(text) {

    if (
        text === null ||
        text === undefined
    ) {

        return "";

    }


    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(text);


    return div.innerHTML;

}


// ============================================================
// ESCAPE URL
// ============================================================

function escapeAttribute(url) {

    if (!url) {

        return "#";

    }


    return String(url)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#39;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        );

}


// ============================================================
// INITIAL BACKEND CHECK
// ============================================================

checkBackendHealth()
    .then(
        function (online) {

            if (online) {

                console.log(
                    "✅ Research AI backend is online."
                );

            }

            else {

                console.warn(
                    "⚠️ Research AI backend health check failed."
                );

            }

        }
    );
