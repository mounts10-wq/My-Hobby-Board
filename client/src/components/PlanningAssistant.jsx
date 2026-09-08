import { useMemo, useState } from "react";
import { apiRequest } from "../services/api";

function buildSuggestions(board) {
  const combinedText = [
    board?.title || "",
    board?.description || "",
    board?.materials || "",
    board?.notes || "",
  ]
    .join(" ")
    .toLowerCase();

  const suggestions = [];

  const activity = combinedText.includes("build") || combinedText.includes("make") || combinedText.includes("restore")
    ? "build"
    : combinedText.includes("learn") || combinedText.includes("study") || combinedText.includes("practice")
      ? "learn"
      : "plan";

  if (activity === "build") {
    suggestions.push(`Break the project into 3 early milestones so ${board?.title || "this board"} feels manageable.`);
  } else if (activity === "learn") {
    suggestions.push(`Create a mini study plan around ${board?.title || "this goal"} so progress stays steady.`);
  } else {
    suggestions.push(`Start with a simple first milestone for ${board?.title || "this project"}.`);
  }

  if (board?.materials) {
    const materialsList = board.materials
      .split(/,|\n/)
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 3)
      .join(", ");

    suggestions.push(`Use your materials as a prep checklist: ${materialsList || "your current supplies"}.`);
  } else {
    suggestions.push("Add a few materials so the assistant can suggest a better prep plan.");
  }

  if (board?.notes) {
    suggestions.push(`Turn one note into a concrete next task: ${board.notes}`);
  } else {
    suggestions.push("Write one short note about your next step so the assistant can help more specifically.");
  }

  if (combinedText.includes("week") || combinedText.includes("month") || combinedText.includes("timeline") || combinedText.includes("schedule")) {
    suggestions.push("Set a checkpoint date so you can review progress before the next milestone.");
  } else {
    suggestions.push("Add a target date to keep momentum and make the plan feel real.");
  }

  return suggestions;
}

function PlanningAssistant({ board }) {
  const [generatedPlan, setGeneratedPlan] = useState({
    boardSignature: "",
    suggestions: [],
    source: "fallback",
  });
  const [isGenerating, setIsGenerating] = useState(false);

  const boardSignature = useMemo(
    () =>
      JSON.stringify({
        id: board?.id || "",
        title: board?.title || "",
        description: board?.description || "",
        materials: board?.materials || "",
        notes: board?.notes || "",
      }),
    [board?.id, board?.title, board?.description, board?.materials, board?.notes]
  );

  const fallbackSuggestions = useMemo(() => buildSuggestions(board), [board]);
  const showingGenerated = generatedPlan.boardSignature === boardSignature;
  const suggestions = showingGenerated ? generatedPlan.suggestions : fallbackSuggestions;

  async function handleGenerate() {
    setIsGenerating(true);

    try {
      const data = await apiRequest("/assistant/plan", {
        method: "POST",
        body: JSON.stringify({
          title: board?.title || "",
          description: board?.description || "",
          materials: board?.materials || "",
          notes: board?.notes || "",
        }),
      });

      setGeneratedPlan({
        boardSignature,
        suggestions: data.suggestions || [],
        source: data.source || "fallback",
      });
    } catch {
      setGeneratedPlan({
        boardSignature,
        suggestions: fallbackSuggestions,
        source: "fallback",
      });
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <section className="planning-assistant">
      <div className="assistant-header">
        <div>
          <h2>Planning Assistant</h2>
          <p>Get smart milestone and preparation suggestions tailored to your board.</p>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={handleGenerate}
          disabled={isGenerating}
        >
          {isGenerating ? "Thinking..." : "Generate ideas"}
        </button>
      </div>

      <ul className="assistant-list">
        {suggestions.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export default PlanningAssistant;
