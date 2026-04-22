const assistantForm = document.getElementById("assistant-form");

if (assistantForm) {
  const assistantInput = document.getElementById("assistant-input");
  const modeSelect = document.getElementById("mode-select");
  const styleSelect = document.getElementById("style-select");
  const responseCard = document.getElementById("response-card");
  const responseStatus = document.getElementById("response-status");
  const responseContext = document.getElementById("response-context");
  const nextQuestions = document.getElementById("next-questions");
  const copyResponseButton = document.getElementById("copy-response-btn");
  const explainNewButton = document.getElementById("explain-new-btn");
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
  let lastResponseText = responseCard.textContent.trim();
  let activeRequestController = null;

  function updateTopicSelection(topic) {
    currentTopic = topic;
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
    const example = data.example
      ? `<div class="response-example"><strong>Example:</strong> ${escapeHtml(data.example)}</div>`
      : "";

    responseCard.innerHTML = `
      <h3>${escapeHtml(data.heading || heading)}</h3>
      <div class="response-body">
        <p>${escapeHtml(data.answer)}</p>
        ${bulletMarkup ? `<ul class="response-points">${bulletMarkup}</ul>` : ""}
        ${clarification}
        ${example}
      </div>
    `;

    responseStatus.textContent = data.used_fallback ? "Fallback guidance used" : "Assistant response ready";
    responseContext.textContent = `Current focus: ${heading}`;
    lastResponseText = [
      data.heading || heading,
      data.answer || "",
      ...(data.bullets || []),
      data.clarification || "",
      data.example ? `Example: ${data.example}` : "",
    ]
      .filter(Boolean)
      .join("\n");
    updateSuggestions(data.suggestions || []);
    updateProgress(data.progress || {});
    updateVisitedTopics(data.visited_topics || [], data.suggested_next_topic || "");
    updateTopicSelection(data.topic || currentTopic);
    responseCard.scrollIntoView({ behavior: "smooth", block: "start" });
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

  function updateProgress(progress) {
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

  function setLoadingState(questionText, text = "Thinking through the election process...") {
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
    responseCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function submitQuestion(question, topic = currentTopic, explainLikeNew = false, interactionSource = "manual") {
    if (!question.trim()) {
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

    if (activeRequestController) {
      activeRequestController.abort();
    }

    const requestController = new AbortController();
    activeRequestController = requestController;

    setLoadingState(question);

    try {
      const response = await fetch("/api/assistant", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        signal: requestController.signal,
        body: JSON.stringify({
          question,
          topic,
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

  assistantForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitQuestion(assistantInput.value, currentTopic, false, "manual");
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chip.classList.add("active");
      updateTopicSelection(chip.dataset.topic);
      assistantInput.value = chip.dataset.question || chip.textContent.trim();
      submitQuestion(assistantInput.value, chip.dataset.topic, false, "chip");
    });
  });

  nextQuestions.addEventListener("click", (event) => {
    const button = event.target.closest(".suggestion-chip");
    if (!button || button.disabled) {
      return;
    }

    const question = button.textContent.trim();
    assistantInput.value = question;
    submitQuestion(question, currentTopic, false, "suggestion");
  });

  explainNewButton.addEventListener("click", () => {
    const text = assistantInput.value.trim() || "Explain the election process simply";
    assistantInput.value = text;
    submitQuestion(text, currentTopic, true, "explain_new");
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
        updateProgress(data.progress);
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
