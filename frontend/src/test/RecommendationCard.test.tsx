import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RecommendationCard } from "../components/RecommendationCard";
import { renderWithProviders } from "./renderWithProviders";
import type { Recommendation } from "../api/types";

const rec: Recommendation = {
  id: 1,
  greenhouse_id: 1,
  zone_id: 1,
  sensor_id: 1,
  recommendation_type: "irrigation_needed",
  priority: "high",
  status: "open",
  message: "Soil moisture in Zone A is 40%, below the target minimum of 55%.",
  reason: "Zone target for soil moisture is 55%–75%.",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  resolved_at: null,
};

describe("RecommendationCard", () => {
  it("renders message and reason", () => {
    renderWithProviders(<RecommendationCard recommendation={rec} />);
    expect(screen.getByText(rec.message)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(rec.reason))).toBeInTheDocument();
  });

  it("calls onComplete when open", async () => {
    const onComplete = vi.fn();
    renderWithProviders(
      <RecommendationCard recommendation={rec} onComplete={onComplete} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /completed/i }));
    expect(onComplete).toHaveBeenCalledWith(1);
  });

  it("hides actions when not open", () => {
    renderWithProviders(
      <RecommendationCard recommendation={{ ...rec, status: "completed" }} />,
    );
    expect(screen.queryByRole("button", { name: /completed/i })).toBeNull();
  });
});
