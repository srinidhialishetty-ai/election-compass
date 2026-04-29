const assistantForm = document.getElementById("assistant-form");
let currentContext = "overview";

function inferTopicFromQuestion(question) {
    const text = (question || "").toLowerCase();
    if (text.includes("timeline") || text.includes("order") || text.includes("sequence") || text.includes("when")) return "timeline";
    if (text.includes("register") || text.includes("eligible") || text.includes("eligibility")) return "registration";
    if (text.includes("voting day") || text.includes("poll") || text.includes("ballot")) return "voting_day";
    if (text.includes("count") || text.includes("result") || text.includes("after voting") || text.includes("after votes")) return "results";
    if (text.includes("stage") || text.includes("step")) return "stages";
    if (text.includes("question") || text.includes("confused")) return "faq";
    return currentContext || "overview";
}

function typeWriterEffect(element, text, speed = 10) {
    if (!element) return;
    let i = 0;
    element.innerHTML = "";
    function typing() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(typing, speed);
        }
    }
    typing();
}

function updateProgress(step) {
    const map = {
        "overview": 20,
        "stages": 40,
        "timeline": 60,
        "voting": 80,
        "voting_day": 80,
        "results": 100
    };
    const progressFill = document.getElementById("progressFill");
    if (progressFill && map[step]) {
        progressFill.style.width = map[step] + "%";
    }
}

function setContext(context) {
    currentContext = context;
    updateProgress(context);
}

function sendToBackend(input, topic) {
    const resolvedTopic = topic || inferTopicFromQuestion(input);
    if (window.submitAssistantQuestion) {
        window.submitAssistantQuestion(input, resolvedTopic, false, "manual");
        return;
    }

    const params = new URLSearchParams({
        topic: resolvedTopic,
        question: input
    });
    window.location.href = "/assistant?" + params.toString();
}

function askQuestion(question, topic) {
    if (topic) {
        setContext(topic);
    }
    sendToBackend(question, topic);
}

window.setContext = setContext;
window.sendToBackend = sendToBackend;
window.askQuestion = askQuestion;

const timelineTogglePanel = document.querySelector("[data-timeline-toggle-panel]");
if (timelineTogglePanel) {
  const timelineModes = {
    simple: [
      "The election process begins with public information and preparation.",
      "Registration checks help voters confirm requirements before deadlines.",
      "Voters learn practical details before voting day arrives.",
      "Voting day is when ballots are cast through the official process.",
      "Counting and reporting happen after voting closes; final confirmation can take longer."
    ],
    detailed: [
      "Election authorities publish notices, rules, and educational material so voters can understand the process.",
      "Registration checkpoints give voters time to confirm eligibility, identity, address, or other local requirements.",
      "The public information phase helps people review official guidance, options, and voting logistics.",
      "On voting day, voters check in, follow instructions, and submit ballots through approved methods.",
      "After voting ends, ballots are counted, reviewed, reported, and then officially confirmed under the relevant process."
    ],
    phases: [
      "Before voting: preparation and public notice.",
      "Before voting: registration and eligibility checkpoint.",
      "Before voting: official information and practical readiness.",
      "Voting day: ballots are cast.",
      "After voting: counting, reporting, and final confirmation."
    ]
  };

  const modeButtons = timelineTogglePanel.querySelectorAll("[data-timeline-mode]");
  const copyTargets = document.querySelectorAll("[data-timeline-copy]");

  function setTimelineMode(mode) {
    const content = timelineModes[mode] || timelineModes.simple;
    copyTargets.forEach((target, index) => {
      target.textContent = content[index] || target.textContent;
    });
    modeButtons.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.timelineMode === mode);
    });
  }

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => setTimelineMode(button.dataset.timelineMode));
  });
}

if (assistantForm) {
  const assistantInput = document.getElementById("assistant-input");
  const modeSelect = document.getElementById("mode-select");
  const styleSelect = document.getElementById("style-select");
  const responseCard = document.getElementById("response-card");
  const responseStatus = document.getElementById("response-status");
  const responseContext = document.getElementById("response-context");
  const nextQuestions = document.getElementById("next-questions");
  const copyResponseButton = document.getElementById("copy-response-btn");
  const chips = document.querySelectorAll(".chip[data-topic]");
  const progressItems = document.querySelectorAll(".progress-item");
  const topicProgressItems = document.querySelectorAll(".topic-progress-item");

  const initialState = window.ELECTION_COMPASS_INITIAL || {};

  const topicLabels = {
    overview: "Election Overview",
    stages: "Process Stages",
    timeline: "Timeline",
    registration: "Registration Basics",
    voting_day: "Voting Day",
    results: "Counting & Results",
    faq: "Common Questions",
  };

  let currentTopic = initialState.topic || "overview";
  let lastQuestion = initialState.question || "";
  let lastResponseText = responseCard.textContent.trim();
  let activeRequestController = null;
  setContext(currentTopic);

  function updateTopicSelection(topic) {
    currentTopic = topic;
    setContext(topic);
    chips.forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.topic === topic);
    });
  }

  function updateResponseUI(data) {
    const heading = topicLabels[data.topic] || "Assistant Response";
    responseStatus.classList.remove("is-loading");
    responseCard.classList.remove("is-loading");
    setSuggestionLoadingState(false);
    const bulletMarkup = (data.bullets || [])
      .map((item) => `<li>${escapeHtml(item)}</li>`)
      .join("");
    const clarification = data.clarification
      ? `<div class="response-note">${escapeHtml(data.clarification)}</div>`
      : "";
    const normalizedExample = normalizeExample(data.example);
    const example = normalizedExample
      ? `<div class="response-example"><strong>Example:</strong> ${escapeHtml(normalizedExample)}</div>`
      : "";

    responseCard.innerHTML = `
      <h3>${escapeHtml(data.heading || heading)}</h3>
      <div class="response-body">
        <p id="response-text"></p>
        ${bulletMarkup ? `<ul class="response-points">${bulletMarkup}</ul>` : ""}
        ${clarification}
        ${example}
      </div>
    `;
    typeWriterEffect(document.getElementById("response-text"), escapeHtml(data.answer || ""));

    responseStatus.textContent = "Assistant response ready";
    responseContext.innerHTML = `Current focus: <span class="current-focus">${escapeHtml(heading)}</span>`;
    lastResponseText = [
      data.heading || heading,
      data.answer || "",
      ...(data.bullets || []),
      data.clarification || "",
      normalizedExample ? `Example: ${normalizedExample}` : "",
    ]
      .filter(Boolean)
      .join("\n");
    updateSuggestions(data.suggestions || []);
    updateLearningProgress(data.progress || {});
    updateVisitedTopics(data.visited_topics || [], data.suggested_next_topic || "");
    updateTopicSelection(data.topic || currentTopic);
    scrollToResponseTop();
  }

  function scrollToResponseTop() {
    requestAnimationFrame(() => {
      responseCard.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  function setSuggestionLoadingState(isLoading) {
    nextQuestions.querySelectorAll(".chip").forEach((button) => {
      button.classList.toggle("is-loading", isLoading);
      button.disabled = isLoading;
    });
  }

  function updateSuggestions(items) {
    nextQuestions.innerHTML = "";

    items.slice(0, 4).forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chip suggestion-chip";
      button.textContent = item;
      nextQuestions.appendChild(button);
    });
  }

  function updateLearningProgress(progress) {
    progressItems.forEach((item) => {
      const key = item.dataset.progressKey;
      const active = Boolean(progress[key]);
      item.classList.remove("is-active", "is-done");
      item.classList.toggle("is-done", active);
      if (active) {
        item.classList.add("is-active");
      }
    });
  }

  function updateVisitedTopics(visitedTopics, nextTopic) {
    topicProgressItems.forEach((item) => {
      const topicKey = item.dataset.topicKey;
      item.classList.toggle("is-visited", visitedTopics.includes(topicKey));
      item.classList.toggle("is-next", nextTopic === topicKey && !visitedTopics.includes(topicKey));
    });
  }

  function setLoadingState(questionText) {
    responseStatus.classList.add("is-loading");
    responseStatus.textContent = "Preparing explanation...";
    responseCard.classList.add("is-loading");
    responseCard.innerHTML = `
      <h3>Working on it</h3>
      <div class="response-body">
        <p>${escapeHtml(questionText)}</p>
        <ul class="response-points">
          <li>Reading the current question</li>
          <li>Checking the last topic in session</li>
          <li>Preparing the next guided step</li>
        </ul>
      </div>
    `;
    setSuggestionLoadingState(true);
  }

  async function submitQuestion(question, topic = currentTopic, explainLikeNew = false, interactionSource = "manual") {
    const trimmedQuestion = (question || "").trim();
    const resolvedTopic = interactionSource === "chip"
      ? (topic || currentTopic)
      : inferTopicFromQuestion(trimmedQuestion);

    if (!trimmedQuestion) {
      responseStatus.classList.remove("is-loading");
      responseStatus.textContent = "Please enter a question";
      responseCard.classList.remove("is-loading");
      responseCard.innerHTML = `
        <h3>Choose a starting prompt</h3>
        <div class="response-body">
          <p>The assistant can explain the election process, break stages apart, clarify the timeline, and summarize what happens after voting.</p>
          <ul class="response-points">
            <li>What is the election process?</li>
            <li>Show me the election timeline</li>
            <li>Explain voting day</li>
          </ul>
        </div>
      `;
      updateSuggestions([
        "What is the election process?",
        "Show me the election timeline",
        "Explain voting day",
      ]);
      return;
    }

    lastQuestion = trimmedQuestion;
    currentTopic = resolvedTopic;
    setContext(resolvedTopic);

    if (activeRequestController) {
      activeRequestController.abort();
    }

    const requestController = new AbortController();
    activeRequestController = requestController;

    setLoadingState(trimmedQuestion);

    try {
      const response = await fetch("/api/assistant", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        signal: requestController.signal,
        body: JSON.stringify({
          question: trimmedQuestion,
          context: currentContext,
          topic: resolvedTopic,
          mode: modeSelect.value,
          style: styleSelect.value,
          explain_like_new: explainLikeNew,
          interaction_source: interactionSource,
        }),
      });

      const data = await response.json();
      if (activeRequestController !== requestController) {
        return;
      }

      if (!response.ok) {
        updateResponseUI({
          answer: data.answer || "I can still help if you ask a short question about stages, voting day, or results.",
          topic: data.topic || currentTopic,
          suggestions: data.suggestions || [],
          progress: data.progress || {},
          used_fallback: true,
        });
        return;
      }

      responseStatus.classList.remove("is-loading");
      responseCard.classList.remove("is-loading");
      setSuggestionLoadingState(false);
      updateResponseUI(data);
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }
      responseStatus.classList.remove("is-loading");
      responseCard.classList.remove("is-loading");
      setSuggestionLoadingState(false);
      updateResponseUI({
        heading: topicLabels[topic] || "Assistant Response",
        answer:
          "The live assistant is temporarily unavailable, so here is a reliable fallback: elections generally move through preparation, registration, voting, counting, and official confirmation. You can ask about any one stage next.",
        bullets: [
          "Preparation establishes the process.",
          "Voting day is only one part of the sequence.",
          "Counting and reporting follow after ballots are cast.",
        ],
        clarification: "You can continue by choosing one of the next-step prompts below.",
        example: null,
        topic,
        suggestions: [
          "Explain the election overview",
          "Show me the timeline",
          "What happens on voting day?",
          "Give me a quick recap",
        ],
        progress: {},
        used_fallback: true,
      });
    } finally {
      if (activeRequestController === requestController) {
        activeRequestController = null;
      }
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function normalizeExample(exampleText) {
    return (exampleText || "").replace(/^\s*example(?:\s+sequence)?\s*:\s*/i, "").trim();
  }

  function regenerateLastQuestion(interactionSource = "manual") {
    const question = lastQuestion || assistantInput.value.trim();
    if (!question) {
      return;
    }
    assistantInput.value = question;
    submitQuestion(question, currentTopic, false, interactionSource);
  }

  function explainSimple() {
    const baseQuestion = assistantInput.value.trim() || `Explain ${topicLabels[currentTopic] || "the election process"} like I'm new`;
    assistantInput.value = baseQuestion;
    submitQuestion(baseQuestion, currentTopic, true, "explain_new");
  }

  function askAssistantQuestion(question) {
    assistantInput.value = question;
    submitQuestion(question, currentTopic, false, "suggestion");
  }

  window.explainSimple = explainSimple;
  window.submitAssistantQuestion = submitQuestion;
  window.askQuestion = askAssistantQuestion;

  modeSelect.addEventListener("change", () => {
    regenerateLastQuestion("manual");
  });

  styleSelect.addEventListener("change", () => {
    regenerateLastQuestion("manual");
  });

  assistantForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitQuestion(assistantInput.value, currentTopic, false, "manual");
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      updateTopicSelection(chip.dataset.topic);
      const question = lastQuestion || assistantInput.value.trim() || chip.dataset.question || chip.textContent.trim();
      assistantInput.value = question;
      submitQuestion(question, chip.dataset.topic, false, "chip");
    });
  });

  topicProgressItems.forEach((item) => {
    item.setAttribute("role", "button");
    item.setAttribute("tabindex", "0");
    item.addEventListener("click", () => {
      const topic = item.dataset.topicKey || "overview";
      const question = `Explain the ${topicLabels[topic] || topic} stage`;
      assistantInput.value = question;
      updateTopicSelection(topic);
      submitQuestion(question, topic, false, "chip");
    });
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        item.click();
      }
    });
  });

  nextQuestions.addEventListener("click", (event) => {
    const button = event.target.closest(".suggestion-chip");
    if (!button || button.disabled) {
      return;
    }

    askAssistantQuestion(button.textContent.trim());
  });

  copyResponseButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(lastResponseText);
      responseStatus.textContent = "Response copied";
    } catch (error) {
      responseStatus.textContent = "Copy failed";
    }
  });

  fetch("/api/state")
    .then((response) => response.json())
    .then((data) => {
      if (data.mode) {
        modeSelect.value = data.mode;
      }
      if (data.style) {
        styleSelect.value = data.style;
      }
      if (data.current_topic) {
        updateTopicSelection(initialState.topic || data.current_topic);
      }
      if (data.progress) {
        updateLearningProgress(data.progress);
      }
      if (data.visited_topics) {
        updateVisitedTopics(data.visited_topics, "");
      }
      if (initialState.question) {
        assistantInput.value = initialState.question;
        submitQuestion(initialState.question, initialState.topic || data.current_topic || "overview", false, "manual");
      }
    })
    .catch(() => {
      updateTopicSelection(initialState.topic || "overview");
      if (initialState.question) {
        assistantInput.value = initialState.question;
      }
    });
}
