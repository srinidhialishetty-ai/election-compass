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
    responseCard.innerHTML = `
      <h3>${heading}</h3>
      <p>${escapeHtml(data.answer)}</p>
    `;

    responseStatus.textContent = data.used_fallback ? "Fallback guidance used" : "Assistant response ready";
    responseContext.textContent = `Current focus: ${heading}`;
    lastResponseText = `${heading}\n\n${data.answer}`;
    updateSuggestions(data.suggestions || []);
    updateProgress(data.progress || {});
    updateTopicSelection(data.topic || currentTopic);
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

  function setLoadingState(questionText, text = "Thinking through the election process...") {
    responseStatus.classList.add("is-loading");
    responseStatus.textContent = text;
    responseCard.classList.add("is-loading");
    responseCard.innerHTML = `
      <h3>Working on it</h3>
      <p>${escapeHtml(questionText)}</p>
    `;
    setSuggestionLoadingState(true);
  }

  async function submitQuestion(question, topic = currentTopic, explainLikeNew = false) {
    if (!question.trim()) {
      responseStatus.classList.remove("is-loading");
      responseStatus.textContent = "Please enter a question";
      responseCard.classList.remove("is-loading");
      responseCard.innerHTML = `
        <h3>Helpful prompt</h3>
        <p>Try asking "What is the election process?", "Explain voting day", or "Show me the timeline."</p>
      `;
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
        answer:
          "The live assistant is temporarily unavailable, so here is a reliable fallback: elections generally move through preparation, registration, voting, counting, and official confirmation. You can ask about any one stage next.",
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
    submitQuestion(assistantInput.value, currentTopic, false);
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      updateTopicSelection(chip.dataset.topic);
      assistantInput.value = chip.dataset.question || chip.textContent.trim();
      submitQuestion(assistantInput.value, chip.dataset.topic, false);
    });
  });

  nextQuestions.addEventListener("click", (event) => {
    const button = event.target.closest(".suggestion-chip");
    if (!button || button.disabled) {
      return;
    }

    const question = button.textContent.trim();
    assistantInput.value = question;
    submitQuestion(question, currentTopic, false);
  });

  explainNewButton.addEventListener("click", () => {
    const text = assistantInput.value.trim() || "Explain the election process simply";
    assistantInput.value = text;
    submitQuestion(text, currentTopic, true);
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
      if (initialState.question) {
        assistantInput.value = initialState.question;
        submitQuestion(initialState.question, initialState.topic || data.current_topic || "overview", false);
      }
    })
    .catch(() => {
      updateTopicSelection(initialState.topic || "overview");
      if (initialState.question) {
        assistantInput.value = initialState.question;
      }
    });
}
