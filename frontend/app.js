// ============================================================
// RESEARCH AI FRONTEND
// Local + Render Production Ready
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
// API CONFIG
// ============================================================
//
// Local:
// http://127.0.0.1:5000/research
//
// Render:
// /research
//
// Same frontend/backend Render service হলে
// relative URL ব্যবহার করাই সবচেয়ে ভালো.
// ============================================================

const IS_LOCAL =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost";

const API_BASE_URL = IS_LOCAL
    ? "http://127.0.0.1:5000"
    : "";

const RESEARCH_API =
    `${API_BASE_URL}/research`;


// ============================================================
// BASIC VALIDATION
// ============================================================

if (!button || !question || !result || !summary || !sourceCount) {

    console.error(
        "❌ Required Research AI elements not found."
    );

}


// ============================================================
// RESEARCH BUTTON
// ============================================================

if (button) {

    button.addEventListener(
        "click",
        runResearch
    );

}


// ============================================================
// ENTER KEY SUPPORT
// ============================================================

if (question) {

    question.addEventListener(
        "keydown",
        function (event) {

            // Ctrl + Enter / Cmd + Enter
            if (
                event.key === "Enter" &&
                (event.ctrlKey || event.metaKey)
            ) {

                event.preventDefault();

                runResearch();

            }

        }
    );

}


// ============================================================
// MAIN RESEARCH FUNCTION
// ============================================================

async function runResearch() {

    const text =
        question.value.trim();


    // ========================================================
    // EMPTY QUESTION
    // ========================================================

    if (!text) {

        showError(
            "Please enter a question."
        );

        question.focus();

        return;

    }


    // ========================================================
    // QUESTION LENGTH
    // Backend limit = 5000
    // ========================================================

    if (text.length > 5000) {

        showError(
            "Question is too long. Maximum 5000 characters allowed."
        );

        return;

    }


    // ========================================================
    // SHOW RESULT
    // ========================================================

    result.classList.remove(
        "hidden"
    );


    // ========================================================
    // LOADING STATE
    // ========================================================

    setLoadingState();


    try {

        // ====================================================
        // SELECTED LANGUAGE
        // ====================================================

        const selectedLanguage =
            language
                ? language.value
                : "auto";


        console.log(
            "================================"
        );

        console.log(
            "🤖 Research AI Request"
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
            RESEARCH_API
        );

        console.log(
            "================================"
        );


        // ====================================================
        // SEND REQUEST
        // ====================================================

        const response =
            await fetch(
                RESEARCH_API,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body: JSON.stringify({

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

        const data =
            await readBackendResponse(
                response
            );


        console.log(
            "✅ Backend response:",
            data
        );


        // ====================================================
        // HTTP ERROR
        // ====================================================

        if (!response.ok) {

            throw new Error(

                data?.error ||
                data?.details ||
                `Research failed (${response.status})`

            );

        }


        // ====================================================
        // BACKEND SUCCESS CHECK
        // ====================================================

        if (
            data.success === false
        ) {

            throw new Error(

                data.error ||
                "Research failed."

            );

        }


        // ====================================================
        // DISPLAY RESULT
        // ====================================================

        renderResearchResult(
            data
        );


    }

    catch (error) {

        console.error(
            "❌ Research Error:",
            error
        );


        showBackendError(
            error
        );

    }

    finally {

        // ====================================================
        // RESTORE BUTTON
        // ====================================================

        button.disabled =
            false;

        button.textContent =
            "Research →";

    }

}


// ============================================================
// READ BACKEND RESPONSE
// ============================================================

async function readBackendResponse(
    response
) {

    const contentType =
        response.headers.get(
            "content-type"
        ) || "";


    // ========================================================
    // JSON RESPONSE
    // ========================================================

    if (
        contentType
            .toLowerCase()
            .includes(
                "application/json"
            )
    ) {

        try {

            return await response.json();

        }

        catch (error) {

            console.error(
                "❌ Invalid JSON:",
                error
            );

            throw new Error(
                "Backend returned invalid JSON."
            );

        }

    }


    // ========================================================
    // HTML / TEXT RESPONSE
    // ========================================================

    const raw =
        await response.text();


    console.error(
        "❌ Backend returned non-JSON response:",
        raw
    );


    // Render / proxy errors can return HTML
    if (
        raw.toLowerCase().includes(
            "<html"
        )
    ) {

        throw new Error(

            `Server returned ${response.status}. ` +
            "The backend may be unavailable or timed out."

        );

    }


    throw new Error(

        raw ||
        `Server returned ${response.status}.`

    );

}


// ============================================================
// LOADING UI
// ============================================================

function setLoadingState() {

    button.disabled =
        true;

    button.textContent =
        "Researching...";


    sourceCount.textContent =
        "Searching...";


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
                ⏳ কিছু সময় লাগতে পারে...
            </p>

        </div>

    `;

}


// ============================================================
// RENDER RESEARCH RESULT
// ============================================================

function renderResearchResult(
    data
) {

    // ========================================================
    // LANGUAGE
    // ========================================================

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


    // ========================================================
    // SOURCE COUNT
    // ========================================================

    const sources =
        Array.isArray(
            data.sources
        )
            ? data.sources
            : [];


    const count =
        Number.isFinite(
            Number(
                data.source_count
            )
        )
            ? Number(
                data.source_count
            )
            : sources.length;


    sourceCount.textContent =
        `${count} Sources`;


    // ========================================================
    // NO SOURCES
    // ========================================================

    if (
        sources.length === 0
    ) {

        summary.innerHTML = `

            ${languageText}

            <div class="error-box">

                <p>
                    ❌ কোনো readable source পাওয়া যায়নি।
                </p>

                <br>

                <p>
                    Search query:
                    <strong>
                        ${escapeHTML(
                            data.search_query ||
                            data.question ||
                            ""
                        )}
                    </strong>
                </p>

            </div>

        `;

        return;

    }


    // ========================================================
    // BUILD HTML
    // ========================================================

    let html = "";


    // Language
    html +=
        languageText;


    // ========================================================
    // AI SUMMARY
    // ========================================================

    if (
        data.summary
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


    // ========================================================
    // RESEARCH INFORMATION
    // ========================================================

    html += `

        <div class="research-intro">

            <h2>
                📚 Research Result
            </h2>

            <p>

                মোট

                <strong>
                    ${count}
                </strong>

                টি source পাওয়া গেছে।

            </p>

        </div>

    `;


    // ========================================================
    // SEARCH QUERY
    // ========================================================

    if (
        data.search_query
    ) {

        html += `

            <div class="search-query">

                🔎 Search query:

                <strong>
                    ${escapeHTML(
                        data.search_query
                    )}
                </strong>

            </div>

        `;

    }


    // ========================================================
    // SOURCES TITLE
    // ========================================================

    html += `

        <div class="sources-title">

            🔗 Sources

        </div>

    `;


    // ========================================================
    // SOURCE CARDS
    // ========================================================

    sources.forEach(
        function (
            source,
            index
        ) {

            const title =
                source &&
                source.title
                    ? source.title
                    : "Untitled source";


            const url =
                source &&
                source.url
                    ? source.url
                    : "#";


            const text =
                source &&
                source.text
                    ? source.text
                    : "";


            html += `

                <div class="source">

                    <h3>

                        ${index + 1}.
                        ${escapeHTML(
                            title
                        )}

                    </h3>


                    ${
                        text

                        ? `

                            <p>

                                ${escapeHTML(
                                    text
                                )}

                            </p>

                        `

                        : `

                            <p>
                                No readable text found.
                            </p>

                        `
                    }


                    <a
                        href="${escapeAttribute(
                            url
                        )}"
                        target="_blank"
                        rel="noopener noreferrer nofollow"
                    >

                        Open source →

                    </a>

                </div>

            `;

        }
    );


    // ========================================================
    // DISPLAY
    // ========================================================

    summary.innerHTML =
        html;

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

        // Paragraph breaks
        .replace(
            /\n\s*\n/g,
            "<br><br>"
        )

        // Single line breaks
        .replace(
            /\n/g,
            "<br>"
        );

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHTML(
    text
) {

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
// SHOW SIMPLE ERROR
// ============================================================

function showError(
    message
) {

    if (!summary) {

        alert(
            message
        );

        return;

    }


    result.classList.remove(
        "hidden"
    );


    sourceCount.textContent =
        "Error";


    summary.innerHTML = `

        <div class="error-box">

            <h3>
                ❌ Error
            </h3>

            <p>
                ${escapeHTML(
                    message
                )}
            </p>

        </div>

    `;

}


// ============================================================
// BACKEND ERROR UI
// ============================================================

function showBackendError(
    error
) {

    const message =
        error &&
        error.message

            ? error.message

            : "Unknown backend error.";


    sourceCount.textContent =
        "Error";


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

                Backend-এর সাথে connection
                অথবা research process-এ সমস্যা হয়েছে।

            </p>

            ${
                IS_LOCAL

                    ? `

                        <br>

                        <p>
                            Python server চালু আছে কিনা নিশ্চিত করো:
                        </p>

                        <br>

                        <code>
                            venv\\Scripts\\python.exe backend\\app.py
                        </code>

                    `

                    : `

                        <br>

                        <p>
                            Render backend সাময়িকভাবে
                            unavailable বা timeout হতে পারে।
                        </p>

                    `
            }

        </div>

    `;

}


// ============================================================
// DEBUG INFO
// ============================================================

console.log(
    "🚀 Research AI frontend loaded."
);

console.log(
    "🌐 Environment:",
    IS_LOCAL
        ? "LOCAL"
        : "PRODUCTION"
);

console.log(
    "🔗 Research API:",
    RESEARCH_API
);
