import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { SensorChart } from "../components/SensorChart";
import { renderWithProviders } from "./renderWithProviders";

describe("SensorChart", () => {
  it("shows an empty state when there are no readings", () => {
    renderWithProviders(
      <SensorChart readings={[]} color="#000" unit="°C" label="Temperature" />,
    );
    expect(
      screen.getByRole("status", { name: /temperature chart has no data/i }),
    ).toBeInTheDocument();
  });

  it("has an accessible label when data is present", () => {
    renderWithProviders(
      <SensorChart
        readings={[
          { id: 1, sensor_id: 1, timestamp: "2026-01-01T00:00:00Z", value: 20 },
          { id: 2, sensor_id: 1, timestamp: "2026-01-01T01:00:00Z", value: 21 },
        ]}
        color="#000"
        unit="°C"
        label="Temperature"
      />,
    );
    expect(
      screen.getByRole("img", { name: /temperature time series/i }),
    ).toBeInTheDocument();
  });
});
