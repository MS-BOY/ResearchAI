// ==========================================
// DOM Elements
// ==========================================

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


// ==========================================
// RENDER BACKEND API
// ==========================================
//
// IMPORTANT:
// Do NOT use:
// http://127.0.0.1:5000/research
//
// That only works on your own PC.
//
// Render backend:
// ==========================================

const API_URL =
    "https://researchai-v0f0.onrender.com/research";


// ==========================================
// Research Button
// ==========================================

if (button) {

    button.addEventListener(
        "click",
        startResearch
    );

}


// ==========================================
// Enter Key Support
// ==========================================

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


// ==========================================
// Main Research Function
// ==========================================

async function startResearch() {

    const text =
        question
            ? question.value.trim()
            : "";


    // ======================================
    // Empty question
    // ======================================

    if (!text) {

        alert(
            "Please enter a question."
        );

        return;

    }


    // ======================================
    // Show result
    // ======================================

    if (result) {

        result.classList.remove(
            "hidden"
        );

    }


    // ======================================
    // Loading
    // ======================================

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
                    🔎 Internet searching...
                </p>

                <br>

                <p>
                    📖 Reading sources...
                </p>

                <br>

                <p>
                    🧠 Analyzing information...
                </p>

                <br>

                <p>
                    ✍️ Creating summary...
                </p>

            </div>

        `;

    }


    try {

        // ==================================
        // Language
        // ==================================

        const selectedLanguage =
            language
                ? language.value
                : "auto";


        console.log(
            "================================"
        );

        console.log(
            "🚀 RESEARCH REQUEST"
        );

        console.log(
            "================================"
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
            "API:",
            API_URL
        );


        // ==================================
        // Send request to Render
        // ==================================

        const response =
            await fetch(
                API_URL,
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


        // ==================================
        // Read response as text first
        // ==================================
        //
        // This is important.
        //
        // If Render sends HTML error page,
        // response.json() itself will crash.
        //
        // ==================================

        const rawResponse =
            await response.text();


        console.log(
            "HTTP Status:",
            response.status
        );

        console.log(
            "Raw Backend Response:",
            rawResponse
        );


        // ==================================
        // Parse JSON
        // ==================================

        let data;

        try {

            data =
                JSON.parse(
                    rawResponse
                );

        }

        catch (jsonError) {

            throw new Error(

                `Server returned ${response.status} ` +
                `instead of JSON.\n\n` +
                rawResponse.substring(
                    0,
                    500
                )

            );

        }


        // ==================================
        // Backend error
        // ==================================

        if (!response.ok) {

            throw new Error(

                data.details ||
                data.error ||
                `Server error: ${response.status}`

            );

        }


        console.log(
            "✅ Backend response:",
            data
        );


        // ==================================
        // Language information
        // ==================================

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


        // ==================================
        // Source count
        // ==================================

        const totalSources =
            Number(
                data.source_count || 0
            );


        if (sourceCount) {

            sourceCount.textContent =
                `${totalSources} Sources`;

        }


        // ==================================
        // No sources
        // ==================================

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
                            but no webpage
                            could be read.
                        </p>

                        <br>

                        <p>

                            🔎 Query:

                            <strong>
                                ${escapeHTML(
                                    data.search_query ||
                                    text
                                )}
                            </strong>

                        </p>

                        <br>

                        <p>

                            💡 Check the Render
                            logs for search
                            and page-reading errors.

                        </p>

                    </div>

                `;

            }

            return;

        }


        // ==================================
        // Main HTML
        // ==================================

        let html = "";


        // ==================================
        // Language
        // ==================================

        html +=
            languageText;


        // ==================================
        // AI Summary
        // ==================================

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


        // ==================================
        // Research Result
        // ==================================

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


        // ==================================
        // Sources title
        // ==================================

        html += `

            <div class="sources-title">

                🔗 Sources

            </div>

        `;


        // ==================================
        // Display sources
        // ==================================

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


        // ==================================
        // Render result
        // ==================================

        if (summary) {

            summary.innerHTML =
                html;

        }


        console.log(
            "================================"
        );

        console.log(
            "✅ RESEARCH COMPLETED"
        );

        console.log(
            "Sources:",
            totalSources
        );

        console.log(
            "================================"
        );

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


        if (summary) {

            summary.innerHTML = `

                <div class="error-box">

                    <h3>
                        ❌ Research failed
                    </h3>

                    <p>

                        ${escapeHTML(
                            error.message ||
                            "Unknown error"
                        )}

                    </p>

                    <br>

                    <p>

                        🔗 Backend:

                        <br>

                        <code>
                            ${escapeHTML(
                                API_URL
                            )}
                        </code>

                    </p>

                    <br>

                    <p>

                        💡 Open the backend
                        health URL to check
                        whether Render is online.

                    </p>

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


// ==========================================
// Format AI Text
// ==========================================

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


// ==========================================
// Escape HTML
// ==========================================

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


// ==========================================
// Escape URL Attribute
// ==========================================

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
