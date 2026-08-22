// ==========================================
// DOM
// ==========================================

const button = document.getElementById("researchBtn");
const question = document.getElementById("question");
const result = document.getElementById("result");
const summary = document.getElementById("summary");
const sourceCount = document.getElementById("sourceCount");
const language = document.getElementById("language");


// ==========================================
// API
// ==========================================

const API_URL = "/research";


// ==========================================
// Events
// ==========================================

if (button) {
    button.addEventListener("click", startResearch);
}

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
// Main Research
// ==========================================

async function startResearch() {

    const text = question
        ? question.value.trim()
        : "";


    if (!text) {

        alert(
            "Please enter a question."
        );

        return;
    }


    if (result) {

        result.classList.remove(
            "hidden"
        );
    }


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

                <p>🔎 Searching the internet...</p>

                <p>📖 Reading sources...</p>

                <p>🧠 Analyzing information...</p>

                <p>✍️ Creating summary...</p>

            </div>

        `;
    }


    try {

        const selectedLanguage =
            language
                ? language.value
                : "auto";


        console.log(
            "🔎 Question:",
            text
        );


        console.log(
            "🌐 Language:",
            selectedLanguage
        );


        const response = await fetch(
            API_URL,
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


        // ==================================
        // Read response safely
        // ==================================

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

            data = await response.json();

        } else {

            const raw =
                await response.text();

            throw new Error(
                `Server returned non-JSON response (${response.status}): ${raw.slice(0, 300)}`
            );
        }


        console.log(
            "📦 Backend response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `Research failed (${response.status})`
            );
        }


        // ==================================
        // Language
        // ==================================

        const answerLanguage =
            data.answer_language ||
            selectedLanguage ||
            "auto";


        const languageText = `

            <div class="language-info">

                🌐 Answer language:

                <strong>

                    ${escapeHTML(
                        answerLanguage
                    )}

                </strong>

            </div>

        `;


        // ==================================
        // Sources
        // ==================================

        const sources =
            Array.isArray(data.sources)
                ? data.sources
                : [];


        const totalSources =
            Number(
                data.source_count ||
                sources.length ||
                0
            );


        if (sourceCount) {

            sourceCount.textContent =
                `${totalSources} Sources`;
        }


        // ==================================
        // No readable source
        // ==================================

        if (
            sources.length === 0
        ) {

            if (summary) {

                summary.innerHTML = `

                    ${languageText}

                    <div class="error-box">

                        <h3>
                            ⚠️ No readable sources
                        </h3>

                        <p>

                            Search completed, but
                            no webpage could be read.

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

                            💡 Check the Render logs
                            for "Search HTTP",
                            "Search results" and
                            "Page HTTP".

                        </p>

                    </div>

                `;
            }

            return;
        }


        // ==================================
        // Build HTML
        // ==================================

        let html = "";

        html += languageText;


        // ==================================
        // AI Summary
        // ==================================

        if (
            data.summary &&
            String(data.summary).trim()
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
        // Research Info
        // ==================================

        html += `

            <div class="research-intro">

                <h2>
                    📚 Research Result
                </h2>

                <p>

                    ${totalSources}
                    readable source(s)
                    found.

                </p>

            </div>

        `;


        // ==================================
        // Structured Research
        // ==================================

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

                            🧠 Research Details

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


                html += `</div>`;
            }
        }


        // ==================================
        // Video Sources
        // ==================================

        const videoSources =
            sources.filter(
                function (source) {

                    return isVideoSource(
                        source.url
                    );
                }
            );


        if (
            videoSources.length > 0
        ) {

            html += `

                <div class="video-section">

                    <div class="sources-title">

                        🎥 Video Sources

                    </div>

            `;


            videoSources.forEach(
                function (
                    source,
                    index
                ) {

                    html += `

                        <div class="video-source">

                            <h3>

                                ${index + 1}.
                                ${escapeHTML(
                                    source.title ||
                                    "Video"
                                )}

                            </h3>

                            <a
                                href="${escapeAttribute(
                                    source.url
                                )}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >

                                ▶ Open video →

                            </a>

                        </div>

                    `;
                }
            );


            html += `</div>`;
        }


        // ==================================
        // Sources
        // ==================================

        html += `

            <div class="sources-title">

                🔗 Sources

            </div>

        `;


        sources.forEach(
            function (
                source,
                index
            ) {

                const title =
                    source.title ||
                    "Untitled source";


                const text =
                    source.text ||
                    "No readable text.";


                const url =
                    source.url ||
                    "#";


                const video =
                    isVideoSource(
                        url
                    );


                html += `

                    <div class="source">

                        <h3>

                            ${index + 1}.
                            ${escapeHTML(
                                title
                            )}

                        </h3>

                        ${
                            video
                            ? `
                                <div class="video-badge">
                                    🎥 Video source
                                </div>
                            `
                            : ""
                        }

                        <p>

                            ${escapeHTML(
                                text
                            )}

                        </p>

                        <a
                            href="${escapeAttribute(
                                url
                            )}"
                            target="_blank"
                            rel="noopener noreferrer"
                        >

                            ${
                                video
                                ? "▶ Open video →"
                                : "Open source →"
                            }

                        </a>

                    </div>

                `;
            }
        );


        // ==================================
        // Display
        // ==================================

        if (summary) {

            summary.innerHTML =
                html;
        }


        console.log(
            "✅ Research completed"
        );
    }


    catch (error) {

        console.error(
            "❌ Research error:",
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

                </div>

            `;
        }
    }


    finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Research →";
        }
    }
}


// ==========================================
// Format Intent
// ==========================================

function formatIntentName(value) {

    return String(value || "")
        .replace(/[_-]/g, " ")
        .replace(/\b\w/g, function (char) {
            return char.toUpperCase();
        });
}


// ==========================================
// Format Text
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
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
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
// Video Detection
// ==========================================

function isVideoSource(url) {

    if (!url) {
        return false;
    }


    const value =
        String(url).toLowerCase();


    return (
        value.includes("youtube.com") ||
        value.includes("youtu.be") ||
        value.includes("vimeo.com") ||
        value.includes("dailymotion.com")
    );
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
// Escape Attribute
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
