import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ReadingOut } from "../api/types";
import { formatNumber } from "../utils/format";

export interface SensorChartProps {
  readings: ReadingOut[];
  color: string;
  unit: string;
  label: string;
  height?: number;
}

function formatTickTime(ts: number, spanMs: number): string {
  const d = new Date(ts);
  // Short span (< 6h): show HH:MM
  // Long span (>= 6h): show "Mon DD HH:MM"
  if (spanMs < 6 * 60 * 60 * 1000) {
    const hh = d.getHours().toString().padStart(2, "0");
    const mm = d.getMinutes().toString().padStart(2, "0");
    return `${hh}:${mm}`;
  }
  const month = d.toLocaleString(undefined, { month: "short" });
  const day = d.getDate().toString().padStart(2, "0");
  const hh = d.getHours().toString().padStart(2, "0");
  const mm = d.getMinutes().toString().padStart(2, "0");
  return `${month} ${day} ${hh}:${mm}`;
}

export function SensorChart({
  readings,
  color,
  unit,
  label,
  height = 320,
}: SensorChartProps) {
  const { data, xTicks, spanMs } = useMemo(() => {
    const points = [...readings]
      .sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      )
      .map((r) => ({
        t: new Date(r.timestamp).getTime(),
        v: r.value,
      }));

    if (points.length === 0) {
      return { data: points, xTicks: [] as number[], spanMs: 0 };
    }

    const minT = points[0].t;
    const maxT = points[points.length - 1].t;
    const span = Math.max(0, maxT - minT);

    // Pick 4–7 evenly spaced ticks. Never more than 7 so labels cannot overlap.
    let tickCount: number;
    if (span <= 0) tickCount = 1;
    else if (span < 5 * 60 * 1000) tickCount = 3;
    // < 5 min: 3 ticks
    else if (span < 60 * 60 * 1000) tickCount = 5;
    // < 1 h: 5 ticks
    else if (span < 24 * 60 * 60 * 1000) tickCount = 6;
    // < 1 d: 6 ticks
    else tickCount = 7; // multi-day: 7 ticks

    const ticks: number[] =
      tickCount === 1
        ? [minT]
        : Array.from(
            { length: tickCount },
            (_, i) => minT + (span * i) / (tickCount - 1),
          );

    return { data: points, xTicks: ticks, spanMs: span };
  }, [readings]);

  if (data.length === 0) {
    return (
      <div
        role="status"
        aria-label={`${label} chart has no data`}
        style={{
          height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#666",
          border: "1px dashed #bbb",
          borderRadius: 8,
        }}
      >
        No readings in this window
      </div>
    );
  }

  return (
    <div
      role="img"
      aria-label={`${label} time series`}
      style={{ width: "100%", height }}
    >
      <ResponsiveContainer>
        <LineChart
          data={data}
          margin={{ top: 12, right: 32, left: 12, bottom: 24 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />

          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            ticks={xTicks}
            tickFormatter={(v) => formatTickTime(v, spanMs)}
            tick={{ fontSize: 12 }}
            tickMargin={8}
            height={40}
            padding={{ left: 12, right: 12 }}
            interval={0}
          />

          <YAxis
            tickFormatter={(v) => formatNumber(v, 0)}
            width={56}
            allowDecimals={false}
            domain={["auto", "auto"]}
            tick={{ fontSize: 12 }}
            tickMargin={6}
          />

          <Tooltip
            formatter={(value: number) => [
              `${formatNumber(value)} ${unit}`,
              label,
            ]}
            labelFormatter={(v: number) => new Date(v).toLocaleString()}
          />

          <Line
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
