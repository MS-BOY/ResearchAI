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
// Research Button
// ==========================================

button.addEventListener(
    "click",
    async function () {

        const text =
            question.value.trim();


        // Empty question
        if (!text) {

            alert(
                "Please enter a question."
            );

            return;
        }


        // Show result
        result.classList.remove(
            "hidden"
        );


        // Loading state
        button.disabled = true;

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

            </div>

        `;


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
            // Send request to Python
            // ==================================

            const response =
                await fetch(
                    "http://127.0.0.1:5000/research",
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
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


            // ==================================
            // Error check
            // ==================================

            if (!response.ok) {

                throw new Error(

                    data.error ||
                    "Research failed"

                );

            }


            console.log(
                "Backend response:",
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
            // Source Count
            // ==================================

            sourceCount.textContent =
                `${data.source_count || 0} Sources`;


            // ==================================
            // No Sources
            // ==================================

            if (

                !data.sources ||

                data.sources.length === 0

            ) {

                summary.innerHTML = `

                    ${languageText}

                    <div class="error-box">

                        <p>
                            ❌ কোনো readable
                            source পাওয়া যায়নি।
                        </p>

                    </div>

                `;

                return;

            }


            // ==================================
            // AI SUMMARY
            // ==================================

            let html = "";


            html += languageText;


            /*
             * Backend যদি AI summary পাঠায়
             * তাহলে সেটাই প্রথমে দেখাবে।
             */

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


            // ==================================
            // Research Information
            // ==================================

            html += `

                <div class="research-intro">

                    <h2>
                        📚 Research Result
                    </h2>

                    <p>

                        মোট

                        <strong>
                            ${data.source_count}
                        </strong>

                        টি source পাওয়া গেছে।

                    </p>

                </div>

            `;


            // ==================================
            // Sources
            // ==================================

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


                    html += `

                        <div class="source">

                            <h3>

                                ${index + 1}.
                                ${escapeHTML(
                                    source.title ||
                                    "Untitled source"
                                )}

                            </h3>


                            ${
                                source.text
                                ? `

                                    <p>

                                        ${escapeHTML(
                                            source.text
                                        )}

                                    </p>

                                `
                                : `
                                    <p>
                                        No readable
                                        text found.
                                    </p>
                                `
                            }


                            <a
                                href="${escapeAttribute(
                                    source.url
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
            // Show result
            // ==================================

            summary.innerHTML =
                html;


        }

        catch (error) {

            console.error(
                "Research Error:",
                error
            );


            sourceCount.textContent =
                "Error";


            summary.innerHTML = `

                <div class="error-box">

                    <h3>
                        ❌ Research failed
                    </h3>

                    <p>

                        Backend-এর সাথে
                        connection অথবা
                        research process-এ
                        সমস্যা হয়েছে।

                    </p>

                    <br>

                    <p>
                        Python server চালু আছে
                        কিনা নিশ্চিত করো।
                    </p>

                    <br>

                    <code>

                        venv\\Scripts\\python.exe
                        backend\\app.py

                    </code>

                </div>

            `;

        }


        finally {

            button.disabled =
                false;

            button.textContent =
                "Research →";

        }

    }
);


// ==========================================
// Format AI Text
// ==========================================

function formatText(text) {

    if (!text) {

        return "";

    }


    return escapeHTML(
        text
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


// ==========================================
// Escape HTML
// ==========================================

function escapeHTML(text) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        text;

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
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
