
"use strict";

/*
 * SupportSense — Support Operations Center
 *
 * Sprint 8 UI layer.
 *
 * Backend contracts intentionally preserved:
 *
 *   GET  /health
 *   GET  /intents
 *   POST /predict
 *   POST /action/simulate
 *   POST /feedback
 *   GET  /predictions?limit=10
 *
 * Live events are identified by:
 *
 *   source_event_id != null
 *
 * Manual predictions are identified by:
 *
 *   source_event_id == null
 *
 * Confidence is intentionally NOT displayed because the current
 * prediction API does not expose a confidence value.
 */

const state = {
    predictions: [],
    currentPrediction: null,
    activeHistoryFilter: "all",

    historyPage: 1,
    historyPageSize: 10,

    reviewPage: 1,
    reviewPageSize: 10,

    livePage: 1,
    livePageSize: 10
};


/* ============================================================
 * NAVIGATION
 * ============================================================ */

function initializeNavigation() {
    const tabs = document.querySelectorAll(".nav-tab");
    const panels = document.querySelectorAll(".tab-panel");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const target = tab.dataset.tab;

            tabs.forEach((item) => {
                item.classList.toggle("active", item === tab);
            });

            panels.forEach((panel) => {
                panel.classList.toggle(
                    "active",
                    panel.id === `tab-${target}`
                );
            });

            if (target === "live") {
                loadLiveOperations();
            }

            if (target === "history") {
                loadPredictionHistory();
            }

            if (target === "review") {
                loadHumanReview();
            }

            if (target === "system") {
                updateSystemStatus();
            }
        });
    });
}


/* ============================================================
 * HEALTH
 * ============================================================ */

async function checkHealth() {
    const runnerStatus = document.getElementById("runner-status");

    try {
        const response = await fetch("/health");

        if (!response.ok) {
            throw new Error("Runner health check failed");
        }

        const data = await response.json();

        if (runnerStatus) {
            runnerStatus.textContent =
                data.status || "Healthy";
        }

        return data;

    } catch (error) {
        if (runnerStatus) {
            runnerStatus.textContent = "Unavailable";
        }

        console.error("Health check failed:", error);
        return null;
    }
}


/* ============================================================
 * SYSTEM STATUS
 * ============================================================ */

async function updateSystemStatus() {
    const health = await checkHealth();

    const kafka = document.getElementById("kafka-status");
    const spark = document.getElementById("spark-status");
    const model = document.getElementById("system-model-status");

    if (health) {
        if (kafka) {
            kafka.textContent = "Streaming pipeline available";
        }

        if (spark) {
            spark.textContent = "Streaming service available";
        }

        if (model) {
            model.textContent = "Serving model available";
        }
    } else {
        if (kafka) {
            kafka.textContent = "Status unavailable";
        }

        if (spark) {
            spark.textContent = "Status unavailable";
        }

        if (model) {
            model.textContent = "Status unavailable";
        }
    }
}


/* ============================================================
 * INTENTS
 * ============================================================ */

async function loadIntents() {
    const select = document.getElementById("actual-intent");

    if (!select) {
        return;
    }

    try {
        const response = await fetch("/intents");

        if (!response.ok) {
            throw new Error("Unable to load intents");
        }

        const data = await response.json();

        const intents =
            Array.isArray(data)
                ? data
                : data.intents || [];

        select.innerHTML =
            '<option value="">Select intent...</option>';

        intents.forEach((intent) => {
            const option = document.createElement("option");
            option.value = intent;
            option.textContent = intent;
            select.appendChild(option);
        });

    } catch (error) {
        console.error("Failed to load intents:", error);
    }
}


/* ============================================================
 * ACTION SIMULATION
 * ============================================================ */

async function simulateAction() {
    if (!state.currentPrediction) {
        return;
    }

    const resultElement =
        document.getElementById("action-result");

    const button =
        document.getElementById("action-button");

    try {
        button.disabled = true;
        button.textContent = "Simulating...";

        const response = await fetch("/action/simulate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                action_id:
                    state.currentPrediction.action_id,
                action_name:
                    state.currentPrediction.action_name
            })
        });

        if (!response.ok) {
            throw new Error("Action simulation failed");
        }

        const data = await response.json();

        if (resultElement) {
            resultElement.textContent =
                data.message ||
                data.simulation_message ||
                "Action simulation completed.";

            resultElement.classList.remove("hidden");
            resultElement.classList.add("success");
        }

    } catch (error) {
        console.error("Action simulation failed:", error);

        if (resultElement) {
            resultElement.textContent =
                error.message;

            resultElement.classList.remove("hidden");
            resultElement.classList.add("warning");
        }

    } finally {
        button.disabled = false;
        button.textContent = "Simulate Action";
    }
}


/* ============================================================
 * FEEDBACK
 * ============================================================ */

async function submitFeedback() {
    if (!state.currentPrediction) {
        return;
    }

    const actualIntent =
        document.getElementById("actual-intent");

    const resultElement =
        document.getElementById("feedback-result");

    const button =
        document.getElementById("feedback-button");

    if (!actualIntent || !actualIntent.value) {
        return;
    }

    try {
        button.disabled = true;
        button.textContent = "Submitting...";

        const response = await fetch("/feedback", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                event_id:
                    state.currentPrediction.event_id,
                actual_intent:
                    actualIntent.value
            })
        });

        if (!response.ok) {
            throw new Error("Feedback submission failed");
        }

        const data = await response.json();

        if (resultElement) {
            resultElement.textContent =
                data.message ||
                "Feedback submitted successfully.";

            resultElement.classList.remove("hidden");
            resultElement.classList.add("success");
        }

    } catch (error) {
        console.error("Feedback failed:", error);

        if (resultElement) {
            resultElement.textContent =
                error.message;

            resultElement.classList.remove("hidden");
            resultElement.classList.add("warning");
        }

    } finally {
        button.disabled = false;
        button.textContent = "Submit Feedback";
    }
}


/* ============================================================
 * MANUAL PREDICTION
 * ============================================================ */

async function predictTicket() {
    const input =
        document.getElementById("ticket-input");

    const resultCard =
        document.getElementById("result-card");

    const errorElement =
        document.getElementById("error-message");

    const button =
        document.getElementById("predict-button");

    if (!input || !input.value.trim()) {
        if (errorElement) {
            errorElement.textContent =
                "Please enter a support ticket.";
            errorElement.classList.remove("hidden");
        }
        return;
    }

    if (errorElement) {
        errorElement.classList.add("hidden");
    }

    try {
        button.disabled = true;
        button.textContent = "Predicting...";

        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ticket: input.value.trim()
            })
        });

        if (!response.ok) {
            throw new Error("Prediction request failed");
        }

        const data = await response.json();

        if (data.status !== "success") {
            throw new Error(
                data.message || "Prediction failed"
            );
        }

        state.currentPrediction = {
            event_id: data.event_id,
            source_event_id: data.source_event_id,
            ticket: data.ticket,
            predicted_intent: data.prediction,
            action_id:
                data.decision?.action_id || null,
            action_name:
                data.decision?.action_name || null,
            risk:
                data.decision?.risk || null,
            requires_approval:
                Boolean(
                    data.decision?.requires_approval
                ),
            model_name:
                data.model?.model_name || null,
            model_status:
                data.model?.status || null,
            experiment_name:
                data.model?.experiment_name || null,
            run_id:
                data.model?.run_id || null,
            model_id:
                data.model?.model_id || null
        };

        renderManualPrediction(state.currentPrediction);

        if (resultCard) {
            resultCard.classList.remove("hidden");
        }

        input.value = "";

        loadPredictionHistory();

    } catch (error) {
        console.error("Prediction failed:", error);

        if (errorElement) {
            errorElement.textContent =
                error.message;

            errorElement.classList.remove("hidden");
        }

    } finally {
        button.disabled = false;
        button.textContent = "Predict Ticket";
    }
}


/* ============================================================
 * MANUAL RESULT
 * ============================================================ */

function renderManualPrediction(prediction) {
    const intent =
        document.getElementById("predicted-intent");

    const risk =
        document.getElementById("risk-level");

    const approval =
        document.getElementById("approval-required");

    const action =
        document.getElementById("action-name");

    const model =
        document.getElementById("model-status");

    const actionButton =
        document.getElementById("action-button");

    const feedbackButton =
        document.getElementById("feedback-button");

    if (intent) {
        intent.textContent =
            prediction.predicted_intent || "—";
    }

    if (risk) {
        risk.textContent =
            prediction.risk || "—";
    }

    if (approval) {
        approval.textContent =
            prediction.requires_approval
                ? "REQUIRED"
                : "NOT REQUIRED";
    }

    if (action) {
        action.textContent =
            prediction.action_name || "—";
    }

    if (model) {
        model.textContent =
            prediction.model_status || "—";
    }

    if (actionButton) {
        actionButton.classList.toggle(
            "hidden",
            !prediction.action_id
        );
    }

    if (feedbackButton) {
        feedbackButton.disabled = false;
    }
}


/* ============================================================
 * PREDICTION HISTORY
 * ============================================================ */

async function loadPredictionHistory() {
    const container =
        document.getElementById("prediction-history");

    if (!container) {
        return;
    }

    try {
        const response = await fetch(
            "/predictions?limit=50"
        );

        if (!response.ok) {
            throw new Error(
                "Unable to load prediction history"
            );
        }

        const data = await response.json();

        state.predictions =
            data.predictions || [];

        renderHistory();
        updateLiveOperations();

    } catch (error) {
        console.error(
            "Prediction history failed:",
            error
        );

        container.innerHTML = `
            <div class="empty-state">
                <strong>Unable to load prediction history</strong>
                <span>${escapeHtml(error.message)}</span>
            </div>
        `;
    }
}


/* ============================================================
 * SOURCE CLASSIFICATION
 * ============================================================ */

function isLivePrediction(prediction) {
    return Boolean(prediction.source_event_id);
}

function isManualPrediction(prediction) {
    return !prediction.source_event_id;
}


/* ============================================================
 * HISTORY RENDERING
 * ============================================================ */

function renderHistory() {
    const container =
        document.getElementById("prediction-history");

    if (!container) {
        return;
    }

    let predictions =
        [...state.predictions];

    /* --------------------------------------------------------
     * Apply the selected history filter first.
     * Pagination is intentionally applied AFTER filtering.
     * -------------------------------------------------------- */

    if (state.activeHistoryFilter === "live") {
        predictions =
            predictions.filter(isLivePrediction);
    }

    if (state.activeHistoryFilter === "manual") {
        predictions =
            predictions.filter(isManualPrediction);
    }

    if (state.activeHistoryFilter === "review") {
        predictions =
            predictions.filter(
                (prediction) =>
                    Boolean(prediction.requires_approval)
            );
    }

    /* --------------------------------------------------------
     * Empty state
     * -------------------------------------------------------- */

    if (!predictions.length) {
        state.historyPage = 1;

        container.innerHTML = `
            <div class="empty-state">
                <strong>No matching predictions</strong>
                <span>
                    There are no records for the selected view.
                </span>
            </div>
        `;

        return;
    }

    /* --------------------------------------------------------
     * Pagination
     * -------------------------------------------------------- */

    const pageSize =
        state.historyPageSize;

    const totalPages =
        Math.max(
            1,
            Math.ceil(
                predictions.length / pageSize
            )
        );

    /*
     * Protect against a page becoming invalid after
     * filtering or refreshing the prediction history.
     */
    state.historyPage =
        Math.min(
            Math.max(
                state.historyPage,
                1
            ),
            totalPages
        );

    const startIndex =
        (state.historyPage - 1) * pageSize;

    const endIndex =
        Math.min(
            startIndex + pageSize,
            predictions.length
        );

    const pagePredictions =
        predictions.slice(
            startIndex,
            endIndex
        );

    /* --------------------------------------------------------
     * Render current page
     * -------------------------------------------------------- */

    container.innerHTML =
        pagePredictions
            .map(renderPredictionCard)
            .join("");

    /* --------------------------------------------------------
     * Pagination controls
     * -------------------------------------------------------- */

    container.insertAdjacentHTML(
        "beforeend",
        renderHistoryPagination(
            predictions.length,
            totalPages,
            startIndex,
            endIndex
        )
    );

    initializeHistoryPagination();
}

/* ============================================================
 * HISTORY PAGINATION
 * ============================================================ */

function renderHistoryPagination(
    totalRecords,
    totalPages,
    startIndex,
    endIndex
) {
    if (totalPages <= 1) {
        return "";
    }

    const currentPage =
        state.historyPage;

    const pageButtons =
        Array.from(
            { length: totalPages },
            (_, index) => {
                const page =
                    index + 1;

                return `
                    <button
                        type="button"
                        class="pagination-button ${
                            page === currentPage
                                ? "active"
                                : ""
                        }"
                        data-history-page="${page}"
                    >
                        ${page}
                    </button>
                `;
            }
        )
        .join("");

    return `
        <div class="history-pagination">

            <span class="pagination-summary">
                ${startIndex + 1}–${endIndex}
                of
                ${totalRecords}
            </span>

            <div class="pagination-controls">

                <button
                    type="button"
                    class="pagination-button"
                    data-history-page="${currentPage - 1}"
                    ${currentPage === 1 ? "disabled" : ""}
                >
                    Previous
                </button>

                ${pageButtons}

                <button
                    type="button"
                    class="pagination-button"
                    data-history-page="${currentPage + 1}"
                    ${currentPage === totalPages ? "disabled" : ""}
                >
                    Next
                </button>

            </div>

        </div>
    `;
}


function initializeHistoryPagination() {
    const buttons =
        document.querySelectorAll(
            "[data-history-page]"
        );

    buttons.forEach((button) => {
        button.addEventListener(
            "click",
            () => {

                const page =
                    Number(
                        button.dataset.historyPage
                    );

                if (!Number.isFinite(page)) {
                    return;
                }

                state.historyPage =
                    page;

                renderHistory();
            }
        );
    });
}



/* ============================================================
 * HUMAN REVIEW PAGINATION
 * ============================================================ */

function renderReviewPagination(
    totalRecords,
    totalPages,
    startIndex,
    endIndex
) {
    if (totalPages <= 1) {
        return "";
    }

    const currentPage =
        state.reviewPage;

    const pageButtons =
        Array.from(
            { length: totalPages },
            (_, index) => {
                const page =
                    index + 1;

                return `
                    <button
                        type="button"
                        class="pagination-button ${
                            page === currentPage
                                ? "active"
                                : ""
                        }"
                        data-review-page="${page}"
                    >
                        ${page}
                    </button>
                `;
            }
        )
        .join("");

    return `
        <div class="history-pagination review-pagination">

            <span class="pagination-summary">
                ${startIndex + 1}–${endIndex}
                of
                ${totalRecords}
            </span>

            <div class="pagination-controls">

                <button
                    type="button"
                    class="pagination-button"
                    data-review-page="${currentPage - 1}"
                    ${currentPage === 1 ? "disabled" : ""}
                >
                    Previous
                </button>

                ${pageButtons}

                <button
                    type="button"
                    class="pagination-button"
                    data-review-page="${currentPage + 1}"
                    ${currentPage === totalPages ? "disabled" : ""}
                >
                    Next
                </button>

            </div>

        </div>
    `;
}


function initializeReviewPagination() {
    const buttons =
        document.querySelectorAll(
            "[data-review-page]"
        );

    buttons.forEach((button) => {
        button.addEventListener(
            "click",
            () => {

                const page =
                    Number(
                        button.dataset.reviewPage
                    );

                if (!Number.isFinite(page)) {
                    return;
                }

                state.reviewPage =
                    page;

                loadHumanReview();
            }
        );
    });
}



/* ============================================================
 * PREDICTION CARD
 * ============================================================ */

function renderPredictionCard(prediction) {
    const live =
        isLivePrediction(prediction);

    const sourceLabel =
        live ? "LIVE" : "MANUAL";

    const sourceClass =
        live ? "live" : "manual";

    const approval =
        Boolean(prediction.requires_approval)
            ? "REQUIRED"
            : "NOT REQUIRED";

    const timestamp =
        formatTimestamp(
            prediction.timestamp
        );

    return `
        <article class="prediction-card">

            <div class="prediction-card-header">

                <div class="prediction-source">
                    <span class="source-badge ${sourceClass}">
                        ${sourceLabel}
                    </span>

                    <span class="prediction-time">
                        ${escapeHtml(timestamp)}
                    </span>
                </div>

                <span class="risk-badge">
                    ${escapeHtml(
                        prediction.risk || "UNKNOWN"
                    )}
                </span>

            </div>

            <div class="prediction-ticket">
                ${escapeHtml(
                    prediction.ticket || ""
                )}
            </div>

            <div class="prediction-card-grid">

                <div>
                    <span>Intent</span>
                    <strong>
                        ${escapeHtml(
                            prediction.predicted_intent ||
                            "—"
                        )}
                    </strong>
                </div>

                <div>
                    <span>Action</span>
                    <strong>
                        ${escapeHtml(
                            prediction.action_name ||
                            "—"
                        )}
                    </strong>
                </div>

                <div>
                    <span>Approval</span>
                    <strong>
                        ${approval}
                    </strong>
                </div>

                <div>
                    <span>Model</span>
                    <strong>
                        ${escapeHtml(
                            prediction.model_status ||
                            "—"
                        )}
                    </strong>
                </div>

            </div>

            <div class="prediction-identifiers">

                <span>
                    Event:
                    <code>
                        ${escapeHtml(
                            prediction.event_id || "—"
                        )}
                    </code>
                </span>

                ${
                    live
                        ? `
                        <span>
                            Source:
                            <code>
                                ${escapeHtml(
                                    prediction.source_event_id ||
                                    "—"
                                )}
                            </code>
                        </span>
                        `
                        : ""
                }

            </div>

        </article>
    `;
}


/* ============================================================
 * LIVE OPERATIONS
 * ============================================================ */

async function loadLiveOperations() {
    state.livePage = 1;

    animatePipelineActivity();

    await loadPredictionHistory();
    updateLiveOperations();
}

/* ============================================================
 * PIPELINE ACTIVITY
 * ============================================================ */

function animatePipelineActivity() {
    const pipeline =
        document.querySelector(".pipeline-strip");

    if (!pipeline) {
        return;
    }

    pipeline.classList.remove("pipeline-active");

    /*
     * Force a reflow so repeated live refreshes can
     * restart the animation cleanly.
     */
    void pipeline.offsetWidth;

    pipeline.classList.add("pipeline-active");

    window.setTimeout(() => {
        pipeline.classList.remove("pipeline-active");
    }, 2400);
}


function updateLiveOperations() {
    const livePredictions =
        state.predictions.filter(
            isLivePrediction
        );

    /* --------------------------------------------------------
     * KPI values are calculated from the COMPLETE live set.
     * Pagination affects only the visible cards.
     * -------------------------------------------------------- */

    const count =
        document.getElementById("live-count");

    const lowRisk =
        document.getElementById("live-low-risk");

    const review =
        document.getElementById("live-review-count");

    const model =
        document.getElementById("live-model-status");

    if (count) {
        count.textContent =
            livePredictions.length;
    }

    if (lowRisk) {
        lowRisk.textContent =
            livePredictions.filter(
                (prediction) =>
                    String(
                        prediction.risk || ""
                    ).toUpperCase() === "LOW"
            ).length;
    }

    if (review) {
        review.textContent =
            livePredictions.filter(
                (prediction) =>
                    Boolean(
                        prediction.requires_approval
                    )
            ).length;
    }

    if (model) {
        const latest =
            livePredictions[0];

        model.textContent =
            latest?.model_status ||
            "—";
    }

    const container =
        document.getElementById(
            "live-predictions"
        );

    if (!container) {
        return;
    }

    /* --------------------------------------------------------
     * Empty state
     * -------------------------------------------------------- */

    if (!livePredictions.length) {
        state.livePage = 1;

        container.innerHTML = `
            <div class="empty-state">
                <strong>No live predictions available</strong>
                <span>
                    Streaming predictions will appear here when available.
                </span>
            </div>
        `;

        return;
    }

    /* --------------------------------------------------------
     * Pagination
     * -------------------------------------------------------- */

    const pageSize =
        state.livePageSize;

    const totalPages =
        Math.max(
            1,
            Math.ceil(
                livePredictions.length /
                pageSize
            )
        );

    /*
     * Protect against the current page becoming invalid
     * when the live prediction set changes.
     */
    state.livePage =
        Math.min(
            Math.max(
                state.livePage,
                1
            ),
            totalPages
        );

    const startIndex =
        (state.livePage - 1) *
        pageSize;

    const endIndex =
        Math.min(
            startIndex + pageSize,
            livePredictions.length
        );

    const pagePredictions =
        livePredictions.slice(
            startIndex,
            endIndex
        );

    /* --------------------------------------------------------
     * Render current page
     * -------------------------------------------------------- */

    container.innerHTML =
        pagePredictions
            .map(renderPredictionCard)
            .join("");

    /* --------------------------------------------------------
     * Pagination controls
     * -------------------------------------------------------- */

    container.insertAdjacentHTML(
        "beforeend",
        renderLivePagination(
            livePredictions.length,
            totalPages,
            startIndex,
            endIndex
        )
    );

    initializeLivePagination();
}


/* ============================================================
 * LIVE OPERATIONS PAGINATION
 * ============================================================ */

function renderLivePagination(
    totalRecords,
    totalPages,
    startIndex,
    endIndex
) {
    if (totalRecords === 0) {
        return "";
    }

    const currentPage =
        state.livePage;

    const pageButtons =
        Array.from(
            { length: totalPages },
            (_, index) => {
                const page =
                    index + 1;

                return `
                    <button
                        type="button"
                        class="pagination-button ${
                            page === currentPage
                                ? "active"
                                : ""
                        }"
                        data-live-page="${page}"
                    >
                        ${page}
                    </button>
                `;
            }
        )
        .join("");

    return `
        <div class="history-pagination live-pagination">

            <span class="pagination-summary">
                ${startIndex + 1}–${endIndex}
                of
                ${totalRecords}
            </span>

            <div class="pagination-controls">

                <button
                    type="button"
                    class="pagination-button"
                    data-live-page="${currentPage - 1}"
                    ${currentPage === 1 ? "disabled" : ""}
                >
                    Previous
                </button>

                ${pageButtons}

                <button
                    type="button"
                    class="pagination-button"
                    data-live-page="${currentPage + 1}"
                    ${currentPage === totalPages ? "disabled" : ""}
                >
                    Next
                </button>

            </div>

        </div>
    `;
}


function initializeLivePagination() {
    const buttons =
        document.querySelectorAll(
            "[data-live-page]"
        );

    buttons.forEach((button) => {
        button.addEventListener(
            "click",
            () => {

                const page =
                    Number(
                        button.dataset.livePage
                    );

                if (!Number.isFinite(page)) {
                    return;
                }

                state.livePage =
                    page;

                updateLiveOperations();
            }
        );
    });
}



/* ============================================================
 * HUMAN REVIEW
 * ============================================================ */

function loadHumanReview() {
    const container =
        document.getElementById(
            "review-predictions"
        );

    const total =
        document.getElementById(
            "review-total"
        );

    if (!container) {
        return;
    }

    const reviewItems =
        state.predictions.filter(
            (prediction) =>
                Boolean(
                    prediction.requires_approval
                )
        );

    if (total) {
        total.textContent =
            reviewItems.length
                ? `${reviewItems.length} ticket(s) require review`
                : "No tickets require review";
    }

    /* --------------------------------------------------------
     * Empty state
     * -------------------------------------------------------- */

    if (!reviewItems.length) {
        state.reviewPage = 1;

        container.innerHTML = `
            <div class="empty-state">
                <strong>No tickets currently require review</strong>
                <span>
                    No prediction currently has requires_approval enabled.
                </span>
            </div>
        `;

        return;
    }

    /* --------------------------------------------------------
     * Pagination
     * -------------------------------------------------------- */

    const pageSize =
        state.reviewPageSize;

    const totalPages =
        Math.max(
            1,
            Math.ceil(
                reviewItems.length / pageSize
            )
        );

    /*
     * Protect against the current page becoming invalid
     * after the review queue changes.
     */
    state.reviewPage =
        Math.min(
            Math.max(
                state.reviewPage,
                1
            ),
            totalPages
        );

    const startIndex =
        (state.reviewPage - 1) * pageSize;

    const endIndex =
        Math.min(
            startIndex + pageSize,
            reviewItems.length
        );

    const pageItems =
        reviewItems.slice(
            startIndex,
            endIndex
        );

    /* --------------------------------------------------------
     * Render current review page
     * -------------------------------------------------------- */

    container.innerHTML =
        pageItems
            .map(renderPredictionCard)
            .join("");

    /* --------------------------------------------------------
     * Reuse the existing pagination UI
     * -------------------------------------------------------- */

    container.insertAdjacentHTML(
        "beforeend",
        renderReviewPagination(
            reviewItems.length,
            totalPages,
            startIndex,
            endIndex
        )
    );

    initializeReviewPagination();
}


/* ============================================================
 * FILTERS
 * ============================================================ */

function initializeHistoryFilters() {
    const buttons =
        document.querySelectorAll(
            ".filter-button"
        );

    buttons.forEach((button) => {
        button.addEventListener(
            "click",
            () => {

                buttons.forEach(
                    (item) =>
                        item.classList.toggle(
                            "active",
                            item === button
                        )
                );

                state.activeHistoryFilter =
                    button.dataset.historyFilter ||
                    "all";

                state.historyPage = 1;

                renderHistory();
            }
        );
    });
}


/* ============================================================
 * UTILITIES
 * ============================================================ */

function formatTimestamp(value) {
    if (!value) {
        return "Unknown time";
    }

    try {
        return new Date(value).toLocaleString();
    } catch {
        return value;
    }
}


function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ============================================================
 * EVENT WIRING
 * ============================================================ */

function initializeEventHandlers() {

    const predictButton =
        document.getElementById(
            "predict-button"
        );

    if (predictButton) {
        predictButton.addEventListener(
            "click",
            predictTicket
        );
    }


    const actionButton =
        document.getElementById(
            "action-button"
        );

    if (actionButton) {
        actionButton.addEventListener(
            "click",
            simulateAction
        );
    }


    const feedbackButton =
        document.getElementById(
            "feedback-button"
        );

    if (feedbackButton) {
        feedbackButton.addEventListener(
            "click",
            submitFeedback
        );
    }


    const historyButton =
        document.getElementById(
            "history-button"
        );

    if (historyButton) {
        historyButton.addEventListener(
            "click",
            loadPredictionHistory
        );
    }


    const liveButton =
        document.getElementById(
            "live-refresh-button"
        );

    if (liveButton) {
        liveButton.addEventListener(
            "click",
            loadLiveOperations
        );
    }
}


/* ============================================================
 * APPLICATION STARTUP
 * ============================================================ */

async function initializeApplication() {

    initializeNavigation();
    initializeEventHandlers();
    initializeHistoryFilters();

    await checkHealth();
    await loadIntents();
    await loadPredictionHistory();

    updateLiveOperations();
    loadHumanReview();
    updateSystemStatus();
}


/* ============================================================
 * START
 * ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeApplication
);
