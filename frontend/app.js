"use strict";

// ============================================================
// DOM
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

const isLocal =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";

const BACKEND_URL = isLocal
    ? "http://127.0.0.1:5000"
    : window.location.origin;

const RESEARCH_URL = BACKEND_URL + "/research";
const HEALTH_URL = BACKEND_URL + "/api/health";

console.log("Research Backend:", BACKEND_URL);


// ============================================================
// BACKEND HEALTH
// ============================================================

async function checkBackend() {

    try {

        const response = await fetch(
            HEALTH_URL,
            {
                method: "GET",
                cache: "no-store"
            }
        );

        const data = await response.json();

        console.log("Backend health:", data);

        if (!response.ok) {
            return false;
        }

        if (data.tools_loaded === false) {

            console.error(
                "Backend online, but tools_loaded = false"
            );

            console.error(
                "Import error:",
                data.tool_import_error
            );

            return false;
        }

        return true;

    } catch (error) {

        console.error(
            "Health check failed:",
            error
        );

        return false;
    }
}


// ============================================================
// RESEARCH
// ============================================================

async function startResearch() {

    if (!question) {
        console.error("Question input not found");
        return;
    }

    const text = question.value.trim();

    if (!text) {

        alert(
            "Please enter a research question."
        );

        question.focus();

        return;
    }


    if (result) {
        result.classList.remove("hidden");
    }


    setLoading(true);


    try {

        const selectedLanguage =
            language
                ? language.value
                : "auto";


        console.log("Question:", text);
        console.log("Language:", selectedLanguage);
        console.log("Request:", RESEARCH_URL);


        const response = await fetch(
            RESEARCH_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    question: text,
                    language: selectedLanguage
                })
            }
        );


        const contentType =
            response.headers.get("content-type") || "";


        let data;


        if (
            contentType.indexOf(
                "application/json"
            ) !== -1
        ) {

            data = await response.json();

        } else {

            const raw =
                await response.text();

            console.error(
                "Backend returned:",
                raw
            );

            throw new Error(
                "Backend did not return JSON. HTTP " +
                response.status
            );
        }


        console.log(
            "Backend response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.details ||
                data.error ||
                "Research failed"
            );
        }


        if (data.success === false) {

            throw new Error(
                data.details ||
                data.error ||
                "Research failed"
            );
        }


        // ====================================================
        // SOURCE COUNT
        // ====================================================

        const totalSources =
            Number(data.source_count || 0);


        if (sourceCount) {

            sourceCount.textContent =
                totalSources + " Sources";
        }


        // ====================================================
        // RESULT HTML
        // ====================================================

        let html = "";


        // Language

        if (data.answer_language) {

            html +=
                '<div class="language-info">' +
                '🌐 Answer language: ' +
                '<strong>' +
                escapeHTML(
                    data.answer_language
                ) +
                '</strong>' +
                '</div>';
        }


        // Summary

        if (data.summary) {

            html +=
                '<div class="ai-summary">' +

                '<div class="summary-title">' +
                '🧠 AI Summary' +
                '</div>' +

                '<div class="summary-content">' +
                formatText(
                    data.summary
                ) +
                '</div>' +

                '</div>';
        }


        // Research information

        html +=
            '<div class="research-intro">' +

            '<h2>📚 Research Result</h2>' +

            '<p>' +
            'মোট <strong>' +
            totalSources +
            '</strong> টি readable source পাওয়া গেছে।' +
            '</p>' +

            '</div>';


        // ====================================================
        // STRUCTURED DATA
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

                html +=
                    '<div class="structured-research">' +
                    '<div class="sources-title">' +
                    '📊 Research Analysis' +
                    '</div>';


                sections.forEach(
                    function (item) {

                        const key = item[0];
                        const value = item[1];

                        if (!value) {
                            return;
                        }


                        html +=
                            '<div class="research-section">' +

                            '<h3>' +
                            escapeHTML(
                                formatIntentName(
                                    key
                                )
                            ) +
                            '</h3>' +

                            '<div>' +
                            formatText(value) +
                            '</div>' +

                            '</div>';
                    }
                );


                html +=
                    '</div>';
            }
        }


        // ====================================================
        // SOURCES
        // ====================================================

        if (
            Array.isArray(data.sources) &&
            data.sources.length > 0
        ) {

            html +=
                '<div class="sources-title">' +
                '🔗 Sources' +
                '</div>';


            data.sources.forEach(
                function (source, index) {

                    const title =
                        source.title ||
                        "Untitled source";

                    const url =
                        source.url ||
                        "#";

                    const text =
                        source.text ||
                        "No readable text found.";


                    html +=
                        '<div class="source">' +

                        '<h3>' +
                        (index + 1) +
                        '. ' +
                        escapeHTML(title) +
                        '</h3>' +

                        '<p>' +
                        escapeHTML(text) +
                        '</p>' +

                        '<a href="' +
                        escapeAttribute(url) +
                        '" target="_blank" ' +
                        'rel="noopener noreferrer">' +
                        'Open source →' +
                        '</a>' +

                        '</div>';
                }
            );

        } else {

            html +=
                '<div class="error-box">' +
                '<p>' +
                '⚠️ Search completed, but no readable webpage was returned.' +
                '</p>' +
                '</div>';
        }


        // Processing time

        if (data.processing_time) {

            html +=
                '<div class="processing-time">' +
                '⏱️ Processing time: ' +
                escapeHTML(
                    String(
                        data.processing_time
                    )
                ) +
                ' seconds' +
                '</div>';
        }


        // Display

        if (summary) {

            summary.innerHTML =
                html;
        }


    } catch (error) {

        console.error(
            "Research Error:",
            error
        );


        if (sourceCount) {
            sourceCount.textContent =
                "Error";
        }


        if (summary) {

            summary.innerHTML =
                '<div class="error-box">' +

                '<h3>❌ Research failed</h3>' +

                '<p>' +
                escapeHTML(
                    error.message ||
                    "Unknown error"
                ) +
                '</p>' +

                '<br>' +

                '<p>🔗 Backend:</p>' +

                '<code>' +
                escapeHTML(
                    RESEARCH_URL
                ) +
                '</code>' +

                '</div>';
        }

    } finally {

        setLoading(false);
    }
}


// ============================================================
// LOADING
// ============================================================

function setLoading(loading) {

    if (button) {

        button.disabled =
            loading;

        button.textContent =
            loading
                ? "Researching..."
                : "Research →";
    }


    if (loading && sourceCount) {

        sourceCount.textContent =
            "Searching...";
    }


    if (loading && summary) {

        summary.innerHTML =
            '<div class="loading">' +

            '<p>🔎 ইন্টারনেটে খোঁজা হচ্ছে...</p>' +

            '<br>' +

            '<p>📖 বিভিন্ন webpage পড়া হচ্ছে...</p>' +

            '<br>' +

            '<p>🧠 তথ্য বিশ্লেষণ করা হচ্ছে...</p>' +

            '</div>';
    }
}


// ============================================================
// FORMAT TEXT
// ============================================================

function formatText(text) {

    if (
        text === null ||
        text === undefined
    ) {
        return "";
    }


    return escapeHTML(
        String(text)
    )
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");
}


// ============================================================
// FORMAT INTENT
// ============================================================

function formatIntentName(name) {

    return String(name || "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, function (char) {
            return char.toUpperCase();
        });
}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        String(text || "");

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
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}


// ============================================================
// BUTTON
// ============================================================

if (button) {

    button.addEventListener(
        "click",
        startResearch
    );
}


// ============================================================
// CTRL + ENTER
// ============================================================

if (question) {

    question.addEventListener(
        "keydown",
        function (event) {

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
// GLOBAL OBJECT
// ============================================================

window.ResearchAI = {
    backend: BACKEND_URL,
    research: RESEARCH_URL,
    health: HEALTH_URL,
    checkBackend: checkBackend,
    startResearch: startResearch
};


console.log(
    "✅ Research AI JavaScript loaded"
);

checkBackend();
