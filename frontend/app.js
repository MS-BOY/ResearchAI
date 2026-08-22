// ==========================================
// Research AI - Frontend App
// ==========================================

// ==========================================
// DOM Elements
// ==========================================

const button = document.getElementById("researchBtn");
const question = document.getElementById("question");
const result = document.getElementById("result");
const summary = document.getElementById("summary");
const sourceCount = document.getElementById("sourceCount");
const language = document.getElementById("language");


// ==========================================
// API URL
// ==========================================
//
// Frontend এবং Flask একই Render service-এ থাকলে:
//
// /research
//
// Local development-এ:
// http://127.0.0.1:5000/research
//
// ==========================================

const API_URL = "/research";


// ==========================================
// Event Listeners
// ==========================================

if (button) {

    button.addEventListener(
        "click",
        startResearch
    );

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
// Main Research Function
// ==========================================

async function startResearch() {

    const text = question
        ? question.value.trim()
        : "";


    // ======================================
    // Validate Question
    // ======================================

    if (!text) {

        alert(
            "Please enter a question."
        );

        return;

    }


    // ======================================
    // Show Result
    // ======================================

    if (result) {

        result.classList.remove(
            "hidden"
        );

    }


    // ======================================
    // Loading State
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
                    ✍️ Summary তৈরি করা হচ্ছে...
                </p>

            </div>
        `;

    }


    try {

        // ==================================
        // Selected Language
        // ==================================

        const selectedLanguage =
            language
                ? language.value
                : "auto";


        console.log(
            "Question:",
            text
        );

        console.log(
            "Language:",
            selectedLanguage
        );


        // ==================================
        // Send Request
        // ==================================

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
        // Read Response
        // ==================================

        const contentType =
            response.headers.get(
                "content-type"
            );


        let data;


        if (
            contentType &&
            contentType.includes(
                "application/json"
            )
        ) {

            data =
                await response.json();

        }

        else {

            const rawText =
                await response.text();

            throw new Error(
                "Server returned non-JSON response: " +
                rawText.substring(0, 300)
            );

        }


        console.log(
            "Backend response:",
            data
        );


        // ==================================
        // Error Check
        // ==================================

        if (!response.ok) {

            throw new Error(

                data.error ||
                "Research failed"

            );

        }


        // ==================================
        // Answer Language
        // ==================================

        let languageHTML = "";


        if (
            data.answer_language
        ) {

            languageHTML = `
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
        // Source Count
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
        // No Sources
        // ==================================

        if (
            sources.length === 0
        ) {

            if (summary) {

                summary.innerHTML = `

                    ${languageHTML}

                    <div class="error-box">

                        <h3>
                            ❌ কোনো readable source পাওয়া যায়নি
                        </h3>

                        <p>
                            Internet থেকে
                            readable information
                            পাওয়া যায়নি।
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

        html += languageHTML;


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
        // Intent Information
        // ==================================

        if (
            Array.isArray(
                data.intents
            ) &&
            data.intents.length > 0
        ) {

            html += `

                <div class="research-intro">

                    <h2>
                        🎯 Question Analysis
                    </h2>

                    <p>

                        ${data.intents
                            .map(
                                function (intent) {

                                    return `
                                        <span class="intent-tag">
                                            ${escapeHTML(intent)}
                                        </span>
                                    `;

                                }
                            )
                            .join(" ")
                        }

                    </p>

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


            if (
                sections.length > 0
            ) {

                html += `

                    <div class="structured-research">

                        <div class="sources-title">

                            📌 Detailed Information

                        </div>

                `;


                sections.forEach(
                    function (
                        entry
                    ) {

                        const intent =
                            entry[0];

                        const content =
                            entry[1];


                        if (
                            !content
                        ) {

                            return;

                        }


                        html += `

                            <div class="structured-section">

                                <h3>

                                    ${escapeHTML(
                                        intent
                                    )}

                                </h3>

                                <div>

                                    ${formatText(
                                        content
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

                        🎥 YouTube / Video Examples

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

                                ▶ Watch video →

                            </a>

                        </div>

                    `;

                }
            );


            html += `

                </div>

            `;

        }


        // ==================================
        // Sources Title
        // ==================================

        html += `

            <div class="sources-title">

                🔗 Sources

            </div>

        `;


        // ==================================
        // Display Sources
        // ==================================

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
                    "No readable text found.";


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
                                ? "▶ Watch source →"
                                : "Open source →"
                            }

                        </a>

                    </div>

                `;

            }
        );


        // ==================================
        // Show Final Result
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
            "Research Error:",
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

                        Backend অথবা
                        Render API-তে
                        সমস্যা হয়েছে।

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


    // Markdown bold
    safeText =
        safeText.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    // Normalize line breaks
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
// Detect Video Source
// ==========================================

function isVideoSource(url) {

    if (!url) {

        return false;

    }


    const value =
        String(url)
            .toLowerCase();


    return (

        value.includes(
            "youtube.com"
        ) ||

        value.includes(
            "youtu.be"
        ) ||

        value.includes(
            "vimeo.com"
        ) ||

        value.includes(
            "dailymotion.com"
        )

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
