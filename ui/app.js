const ticketInput = document.getElementById("ticket");
const predictButton = document.getElementById("predict-button");

const resultCard = document.getElementById("result-card");
const errorMessage = document.getElementById("error-message");
const healthStatus = document.getElementById("health-status");

const actionButton = document.getElementById("action-button");
const actionResult = document.getElementById("action-result");
const actualIntent = document.getElementById("actual-intent");
const feedbackButton = document.getElementById("feedback-button");
const feedbackResult = document.getElementById("feedback-result");

let currentEventId = null;

let currentActionId = null;


async function checkHealth() {
    try {
        const response = await fetch("/health");

        if (!response.ok) {
            throw new Error("Runner is unhealthy");
        }

        healthStatus.textContent = "Runner healthy";
        healthStatus.className = "status healthy";
    } catch (error) {
        healthStatus.textContent = "Runner unavailable";
        healthStatus.className = "status unhealthy";
    }
}


async function simulateAction() {
    if (!currentActionId) {
        return;
    }

    actionButton.disabled = true;
    actionButton.textContent = "Processing...";
    actionResult.classList.add("hidden");
    actionResult.classList.remove("success", "warning");

    try {
        const response = await fetch("/action/simulate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                action_id: currentActionId
            })
        });

        const body = await response.json();

        if (!response.ok) {
            throw new Error(
                body.detail || "Action simulation failed."
            );
        }

        actionResult.textContent = body.message;

        if (body.status === "simulated") {
            actionResult.classList.add("success");
        } else if (body.status === "approval_required") {
            actionResult.classList.add("warning");
        }

        actionResult.classList.remove("hidden");

    } catch (error) {
        actionResult.textContent = error.message;
        actionResult.classList.add("warning");
        actionResult.classList.remove("hidden");

    } finally {
        actionButton.disabled = false;

        if (actionButton.dataset.approval === "true") {
            actionButton.textContent = "Request Approval";
        } else {
            actionButton.textContent = "Simulate Action";
        }
    }
}


async function loadIntents() {
    try {
        const response = await fetch("/intents");

        if (!response.ok) {
            throw new Error("Unable to load support intents.");
        }

        const body = await response.json();

        body.intents.forEach((intent) => {
            const option = document.createElement("option");

            option.value = intent;
            option.textContent = intent;

            actualIntent.appendChild(option);
        });
    } catch (error) {
        feedbackResult.textContent = error.message;
        feedbackResult.classList.add("warning");
        feedbackResult.classList.remove("hidden");
    }
}


async function submitFeedback() {
    if (!currentEventId || !actualIntent.value) {
        return;
    }

    feedbackButton.disabled = true;
    feedbackButton.textContent = "Recording...";
    feedbackResult.classList.add("hidden");
    feedbackResult.classList.remove("success", "warning");

    try {
        const response = await fetch("/feedback", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                event_id: currentEventId,
                actual_intent: actualIntent.value
            })
        });

        const body = await response.json();

        if (!response.ok) {
            throw new Error(
                body.detail || "Feedback submission failed."
            );
        }

        feedbackResult.textContent =
            body.prediction_correct
                ? "✓ Prediction confirmed correct."
                : "✗ Prediction was incorrect.";

        feedbackResult.classList.add("success");
        feedbackResult.classList.remove("warning");
        feedbackResult.classList.remove("hidden");

    } catch (error) {
        feedbackResult.textContent = error.message;
        feedbackResult.classList.add("warning");
        feedbackResult.classList.remove("success");
        feedbackResult.classList.remove("hidden");

    } finally {
        feedbackButton.disabled = false;
        feedbackButton.textContent = "Submit Feedback";
    }
}


async function predictTicket() {
    const ticket = ticketInput.value.trim();

    resultCard.classList.add("hidden");
    errorMessage.classList.add("hidden");
    actionResult.classList.add("hidden");

    if (!ticket) {
        errorMessage.textContent =
            "Please enter a support ticket.";

        errorMessage.classList.remove("hidden");
        return;
    }

    predictButton.disabled = true;
    predictButton.textContent = "Predicting...";

    const start = performance.now();

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ticket: ticket
            })
        });

        const body = await response.json();

        if (!response.ok) {
            throw new Error(
                body.detail || "Prediction failed."
            );
        }

        const latency =
            (performance.now() - start).toFixed(1);

        /*
         * Prediction
         */

        document.getElementById("prediction").textContent =
            body.prediction;

        currentEventId = body.event_id;
        actualIntent.value = "";
        feedbackButton.disabled = false;
        feedbackResult.classList.add("hidden");
        feedbackResult.classList.remove("success", "warning");

        /*
         * Decision
         */

        document.getElementById("decision-intent").textContent =
            body.decision.intent;

        document.getElementById("action-name").textContent =
            body.decision.action_name;

        document.getElementById("action-id").textContent =
            body.decision.action_id;

        document.getElementById("risk").textContent =
            body.decision.risk;

        document.getElementById("approval-required").textContent =
            body.decision.requires_approval ? "YES" : "NO";

        document.getElementById("simulation-message").textContent =
            body.decision.simulation_message;

        /*
         * Action control
         */

        currentActionId = body.decision.action_id;

        actionButton.dataset.approval =
            body.decision.requires_approval ? "true" : "false";

        actionButton.textContent =
            body.decision.requires_approval
                ? "Request Approval"
                : "Simulate Action";

        actionButton.classList.remove("hidden");

        /*
         * Model information
         */

        document.getElementById("experiment-name").textContent =
            body.model.experiment_name;

        document.getElementById("run-id").textContent =
            body.model.run_id;

        document.getElementById("model-id").textContent =
            body.model.model_id;

        document.getElementById("model-name").textContent =
            body.model.model_name;

        document.getElementById("model-status").textContent =
            body.model.status;

        /*
         * Latency
         */

        document.getElementById("latency").textContent =
            `${latency} ms`;

        resultCard.classList.remove("hidden");

    } catch (error) {
        errorMessage.textContent = error.message;
        errorMessage.classList.remove("hidden");

    } finally {
        predictButton.disabled = false;
        predictButton.textContent = "Predict Ticket";
    }
}


predictButton.addEventListener(
    "click",
    predictTicket
);

actionButton.addEventListener(
    "click",
    simulateAction
);

feedbackButton.addEventListener(
    "click",
    submitFeedback
);

loadIntents();
checkHealth();


async function loadPredictionHistory() {
    const historyContainer =
        document.getElementById("prediction-history");

    const historyButton =
        document.getElementById("refresh-history-button");

    if (!historyContainer || !historyButton) {
        return;
    }

    historyButton.disabled = true;
    historyButton.textContent = "Loading...";

    try {
        const response = await fetch(
            "/predictions?limit=10"
        );

        const body = await response.json();

        if (!response.ok) {
            throw new Error(
                body.detail || "Failed to load prediction history."
            );
        }

        historyContainer.innerHTML = "";

        if (!body.predictions.length) {
            historyContainer.innerHTML =
                '<p class="history-empty">' +
                'No prediction history available.' +
                '</p>';

            return;
        }

        for (const event of body.predictions) {
            const item = document.createElement("div");

            item.className = "history-item";

            const correctClass =
                event.prediction_correct === null
                    ? "pending"
                    : event.prediction_correct
                        ? "yes"
                        : "no";

            const correctText =
                event.prediction_correct === null
                    ? "Pending"
                    : event.prediction_correct
                        ? "Correct"
                        : "Incorrect";

            item.innerHTML = `
                <div class="history-item-header">
                    <span class="history-intent">
                        ${event.predicted_intent}
                    </span>

                    <span class="history-time">
                        ${event.timestamp}
                    </span>
                </div>

                <div class="history-ticket">
                    ${event.ticket}
                </div>

                <div class="history-details">
                    <strong>Action</strong>
                    <span>${event.action_name}</span>

                    <strong>Risk</strong>
                    <span>${event.risk}</span>

                    <strong>Actual Intent</strong>
                    <span>
                        ${event.actual_intent ?? "Not provided"}
                    </span>

                    <strong>Prediction</strong>
                    <span class="history-correct ${correctClass}">
                        ${correctText}
                    </span>
                </div>
            `;

            historyContainer.appendChild(item);
        }

    } catch (error) {
        historyContainer.innerHTML =
            `<p class="history-empty">
                ${error.message}
            </p>`;

    } finally {
        historyButton.disabled = false;
        historyButton.textContent = "Refresh History";
    }
}


document
    .getElementById("refresh-history-button")
    .addEventListener(
        "click",
        loadPredictionHistory
    );
