```javascript
// ============================================================
// RESEARCH AI FRONTEND
// Works with local Flask + Render production backend
// ============================================================

"use strict";


// ============================================================
// DOM ELEMENTS
// ============================================================

const button = document.getElementById("researchBtn");
const question = document.getElementById("question");
const result = document.getElementById("result");
const summary = document.getElementById("summary");
const sourceCount = document.getElementById("sourceCount");
const language = document.getElementById("language");


// ============================================================
// BACKEND URL
// ============================================================

// If frontend is served by Render itself:
//   window.location.origin = https://researchai-v0f0.onrender.com
//
// If frontend is opened locally:
//   use local Flask.
//
// This removes the old hard-coded 127.0.0.1 problem.

const BACKEND_URL =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost"
        ? "http://127.0.0.1:5000"
        : window.location.origin;


// Research endpoint
const RESEARCH_URL =
    `${BACKEND_URL}/research`;


// Health endpoint
const HEALTH_URL =
    `${BACKEND_URL}/api/health`;


// ============================================================
// DEBUG
// ============================================================

console.log("====================================");
console.log("🔬 Research AI Frontend");
console.log("Backend:", BACKEND_URL);
console.log("Research:", RESEARCH_URL);
console.log("Health:", HEALTH_URL);
console.log("====================================");


// ============================================================
// CHECK REQUIRED ELEMENTS
// ============================================================

if (!button) {
    console.error("❌ researchBtn not found");
}

if (!question) {
    console.error("❌ question input not found");
}

if (!summary) {
    console.error("❌ summary element not found");
}


// ============================================================
// HEALTH CHECK
// ============================================================

async function checkBackend() {

    try {

        console.log("🩺 Checking backend...");

        const response = await fetch(
            HEALTH_URL,
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            }
        );

        const data = await response.json();

        console.log(
            "🩺 Backend health:",
            data
        );


        if (!response.ok) {

            console.error(
                "❌ Backend health failed:",
                data
            );

            return false;
        }


        if (data.tools_loaded === false) {

            console.error(
                "❌ Backend is online but tools are NOT loaded.",
                data.tool_import_error
            );

            return false;
        }


        return true;

    }

    catch (error) {

        console.error(
            "❌ Backend health connection failed:",
            error
        );

        return false;
    }
}


// ============================================================
// INITIAL BACKEND CHECK
// ============================================================

checkBackend();


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
// ENTER KEY SUPPORT
// ============================================================

if (question) {

    question.addEventListener(
        "keydown",
        function (event) {

            // Ctrl + Enter
            if (
                event.key === "Enter" &&
                event.ctrlKey
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


    // --------------------------------------------------------
    // Empty question
    // --------------------------------------------------------

    if (!text) {

        alert(
            "Please enter a research question."
        );

        if (question) {
            question.focus();
        }

        return;
    }


    // --------------------------------------------------------
    // Show result
    // --------------------------------------------------------

    if (result) {

        result.classList.remove(
            "hidden"
        );
    }


    // --------------------------------------------------------
    // Loading state
    // --------------------------------------------------------

    setLoadingState(true);


    try {

        // ====================================================
        // LANGUAGE
        // ====================================================

        const selectedLanguage =
            language
                ? language.value
                : "auto";


        console.log(
            "❓ Question:",
            text
        );

        console.log(
            "🌐 Language:",
            selectedLanguage
        );

        console.log(
            "📡 Sending:",
            RESEARCH_URL
        );


        // ====================================================
        // REQUEST
        // ====================================================

        const response =
            await fetch(
                RESEARCH_URL,
                {

                    method: "POST",

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

                        })

                }
            );


        // ====================================================
        // READ RESPONSE SAFELY
        // ====================================================

        const contentType =
            response.headers.get(
                "content-type"
            ) || "";


        let data;


        if (
            contentType.includes(
                "application/json"
            )
        ) {

            data =
                await response.json();

        }

        else {

            const raw =
                await response.text();

            console.error(
                "❌ Backend returned non-JSON:",
                raw
            );

            throw new Error(
                `Backend returned ${response.status} instead of JSON`
            );
        }


        console.log(
            "📥 Backend response:",
            data
        );


        // ====================================================
        // HTTP ERROR
        // ====================================================

        if (!response.ok) {

            const backendError =
                data.details ||
                data.error ||
                `HTTP ${response.status}`;

            throw new Error(
                backendError
            );
        }


        // ====================================================
        // BACKEND SUCCESS FLAG
        // ====================================================

        if (
            data.success === false
        ) {

            throw new Error(
                data.details ||
                data.error ||
                "Research failed"
            );
        }


        // ====================================================
        // LANGUAGE INFO
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
        // SUMMARY
        // ====================================================

        let html = "";


        html += languageText;


        if (data.summary) {

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
        // STRUCTURED RESEARCH
        // ====================================================

        if (
            data.structured &&
            typeof data.structured === "object"
        ) {

            const sections =
                Object.entries(
                    data.structured
                );


            if (sections.length > 0) {

                html += `

                    <div class="structured-research">

                        <div class="sources-title">

                            📊 Research Analysis

                        </div>

                `;


                sections.forEach(
                    function (
                        [key, value]
                    ) {

                        if (!value) {
                            return;
                        }


                        html += `

                            <div class="research-section">

                                <h3>
                                    ${escapeHTML(
                                        formatIntentName(
                                            key
                                        )
                                    )}
                                </h3>

                                <div>

                                    ${formatText(
                                        value
                                    )}

                                </div>

                            </div>

                        `;
                    }
                );


                html += `

                    </div>

                `;
            }
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

            </div>

        `;


        // ====================================================
        // SOURCES
        // ====================================================

        if (
            Array.isArray(
                data.sources
            ) &&
            data.sources.length > 0
        ) {

            html += `

                <div class="sources-title">

                    🔗 Sources

                </div>

            `;


            data.sources.forEach(
                function (
                    source,
                    index
                ) {

                    const title =
                        source.title ||
                        "Untitled source";


                    const url =
                        source.url ||
                        "#";


                    const sourceText =
                        source.text ||
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

        }

        else {

            html += `

                <div class="error-box">

                    <p>
                        ⚠️ Search completed,
                        but no readable webpage
                        was returned.
                    </p>

                </div>

            `;
        }


        // ====================================================
        // PROCESSING TIME
        // ====================================================

        if (
            data.processing_time
        ) {

            html += `

                <div class="processing-time">

                    ⏱️ Processing time:
                    ${escapeHTML(
                        String(
                            data.processing_time
                        )
                    )} seconds

                </div>

            `;
        }


        // ====================================================
        // DISPLAY RESULT
        // ====================================================

        if (summary) {

            summary.innerHTML =
                html;
        }


    }

    catch (error) {

        console.error(
            "❌ Research Error:",
            error
        );


        if (sourceCount) {

            sourceCount.textContent =
                "Error";
        }


        const message =
            error && error.message
                ? error.message
                : "Unknown error";


        if (summary) {

            summary.innerHTML = `

                <div class="error-box">

                    <h3>
                        ❌ Research failed
                    </h3>

                    <p>

                        ${escapeHTML(
                            message
                        )}

                    </p>

                    <br>

                    <p>

                        🔗 Backend:

                    </p>

                    <code>

                        ${escapeHTML(
                            RESEARCH_URL
                        )}

                    </code>

                    <br><br>

                    <button
                        type="button"
                        onclick="window.location.reload()"
                    >

                        🔄 Try Again

                    </button>

                </div>

            `;
        }

    }

    finally {

        setLoadingState(false);

    }
}


// ============================================================
// LOADING STATE
// ============================================================

function setLoadingState(
    loading
) {

    if (!button) {
        return;
    }


    button.disabled =
        loading;


    if (loading) {

        button.textContent =
            "Researching...";


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
                        📖 বিভিন্ন webpage পড়া হচ্ছে...
                    </p>

                    <br>

                    <p>
                        🧠 তথ্য বিশ্লেষণ করা হচ্ছে...
                    </p>

                </div>

            `;
        }

    }

    else {

        button.textContent =
            "Research →";
    }
}


// ============================================================
// FORMAT TEXT
// ============================================================

function formatText(
    text
) {

    if (
        text === null ||
        text === undefined
    ) {

        return "";
    }


    return escapeHTML(
        String(text)
    )

    .replace(
        /\n\n/g,
        "<br><br>"
    )

    .replace(
        /\n/g,
        "<br>"
    );
}


// ============================================================
// FORMAT INTENT NAME
// ============================================================

function formatIntentName(
    name
) {

    return String(
        name || ""
    )

    .replace(
        /_/g,
        " "
    )

    .replace(
        /\b\w/g,
        function (char) {
            return char.toUpperCase();
        }
    );
}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHTML(
    text
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(
            text ?? ""
        );


    return div.innerHTML;
}


// ============================================================
// ESCAPE URL ATTRIBUTE
// ============================================================

function escapeAttribute(
    url
) {

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
// GLOBAL DEBUG HELPER
// ============================================================

window.ResearchAI = {

    backend:
        BACKEND_URL,

    research:
        RESEARCH_URL,

    health:
        HEALTH_URL,

    checkBackend:
        checkBackend,

    startResearch:
        startResearch

};


console.log(
    "✅ Research AI frontend loaded successfully"
);
```
