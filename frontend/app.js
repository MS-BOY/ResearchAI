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
// Render:
// /research
//
// Local যদি Flask frontend serve করে:
// /research
//
// আলাদা frontend server হলে:
// http://127.0.0.1:5000/research
// ==========================================

const API_URL = "/research";


// ==========================================
// Button Event
// ==========================================

if (button) {

    button.addEventListener(
        "click",
        startResearch
    );

}


// ==========================================
// Enter Key
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
            ) || "";


        if (
            !contentType.includes(
                "application/json"
            )
        ) {

            throw new Error(
                `Server returned ${response.status} instead of JSON.`
            );

        }


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
                `Research failed (${response.status})`

            );

        }


        // ==================================
        // Language Info
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
        // Structured Research
        // ==================================

        if (
            data.structured &&
            typeof data.structured === "object"
        ) {

            const structured =
                data.structured;


            const keys =
                Object.keys(
                    structured
                );


            if (keys.length > 0) {

                html += `

                    <div class="structured-research">

                        <div class="sources-title">

                            📋 Research Details

                        </div>

                `;


                keys.forEach(
                    function (key) {

                        const section =
                            structured[key];


                        if (
                            !section ||
                            !String(section).trim()
                        ) {

                            return;

                        }


                        const label =
                            getIntentLabel(
                                key
                            );


                        html += `

                            <div class="research-section">

                                <h3>

                                    ${escapeHTML(
                                        label
                                    )}

                                </h3>

                                <p>

                                    ${formatText(
                                        section
                                    )}

                                </p>

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
            sources.filter(
                function (source) {

                    return isVideoSource(
                        source.url
                    );

                }
            );


        // ==================================
        // YouTube / Video Examples
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

                    const videoTitle =
                        source.title ||
                        "Video Example";


                    const videoURL =
                        source.url ||
                        "#";


                    html += `

                        <div class="video-source">

                            <h3>

                                ${index + 1}.
                                ${escapeHTML(
                                    videoTitle
                                )}

                            </h3>

                            <a
                                href="${escapeAttribute(
                                    videoURL
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

                        Backend অথবা
                        research process-এ
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

    if (
        text === null ||
        text === undefined
    ) {

        return "";

    }


    let safeText =
        escapeHTML(
            String(text)
        );


    // Bold markdown
    safeText =
        safeText.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    // Normalize line endings
    safeText =
        safeText.replace(
            /\r\n/g,
            "\n"
        );


    // Multiple line breaks
    safeText =
        safeText.replace(
            /\n\n+/g,
            "<br><br>"
        );


    // Single line break
    safeText =
        safeText.replace(
            /\n/g,
            "<br>"
        );


    return safeText;

}


// ==========================================
// Video Source Detector
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
            "youtube-nocookie.com"
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
// Intent Label
// ==========================================

function getIntentLabel(intent) {

    const labels = {

        "biography":
            "👤 Biography",

        "birth":
            "🎂 Birth / Date of Birth",

        "age":
            "🔢 Age",

        "career":
            "💼 Career",

        "songs":
            "🎵 Songs",

        "movies":
            "🎬 Movies",

        "education":
            "🎓 Education",

        "family":
            "👨‍👩‍👧 Family",

        "awards":
            "🏆 Awards",

        "net_worth":
            "💰 Net Worth",

        "personal_life":
            "❤️ Personal Life"

    };


    return labels[intent] ||
        String(intent)
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
