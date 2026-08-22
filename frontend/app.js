```javascript
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
// Render এবং একই server-এ frontend/backend থাকলে
// শুধু "/research" ব্যবহার করতে হবে.
//
// Local:
// http://127.0.0.1:5000/research
//
// Render:
// /research
// ==========================================

const API_URL = "/research";


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
    // Empty Question
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
    // Loading
    // ======================================

    button.disabled = true;

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
            "Selected language:",
            selectedLanguage
        );


        // ==================================
        // Send Request To Backend
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

                    body: JSON.stringify({

                        question:
                            text,

                        language:
                            selectedLanguage

                    })

                }
            );


        // ==================================
        // Read JSON
        // ==================================

        const data =
            await response.json();


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
        // Language Information
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
        // Source Count
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
        // No Sources
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
        // Find Video Sources
        // ==================================

        const videoSources =
            data.sources.filter(
                function (source) {

                    return isVideoSource(
                        source.url
                    );

                }
            );


        // ==================================
        // Video Examples
        // ==================================

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

        data.sources.forEach(

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
        // Show Result
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

                        Backend server
                        চালু আছে কিনা
                        নিশ্চিত করো।

                    </p>

                </div>

            `;

        }

    }


    finally {

        button.disabled =
            false;

        button.textContent =
            "Research →";

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


    // Bold
    safeText =
        safeText.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    // Line breaks
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
// Escape URL
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
```
