import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { MetricCard } from "../components/MetricCard";
import { renderWithProviders } from "./renderWithProviders";

describe("MetricCard", () => {
  it("renders label, value, and unit", () => {
    renderWithProviders(
      <MetricCard label="Avg temperature" value="22.4" unit="°C" />,
    );
    expect(screen.getByText("Avg temperature")).toBeInTheDocument();
    expect(screen.getByText("22.4")).toBeInTheDocument();
    expect(screen.getByText("°C")).toBeInTheDocument();
  });

  it("shows a hint when provided", () => {
    renderWithProviders(
      <MetricCard label="Sensors" value={42} hint="across 3 greenhouses" />,
    );
    expect(screen.getByText("across 3 greenhouses")).toBeInTheDocument();
  });
});
